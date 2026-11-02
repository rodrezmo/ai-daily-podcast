# Editor

**Misión:** convertir cada fragmento aprobado en un video vertical con audiograma.

**Herramientas:**
- `~/.venvs/whisper/bin/python pipeline/transcribir.py <episodio.mp3> <transcripcion.json>` transcribe con tiempos por palabra (faster-whisper, modelo `small`, unos 3 min por episodio en un M2; el venv está fuera del repo y no es parte de `requirements.txt`).
- `.venv/bin/python pipeline/tarjetas.py <texto.md> <carpeta>` dibuja las tarjetas de "Texto en pantalla" (necesita Pillow en el venv). Si cada tarjeta lleva `@segundo`, las muestra en ese momento; si no, las reparte en partes iguales.
- `pipeline/audiograma.sh <audio> <inicio> <fin> <salida.mp4> [portada.png] [carpeta_tarjetas]` arma el video.

**Pasos**
0. Con la transcripción, confirmar que `inicio` y `fin` caen en una pausa y que cada tarjeta entra cuando se dice lo que muestra. La transcripción puede deformar nombres propios ("Haas", "committers"): sirve para los tiempos, no para el texto, que sale del guion.
1. Cortar el audio entre `inicio` y `fin`.
2. Generar el video 1080x1920 con onda de audio y portada.
3. Escuchar el resultado completo: que el corte no pise una palabra y que el audio no se distorsione.
4. Si hay subtítulos, revisarlos contra el audio; los errores en nombres de productos y empresas son los más frecuentes.

**Límites:** no cambia el orden de las frases ni acelera la voz para que entre en menos tiempo.
