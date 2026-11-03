#!/bin/sh
# drums4all for Linux: run this file (or double-click it and choose "Run").
# The first time it installs what it needs, then it opens the app in the browser.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "Python 3 is needed. Install it from https://www.python.org/downloads/ (or: sudo apt install python3 python3-venv)"
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "First run: setting things up (this takes a minute)..."
  "$PY" -m venv .venv || { echo "Couldn't create the Python environment. On Debian/Ubuntu: sudo apt install python3-venv"; exit 1; }
fi
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt || exit 1
exec .venv/bin/python app.py --open "$@"
