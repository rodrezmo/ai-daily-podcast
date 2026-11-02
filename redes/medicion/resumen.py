#!/usr/bin/env python3
"""Resume metricas.csv por red y por semana. Uso: python3 resumen.py [metricas.csv]"""
import csv
import sys
from collections import defaultdict
from datetime import date

MUESTRA_MINIMA = 1000  # vistas por semana y red por debajo de las cuales no se concluye


def semana(f):
    y, w, _ = date.fromisoformat(f).isocalendar()
    return f"{y}-S{w:02d}"


def main(ruta):
    filas = list(csv.DictReader(open(ruta, newline="", encoding="utf-8")))
    if not filas:
        print("Sin datos todavía: no hay línea base.")
        return
    acum = defaultdict(lambda: {"vistas": 0, "clics": 0, "likes": 0, "seg": {}})
    for r in filas:
        k = (semana(r["fecha"]), r["red"])
        a = acum[k]
        a["vistas"] += int(r["vistas"] or 0)
        a["clics"] += int(r["clics_al_podcast"] or 0)
        a["likes"] += int(r["me_gusta"] or 0)
        if r["seguidores_totales"]:
            a["seg"][r["fecha"]] = int(r["seguidores_totales"])

    print("| semana | red | vistas | clics al podcast | clics cada 1000 vistas | seguidores (delta) | lectura |")
    print("|---|---|---|---|---|---|---|")
    for (sem, red), a in sorted(acum.items()):
        ctr = f"{1000 * a['clics'] / a['vistas']:.1f}" if a["vistas"] else "-"
        fechas = sorted(a["seg"])
        delta = a["seg"][fechas[-1]] - a["seg"][fechas[0]] if len(fechas) > 1 else "-"
        lectura = "muestra chica" if a["vistas"] < MUESTRA_MINIMA else "ok"
        print(f"| {sem} | {red} | {a['vistas']} | {a['clics']} | {ctr} | {delta} | {lectura} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "metricas.csv")
