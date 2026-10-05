#!/usr/bin/env python3
"""RSS 2.0 con tags iTunes. Un feed por show (ruta en feed_path del yaml)."""
import argparse
import html
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd", "content": "http://purl.org/rss/1.0/modules/content/"}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def q(tag):
    prefix, name = tag.split(":")
    return f"{{{NS[prefix]}}}{name}"


def load_show(show_id):
    return yaml.safe_load((ROOT / "shows" / f"{show_id}.yaml").read_text(encoding="utf-8"))


def feed_file(show):
    return ROOT / show["feed_path"]


def feed_url(show):
    return f"{show['site_url'].rstrip('/')}/{Path(show['feed_path']).name}"


def text(parent, tag, value):
    el = ET.SubElement(parent, tag)
    el.text = value
    return el


def new_channel(show):
    rss = ET.Element("rss", {"version": "2.0"})
    ch = ET.SubElement(rss, "channel")
    text(ch, "title", show["title"])
    text(ch, "link", show["site_url"])
    text(ch, "description", " ".join(show["description"].split()))
    text(ch, "language", show["language"])
    text(ch, q("itunes:author"), show["author"])
    text(ch, q("itunes:explicit"), "true" if show["explicit"] else "false")
    ET.SubElement(ch, q("itunes:category"), {"text": show["category"]})
    cover_url = f"{show['site_url'].rstrip('/')}/{show['cover']}"
    ET.SubElement(ch, q("itunes:image"), {"href": cover_url})
    image = ET.SubElement(ch, "image")
    text(image, "url", cover_url)
    text(image, "title", show["title"])
    text(image, "link", show["site_url"])
    return rss


def show_notes(meta):
    items = "".join(
        f'<li><a href="{html.escape(s["url"])}">{html.escape(s["title"])}</a></li>' for s in meta["stories"]
    )
    out = f"<p>{html.escape(meta['summary'])}</p><p>Fuentes:</p><ul>{items}</ul>"
    if meta.get("discarded"):
        extra = "".join(
            f'<li><a href="{html.escape(s["url"])}">{html.escape(s["title"])}</a></li>' for s in meta["discarded"]
        )
        out += f"<p>Quedaron afuera:</p><ul>{extra}</ul>"
    return out


def add_episode(show, meta):
    """meta: guid, title, summary, pub_date (ISO), mp3_url, bytes, seconds, stories[{title,url}]"""
    path = feed_file(show)
    rss = ET.parse(path).getroot() if path.exists() else new_channel(show)
    ch = rss.find("channel")
    if any(i.findtext("guid") == meta["guid"] for i in ch.findall("item")):
        raise ValueError(f"el episodio {meta['guid']} ya está en el feed")

    item = ET.Element("item")
    text(item, "title", meta["title"])
    text(item, "description", show_notes(meta))
    text(item, q("content:encoded"), show_notes(meta))
    text(item, "guid", meta["guid"]).set("isPermaLink", "false")
    text(item, "pubDate", format_datetime(datetime.fromisoformat(meta["pub_date"])))
    ET.SubElement(item, "enclosure", {"url": meta["mp3_url"], "length": str(meta["bytes"]), "type": "audio/mpeg"})
    m, s = divmod(int(meta["seconds"]), 60)
    text(item, q("itunes:duration"), f"{m // 60:02d}:{m % 60:02d}:{s:02d}")
    text(item, q("itunes:explicit"), "false")

    first = ch.find("item")
    ch.insert(list(ch).index(first) if first is not None else len(ch), item)
    for tag in ("lastBuildDate",):
        for old in ch.findall(tag):
            ch.remove(old)
    last = ET.Element("lastBuildDate")
    last.text = format_datetime(datetime.now(timezone.utc))
    ch.insert(list(ch).index(ch.find("item")), last)
    write(rss, path)


def write(rss, path):
    ET.indent(rss)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(rss).write(path, encoding="utf-8", xml_declaration=True)


def validate(show):
    rss = ET.parse(feed_file(show)).getroot()
    ch = rss.find("channel")
    for tag in ("title", "link", "description", "language"):
        assert ch.findtext(tag), f"falta <{tag}> en el canal"
    for i in ch.findall("item"):
        enc = i.find("enclosure")
        assert enc is not None and enc.get("url", "").startswith("https://"), "item sin enclosure https"
        assert i.findtext("guid") and i.findtext("pubDate"), "item sin guid o pubDate"
    return len(ch.findall("item"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "add", "validate"])
    ap.add_argument("--show", required=True)
    ap.add_argument("--meta", help="JSON del episodio (solo para add)")
    args = ap.parse_args()
    show = load_show(args.show)
    if args.cmd == "init":
        if feed_file(show).exists():
            raise SystemExit("el feed ya existe")
        write(new_channel(show), feed_file(show))
    elif args.cmd == "add":
        add_episode(show, json.loads(Path(args.meta).read_text(encoding="utf-8")))
    print(f"ok: {validate(show)} episodios en {feed_file(show)}")


if __name__ == "__main__":
    main()
