#!/usr/bin/env bash
# Prepara el entorno (Routine en Ubuntu, o local): ffmpeg y dependencias de Python.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { (apt-get update -qq && apt-get install -y -qq ffmpeg) >/dev/null; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
echo "setup ok: $(ffmpeg -version | head -1 | cut -c1-30)"
