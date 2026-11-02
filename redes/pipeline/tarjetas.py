#!/usr/bin/env python3
"""Dibuja las tarjetas de 'Texto en pantalla' de un texto.md como PNG transparentes.
Uso: tarjetas.py <texto.md> <carpeta_salida>   (necesita Pillow: .venv/bin/pip install pillow)"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Futura.ttc"
ANCHO = 960
TAM = 54
PAD = 36


def tarjetas(texto_md):
    bloque = re.search(r"## Texto en pantalla[^\n]*\n(.*?)(?:\n## |\Z)", texto_md, re.S)
    if not bloque:
        sys.exit("texto.md no tiene la sección 'Texto en pantalla'")
    return [
        (m.group(1), m.group(2).strip())
        for m in re.finditer(r"^\d+\.\s+(?:@([\d.,]+)\s+)?(.+)$", bloque.group(1), re.M)
    ]


def partir(d, texto, fuente, maximo):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if d.textlength(prueba, font=fuente) <= maximo or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def dibujar(texto, ruta):
    fuente = ImageFont.truetype(FONT, TAM, index=2)  # Futura Bold
    medida = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lineas = partir(medida, texto, fuente, ANCHO - 2 * PAD)
    alto = 2 * PAD + int(len(lineas) * TAM * 1.2)
    img = Image.new("RGBA", (ANCHO, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, ANCHO - 1, alto - 1), radius=36, fill=(12, 4, 32, 215))
    y = PAD
    for linea in lineas:
        d.text(((ANCHO - d.textlength(linea, font=fuente)) / 2, y), linea, font=fuente, fill="white")
        y += int(TAM * 1.2)
    img.save(ruta)


def main(md, salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    lista = tarjetas(Path(md).read_text(encoding="utf-8"))
    for i, (_, t) in enumerate(lista, 1):
        if len(t.split()) > 8:
            sys.exit(f"Tarjeta {i} tiene más de 8 palabras: {t}")
        dibujar(t, salida / f"{i:02d}.png")
    inicios = [ini for ini, _ in lista]
    tiempos = salida / "inicios.txt"
    if all(inicios):
        tiempos.write_text("\n".join(i.replace(",", ".") for i in inicios) + "\n")
    else:
        tiempos.unlink(missing_ok=True)  # sin @, audiograma.sh reparte en partes iguales
    print(f"{len(lista)} tarjetas en {salida}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
