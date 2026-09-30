# Radar IA

Podcast diario de noticias de IA en es-AR, generado por agentes de Claude y publicado como feed RSS.

## Flujo
`prompts/orchestrator.md` describe el pipeline diario: investigar, anti-repetición, selección, guion, verificación, audio y publicación. Si algo falla no se publica nada.

## Estructura
- `shows/<id>.yaml`: configuración de cada show (temas, fuentes, voces, largo, modelos). Un show nuevo es un yaml nuevo.
- `prompts/`: instrucciones de cada agente.
- `scripts/tts.py`: guion a MP3 (Gemini TTS, respaldo edge-tts, ffmpeg).
- `scripts/seen.py`: filtra notas ya usadas (`state/seen.json`).
- `scripts/feed.py`: arma y valida el RSS.
- `scripts/publish.py`: sube el MP3 a Releases, actualiza feed y estado, commit y push.
- `docs/`: GitHub Pages (`feed.xml` e `index.html`).
- `episodes/<show>/<día>/`: archivos de trabajo de cada episodio (los `.mp3` no se commitean).

## Uso local
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
brew install ffmpeg
echo 'GEMINI_API_KEY=...' > .env   # gratis desde Google AI Studio; está en .gitignore
set -a && . ./.env && set +a
.venv/bin/python scripts/tts.py --show ia --script guion.txt --out episode.mp3 --title "Prueba"
```

Antes de publicar: completar `repo` y `site_url` en `shows/ia.yaml`.
