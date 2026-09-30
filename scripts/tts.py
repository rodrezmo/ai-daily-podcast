#!/usr/bin/env python3
"""Guion (líneas "Nombre: texto") -> episode.mp3. Gemini TTS, con respaldo edge-tts."""
import argparse
import asyncio
import base64
import io
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_RATE = 24000
RETRY_WAITS = (2, 5, 15, 40)


def load_show(show_id):
    return yaml.safe_load((ROOT / "shows" / f"{show_id}.yaml").read_text(encoding="utf-8"))


def parse_script(text, hosts):
    """Devuelve (hablante, texto). Los títulos de sección quedan como ("#", título)."""
    lines = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith("#"):
            lines.append(("#", raw.lstrip("# ").strip()))
            continue
        m = re.match(r"^([^:]{1,30}):\s*(.+)$", raw)
        if not m or m[1] not in hosts:
            raise ValueError(f"línea de guion inválida: {raw[:70]!r}")
        lines.append((m[1], m[2]))
    if not any(sp != "#" for sp, _ in lines):
        raise ValueError("el guion está vacío")
    return lines


def chunk_lines(lines, max_chars):
    chunks, cur, size = [], [], 0
    for speaker, text in lines:
        if cur and size + len(text) > max_chars:
            chunks.append(cur)
            cur, size = [], 0
        cur.append((speaker, text))
        size += len(text)
    if cur:
        chunks.append(cur)
    return chunks


def gemini_chunk(client, tts, chunk):
    """Un request con voces diseñadas (Voice Design): un bloque de texto por turno, anotado con su hablante."""
    hosts = tts["hosts"]
    speech = [{"speaker": n, "voice": h["gemini_voice_id"], "language": "es-AR"} for n, h in hosts.items()]
    content = [
        {"type": "text", "text": t,
         "annotations": [{"type": "speech_metadata", "speaker": s, "start_index": 0, "end_index": len(t.encode())}]}
        for s, t in chunk
    ]
    last = None
    for wait in (0, *RETRY_WAITS):
        time.sleep(wait)
        try:
            r = client.interactions.create(
                model=tts["gemini_model"],
                input=[{"type": "user_input", "content": content}],
                response_format={"type": "audio"},
                generation_config={"speech_config": speech},
            )
            with wave.open(io.BytesIO(base64.b64decode(r.output_audio.data))) as w:
                assert w.getframerate() == SAMPLE_RATE and w.getnchannels() == 1
                pcm = w.readframes(w.getnframes())
            chars = sum(len(t) for _, t in chunk)
            seconds = len(pcm) / (SAMPLE_RATE * 2)
            if seconds < chars / 30:
                raise RuntimeError(f"audio sospechosamente corto: {seconds:.1f}s para {chars} caracteres")
            print(f"  {seconds:.0f}s de audio, {r.usage.total_output_tokens} tokens de salida", file=sys.stderr)
            return pcm
        except Exception as e:  # noqa: BLE001 - reintentamos cualquier falla de red o cupo
            last = e
            print(f"  gemini falló ({type(e).__name__}): {str(e)[:120]}", file=sys.stderr)
    raise RuntimeError(f"Gemini TTS agotó reintentos: {last}")


def synth_gemini(lines, tts):
    from google import genai

    lines = [l for l in lines if l[0] != "#"]
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("falta GEMINI_API_KEY")
    client = genai.Client()
    silence = b"\x00\x00" * int(SAMPLE_RATE * tts["pause_ms"] / 1000)
    out = []
    chunks = chunk_lines(lines, tts["max_chunk_chars"])
    for i, chunk in enumerate(chunks, 1):
        print(f"gemini: trozo {i}/{len(chunks)}", file=sys.stderr)
        out.append(gemini_chunk(client, tts, chunk))
    return silence.join(out)


EDGE_FILTER = "highpass=f=80,acompressor=threshold=-21dB:ratio=3:attack=5:release=90:makeup=2"


def edge_pcm(text, voice, rate, pitch, path):
    import edge_tts
    import numpy as np

    asyncio.run(edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(path)))
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32)


def synth_edge(lines, tts):
    """edge-tts con ritmo humano: variación por frase, pausas según contexto y reacciones solapadas."""
    import numpy as np

    cfg = tts.get("edge", {})
    rng = random.Random(cfg.get("seed", 7))
    base = cfg.get("rate", -3)
    jr, jp = cfg.get("rate_jitter", 4), cfg.get("pitch_jitter", 3)

    def ms(a, b):
        return int(SAMPLE_RATE * rng.uniform(a, b) / 1000)

    track = np.zeros(0, np.float32)
    prev_speaker, prev_text, section_break = None, "", False
    with tempfile.TemporaryDirectory() as tmp:
        for i, (speaker, text) in enumerate(lines):
            if speaker == "#":
                section_break = True
                continue
            voice = tts["hosts"][speaker]["edge_voice"]
            parts = []
            sentences = re.split(r"(?<=[.!?…])\s+", text)
            for j, sent in enumerate(sentences):
                rate = f"{round(base + rng.uniform(-jr, jr)):+d}%"
                pitch = f"{round(rng.uniform(-jp, jp)):+d}Hz"
                parts.append(edge_pcm(sent, voice, rate, pitch, Path(tmp) / f"{i}-{j}.mp3"))
                if j < len(sentences) - 1:
                    parts.append(np.zeros(ms(180, 320), np.float32))
            audio = np.concatenate(parts)

            words = len(text.split())
            reaction = (prev_speaker not in (None, speaker) and words <= 5 and not text.endswith("?")
                        and len(prev_text.split()) > 6)
            if prev_speaker is None:
                gap = 0
            elif section_break:
                gap = ms(800, 1100)
            elif reaction:
                gap = -ms(120, 240)
            elif prev_text.endswith("?"):
                gap = ms(220, 380)
            else:
                gap = ms(250, 450)

            if gap >= 0:
                track = np.concatenate([track, np.zeros(gap, np.float32), audio])
            else:
                ov = min(-gap, len(track), len(audio))
                track[-ov:] += audio[:ov]
                track = np.concatenate([track, audio[ov:]])
            prev_speaker, prev_text, section_break = speaker, text, False
    return np.clip(track, -32768, 32767).astype(np.int16).tobytes()


def master(pcm, out_mp3, intro, pre_filter=""):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "voz.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm)
        norm = (pre_filter + "," if pre_filter else "") + "loudnorm=I=-16:TP=-1.5:LRA=11"
        cmd = ["ffmpeg", "-loglevel", "error", "-y"]
        if intro and Path(intro).exists():
            cmd += ["-i", str(intro), "-i", str(wav), "-filter_complex",
                    f"[0:a]aresample={SAMPLE_RATE},aformat=channel_layouts=mono[a];"
                    f"[1:a]aformat=channel_layouts=mono[b];[a][b]concat=n=2:v=0:a=1,{norm}[o]",
                    "-map", "[o]"]
        else:
            cmd += ["-i", str(wav), "-af", norm]
        cmd += ["-ac", "1", "-codec:a", "libmp3lame", "-b:a", "64k", str(out_mp3)]
        subprocess.run(cmd, check=True)


def tag(mp3, title, show):
    from mutagen.id3 import ID3, TALB, TDRC, TIT2, TPE1
    from mutagen.mp3 import MP3

    tags = ID3()
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TPE1(encoding=3, text=show["author"]))
    tags.add(TALB(encoding=3, text=show["title"]))
    tags.add(TDRC(encoding=3, text=time.strftime("%Y")))
    tags.save(mp3)
    return MP3(mp3).info.length


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", required=True)
    ap.add_argument("--script", required=True, help="guion final verificado (.txt)")
    ap.add_argument("--out", required=True, help="episode.mp3 de salida")
    ap.add_argument("--title", required=True)
    ap.add_argument("--engine", choices=["gemini", "edge"], help="fuerza un motor, sin respaldo")
    args = ap.parse_args()

    show = load_show(args.show)
    tts = show["tts"]
    lines = parse_script(Path(args.script).read_text(encoding="utf-8"), tts["hosts"])
    engine = args.engine or tts["engine"]
    try:
        pcm = synth_gemini(lines, tts) if engine == "gemini" else synth_edge(lines, tts)
    except Exception as e:  # noqa: BLE001
        if args.engine:
            raise
        print(f"Gemini falló, uso edge-tts para TODO el episodio: {e}", file=sys.stderr)
        engine = "edge"
        pcm = synth_edge(lines, tts)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    master(pcm, out, ROOT / "assets" / "intro.mp3", EDGE_FILTER if engine == "edge" else "")
    seconds = tag(out, args.title, show)
    print(json.dumps({"engine": engine, "seconds": round(seconds), "bytes": out.stat().st_size}))


if __name__ == "__main__":
    main()
