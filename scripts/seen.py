#!/usr/bin/env python3
"""Anti-repetición: state/seen.json guarda las notas ya usadas por show."""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / "state" / "seen.json"
KEEP_DAYS = 90


def norm(url):
    p = urlsplit(url.strip())
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunsplit((p.scheme, p.netloc.lower().removeprefix("www."), p.path.rstrip("/"), urlencode(q), ""))


def load():
    return json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}


def unseen(show_id, candidates):
    known = {norm(e["url"]) for e in load().get(show_id, [])}
    return [c for c in candidates if norm(c["url"]) not in known]


def add(show_id, stories, day):
    data = load()
    cutoff = (date.fromisoformat(day) - timedelta(days=KEEP_DAYS)).isoformat()
    kept = [e for e in data.get(show_id, []) if e["date"] >= cutoff]
    kept += [{"url": norm(s["url"]), "title": s["title"], "date": day} for s in stories]
    data[show_id] = kept
    SEEN.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("filter", help="imprime las candidatas que no se usaron todavía")
    f.add_argument("--show", required=True)
    f.add_argument("candidates", help="JSON: lista de {title, url, ...}")
    args = ap.parse_args()
    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    json.dump(unseen(args.show, candidates), sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
