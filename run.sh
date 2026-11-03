#!/usr/bin/env bash
# Keftemulator launcher: sets up the venv on first run, then starts the GUI.
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
export PATH="$PWD/tools/bin:$HOME/.local/bin:$PATH"
( sleep 1.5; xdg-open "http://127.0.0.1:${PORT:-5050}" >/dev/null 2>&1 || true ) &
exec .venv/bin/python -m keftemulator.web --port "${PORT:-5050}" "$@"
