#!/usr/bin/env bash
# Genera un video vertical 1080x1920 con onda de audio a partir de un fragmento.
# Uso: audiograma.sh <audio> <inicio_seg> <fin_seg> <salida.mp4> [portada.png] [carpeta_tarjetas]
# Las tarjetas son los PNG que deja tarjetas.py; salen en los segundos de inicios.txt o, si falta, en partes iguales.
set -euo pipefail
[ $# -ge 4 ] || { echo "Uso: $0 <audio> <inicio_seg> <fin_seg> <salida.mp4> [portada.png] [carpeta_tarjetas]"; exit 1; }
audio="$1"; ini="$2"; fin="$3"; out="$4"; portada="${5:-}"; tarjetas="${6:-}"
dur=$(awk -v a="$ini" -v b="$fin" 'BEGIN{print b-a}')

if [ -n "$portada" ]; then
  # La portada es cuadrada: va entera (sin recortar el logo) sobre un degradado de sus mismos colores; la onda va debajo.
  fondo=(-f lavfi -t "$dur" -i "gradients=s=1080x1920:c0=0x210a4b:c1=0x4f1163:x0=0:y0=180:x1=0:y1=1260:speed=0:r=30" -loop 1 -t "$dur" -i "$portada")
  base="[1:v]scale=1080:1080[c];[0:v][c]overlay=0:180[bg]"
  ia=2
else
  fondo=(-f lavfi -t "$dur" -i "color=c=0x0b0a14:s=1080x1920:r=30")
  base="[0:v]null[bg]"
  ia=1
fi

filtro="${base};[${ia}:a]volume=3,showwaves=s=1000x300:mode=line:scale=sqrt:draw=full:colors=white:rate=30[w];[bg][w]overlay=40:1400:shortest=1[v0]"
extra=()
ultimo=v0
if [ -n "$tarjetas" ]; then
  pngs=("$tarjetas"/*.png)
  n=${#pngs[@]}
  for i in "${!pngs[@]}"; do
    extra+=(-loop 1 -t "$dur" -i "${pngs[$i]}")
    idx=$((ia + 1 + i))
    if [ -f "$tarjetas/inicios.txt" ]; then
      t0=$(sed -n "$((i + 1))p" "$tarjetas/inicios.txt")
      t1=$(sed -n "$((i + 2))p" "$tarjetas/inicios.txt")
      t1=${t1:-$dur}
    else
      t0=$(awk -v d="$dur" -v n="$n" -v i="$i" 'BEGIN{printf "%.2f", d*i/n}')
      t1=$(awk -v d="$dur" -v n="$n" -v i="$i" 'BEGIN{printf "%.2f", d*(i+1)/n}')
    fi
    filtro+=";[${ultimo}][${idx}:v]overlay=(W-w)/2:1150:enable='between(t,${t0},${t1})'[v$((i + 1))]"
    ultimo="v$((i + 1))"
  done
fi

ffmpeg -y -hide_banner -loglevel error "${fondo[@]}" -ss "$ini" -t "$dur" -i "$audio" ${extra[@]+"${extra[@]}"} \
  -filter_complex "$filtro" \
  -map "[${ultimo}]" -map ${ia}:a -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30 -c:a aac -b:a 160k -shortest "$out"
echo "Listo: $out"
