#!/usr/bin/env bash
# Prepara el entorno (Routine en Ubuntu, o local): ffmpeg, gh, dependencias de Python e identidad de git.
set -euo pipefail
cd "$(dirname "$0")/.."
SUDO=""; [ "$(id -u)" = 0 ] || SUDO="sudo"
need=()
command -v ffmpeg >/dev/null || need+=(ffmpeg)
command -v gh >/dev/null || need+=(gh)
if [ ${#need[@]} -gt 0 ]; then
  $SUDO apt-get update -qq >/dev/null 2>&1 || true
  $SUDO apt-get install -y -qq "${need[@]}" >/dev/null
fi
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
git config user.name >/dev/null || git config user.name "Radar IA"
git config user.email >/dev/null || git config user.email "radar-ia@users.noreply.github.com"
echo "setup ok: $(ffmpeg -version | head -1 | cut -c1-30) | $(gh --version | head -1)"
