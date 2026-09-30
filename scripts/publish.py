#!/usr/bin/env python3
"""Publica un episodio: valida, sube el MP3 a Releases, actualiza feed y estado, commit y push.

Si algo falla después de crear el release, se deshace todo y sale con código distinto de 0.
No se publica nada a medias. Con --dry-run no toca GitHub ni git.
"""
import argparse
import json
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mutagen.mp3 import MP3

import feed
import seen

ROOT = Path(__file__).resolve().parent.parent


def run(*cmd, check=True):
    return subprocess.run(cmd, cwd=ROOT, check=check, capture_output=True, text=True)


def validate_inputs(show, mp3, meta):
    cfg = show["episode"]
    if "OWNER" in show["repo"] or "OWNER" in show["site_url"]:
        raise RuntimeError("completar repo y site_url en shows/<id>.yaml")
    minutes = MP3(mp3).info.length / 60
    if not cfg["min_minutes"] <= minutes <= cfg["max_minutes"]:
        raise RuntimeError(f"duración {minutes:.1f} min fuera de {cfg['min_minutes']}-{cfg['max_minutes']}")
    if len(meta["stories"]) != cfg["stories"]:
        raise RuntimeError(f"se esperaban {cfg['stories']} notas y hay {len(meta['stories'])}")
    if not all(s.get("url", "").startswith("http") for s in meta["stories"]):
        raise RuntimeError("todas las notas necesitan URL de fuente")


def publish(show_id, day, dry_run):
    show = feed.load_show(show_id)
    ep_dir = ROOT / "episodes" / show_id / day
    mp3 = ep_dir / "episode.mp3"
    meta = json.loads((ep_dir / "meta.json").read_text(encoding="utf-8"))
    validate_inputs(show, mp3, meta)

    tag = f"{show_id}-{day}"
    meta.update(
        guid=tag,
        bytes=mp3.stat().st_size,
        seconds=MP3(mp3).info.length,
        pub_date=datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).isoformat(),
        mp3_url=f"https://github.com/{show['repo']}/releases/download/{tag}/{mp3.name}",
    )
    if dry_run:
        print("dry-run: validaciones ok\n" + json.dumps(meta, ensure_ascii=False, indent=2))
        return

    if run("git", "status", "--porcelain", "docs", "state").stdout.strip():
        raise RuntimeError("hay cambios sin commitear en docs/ o state/")

    release_created = committed = False
    try:
        run("gh", "release", "create", tag, str(mp3), "--repo", show["repo"],
            "--title", meta["title"], "--notes", meta["summary"])
        release_created = True
        feed.add_episode(show, meta)
        feed.validate(show)
        seen.add(show_id, meta["stories"], day)
        (ep_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        run("git", "add", show["feed_path"], "state/seen.json", str(ep_dir / "meta.json"), str(ep_dir / "guion.txt"))
        run("git", "commit", "-m", f"Episodio {tag}: {meta['title']}")
        committed = True
        run("git", "push")
    except Exception:
        if committed:
            run("git", "reset", "--soft", "HEAD~1", check=False)
        run("git", "restore", "--staged", "--worktree", "--source=HEAD", "--", show["feed_path"], "state", check=False)
        if release_created:
            run("gh", "release", "delete", tag, "--repo", show["repo"], "--cleanup-tag", "-y", check=False)
        raise
    print(f"publicado {tag}: {feed.feed_url(show)}")


def notify_failure(show_id, day, error):
    try:
        repo = feed.load_show(show_id)["repo"]
        run("gh", "issue", "create", "--repo", repo, "--title", f"Falló el episodio {show_id} {day}",
            "--body", f"No se publicó nada.\n\n```\n{error[-1500:]}\n```")
    except Exception:  # noqa: BLE001 - el aviso no puede tapar el error original
        print("no pude abrir el issue de aviso", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        publish(args.show, args.date, args.dry_run)
    except Exception:
        err = traceback.format_exc()
        print(err, file=sys.stderr)
        if not args.dry_run:
            notify_failure(args.show, args.date, err)
        sys.exit(1)


if __name__ == "__main__":
    main()
