#!/usr/bin/env python3
"""Portada del show (3000x3000 JPEG, el tamaño que piden Apple y Spotify). Se corre a mano; el resultado va a docs/."""
import argparse
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import feed

SIZE = 3000
FONT = "/System/Library/Fonts/Supplemental/Futura.ttc"
BARS = 37
BAR_W = 46
MARGIN = 160


def font(size, index=0):
    return ImageFont.truetype(FONT, size, index=index)


def build(show, out):
    img = Image.new("RGB", (SIZE, SIZE))
    d = ImageDraw.Draw(img)
    for y in range(SIZE):
        t = y / SIZE
        d.line([(0, y), (SIZE, y)], fill=(int(30 + 50 * t), int(8 + 10 * t), int(70 + 30 * t)))

    bars = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    b = ImageDraw.Draw(bars)
    gap = (SIZE - 2 * MARGIN - BARS * BAR_W) / (BARS - 1)
    for i in range(BARS):
        u = i / (BARS - 1)
        envelope = math.sin(math.pi * u) ** 1.3
        h = (0.25 + 0.75 * abs(math.sin(u * 9 + 1) * 0.6 + math.sin(u * 23) * 0.4)) * envelope * 1500 + 60
        color = (int(255 - 60 * u), int(94 + 40 * u), int(98 + 130 * u), 255)
        x = MARGIN + i * (BAR_W + gap)
        b.rounded_rectangle([x, 1200 - h / 2, x + BAR_W, 1200 + h / 2], radius=BAR_W // 2, fill=color)
    img = Image.alpha_composite(img.convert("RGBA"), bars.filter(ImageFilter.GaussianBlur(30)))
    img = Image.alpha_composite(img, bars)

    d = ImageDraw.Draw(img)
    title = show["title"].lower()
    size = 100
    while d.textlength(title, font=font(size + 10, 2)) < 2300:
        size += 10
    d.text((SIZE / 2, 2230), title, font=font(size, 2), fill=(255, 255, 255), anchor="mm")
    d.text((SIZE / 2, 2560), "el pulso diario de la inteligencia artificial", font=font(92), fill=(255, 170, 160), anchor="mm")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, quality=92, optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", required=True)
    args = ap.parse_args()
    s = feed.load_show(args.show)
    build(s, feed.ROOT / "docs" / s["cover"])
    print(f"ok: docs/{s['cover']}")
