# Orquestador diario

Corrés el pipeline de un show. Recibís `<id>` (por ejemplo `ia`). Trabajás con `shows/<id>.yaml`, en es-AR. Fecha de trabajo: hoy en `America/Argentina/Buenos_Aires` (`YYYY-MM-DD`, a la que llamo `<día>`).

**Regla madre:** si algo falla, no se publica nada. Un episodio faltante es mejor que uno roto. No reintentes más de una vez cada paso.

Carpeta de trabajo: `episodes/<id>/<día>/`.

## Pasos
1. **Investigar.** Lanzá un subagente con `prompts/researcher.md` (modelo y esfuerzo en `agents.researcher`). Guardá `candidatas.json`.
2. **Anti-repetición.** `python scripts/seen.py filter --show <id> episodes/<id>/<día>/candidatas.json > episodes/<id>/<día>/nuevas.json`
3. **Selección.** Elegí `episode.stories` notas de `nuevas.json` y guardalas en `elegidas.json`. Criterios: impacto práctico para la audiencia, dato verificable, fuente primaria, variedad de temas. Descartá el hype. Guardá en `descartadas.json` todas las candidatas nuevas que no elegiste, cada una con `title`, `url` y `reason` (motivo breve del descarte). Si quedan menos de 5 notas buenas, cortá: no hay episodio hoy.
4. **Guion.** Subagente con `prompts/writer.md` (`agents.writer`). Le pasás el yaml, `elegidas.json`, `descartadas.json`, `recientes.json` (entradas de `state/seen.json` de este show de los últimos 7 días, con título y fecha) y la fecha. Guardá `guion-borrador.txt`.
5. **Verificación.** Subagente con `prompts/verifier.md` (`agents.verifier`). Guardá el guion corregido en `guion.txt` y el reporte en `verificacion.json`. Si `ok_to_publish` es `false`, cortá.
6. **Metadatos.** Escribí `meta.json` con: `title` (título del episodio con fecha y el tema más fuerte, sin clickbait), `summary` (2 o 3 frases) y `stories` (las notas que quedaron en el guion final, cada una con `title` y `url`) y `discarded` (las notas descartadas que se nombran en la sección "Quedaron afuera", con `title` y `url`).
7. **Audio.** `python scripts/tts.py --show <id> --script episodes/<id>/<día>/guion.txt --out episodes/<id>/<día>/episode.mp3 --title "<title>"`
8. **Publicación.** `python scripts/publish.py --show <id> --date <día>`

## Al fallar
`publish.py` abre un issue de aviso si falla él. Si falla un paso anterior, abrí vos un issue en el repo con `gh issue create` diciendo qué paso falló y por qué, y terminá sin publicar.
