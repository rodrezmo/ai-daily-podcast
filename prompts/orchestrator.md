# Orquestador diario

Corrés el pipeline de un show. Recibís `<id>` (por ejemplo `ia`). Trabajás con `shows/<id>.yaml`, en es-AR. Fecha de trabajo: hoy en `America/Argentina/Buenos_Aires` (`YYYY-MM-DD`, a la que llamo `<día>`).

**Regla madre:** si algo falla, no se publica nada. Un episodio faltante es mejor que uno roto. No reintentes más de una vez cada paso.

Carpeta de trabajo: `episodes/<id>/<día>/`.

**Paso 0, preparación:** `bash scripts/setup.sh` (crea `.venv`). Todos los comandos de Python de abajo usan `.venv/bin/python`.

## Pasos
1. **Investigar.** Lanzá un subagente con `prompts/researcher.md` (modelo y esfuerzo en `agents.researcher`). Guardá `candidatas.json`. Pasale también los títulos y URLs de `discarded` del `meta.json` del episodio anterior para que busque novedades o la fuente primaria de esos temas. Si la primera pasada deja menos de 8 candidatas nuevas tras el filtro, hacé una segunda pasada ampliada (más fuentes, changelogs oficiales) y juntá ambas listas.
2. **Anti-repetición.** `.venv/bin/python scripts/seen.py filter --show <id> episodes/<id>/<día>/candidatas.json > episodes/<id>/<día>/nuevas.json`
3. **Selección.** Elegí `episode.stories` notas de `nuevas.json` y guardalas en `elegidas.json`. Criterios: impacto práctico para la audiencia, dato verificable, fuente primaria, variedad de temas. Descartá el hype. Guardá en `descartadas.json` todas las candidatas nuevas que no elegiste, cada una con `title`, `url` y `reason` (motivo breve del descarte). Si quedan menos de 5 notas buenas, cortá: no hay episodio hoy.
4. **Guion.** Subagente con `prompts/writer.md` (`agents.writer`). Le pasás el yaml, `elegidas.json`, `descartadas.json`, `recientes.json` (entradas de `state/seen.json` de este show de los últimos 7 días, con título y fecha) y la fecha. Guardá `guion-borrador.txt`.
5. **Verificación.** Subagente con `prompts/verifier.md` (`agents.verifier`). Guardá el guion corregido en `guion.txt` y el reporte en `verificacion.json`. Si `ok_to_publish` es `false`, cortá.
6. **Metadatos.** Escribí `meta.json` con: `title` (título del episodio con fecha y el tema más fuerte, sin clickbait), `summary` (2 o 3 frases) y `stories` (las notas que quedaron en el guion final, cada una con `title` y `url`) y `discarded` (las notas descartadas que se nombran en la sección "Quedaron afuera", con `title` y `url`).
7. **Entrega del guion.** `git add episodes/<id>/<día>/guion.txt episodes/<id>/<día>/meta.json && git commit -m "Guion <id> <día>" && git push origin HEAD:main`. El audio y la publicación los hace después el workflow `.github/workflows/publish.yml` (GitHub Actions), porque las sesiones de la Routine no pueden crear Releases.
Terminá acá: no generes audio ni publiques. Si el push falla, el episodio no sale y el vigilante de las 07:30 avisa.

## Al fallar
Si falla un paso, no subas nada y terminá explicando en una o dos líneas qué paso falló y por qué. No abras issues (en las sesiones de la Routine `gh issue` no funciona). El aviso lo da el vigilante (`watchdog.yml`) cuando a las 07:30 ART falta el episodio en el feed.
