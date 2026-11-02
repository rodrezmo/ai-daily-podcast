#!/usr/bin/env python3
"""Transcribe un episodio con marcas de tiempo por palabra. Uso: transcribir.py <audio.mp3> <salida.json> [modelo]
Necesita faster-whisper, que no está en requirements.txt: ~/.venvs/whisper/bin/pip install faster-whisper"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel


def decodificar(audio):
    # ffmpeg en vez de la lectura interna de faster-whisper (PyAV nuevo rompe con metadata_errors)
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(crudo, dtype=np.float32)


def main(audio, salida, modelo="small"):
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    segmentos, info = m.transcribe(decodificar(audio), language="es", word_timestamps=True, vad_filter=False)
    palabras = [
        {"t0": round(w.start, 2), "t1": round(w.end, 2), "w": w.word.strip()}
        for s in segmentos
        for w in s.words
    ]
    json.dump({"modelo": modelo, "duracion": round(info.duration, 2), "palabras": palabras}, open(salida, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(palabras)} palabras, {info.duration:.0f} s -> {salida}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
