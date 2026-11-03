"""drums4all: web app to write drum tabs and practice them with a metronome.

The tabs are plain .txt files in tabs/ (you can also edit them by hand).
The audio is generated in the browser, which is the only place that can
play it with sample-accurate timing.

    python app.py                  # http://127.0.0.1:8484
    python app.py --open           # ...and open it in the browser
    python app.py --host 0.0.0.0   # reachable from the phone on the same network
"""

import argparse
import logging
import os
import re
import shutil
import tempfile
import threading
import unicodedata
import webbrowser
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from flask import cli as flask_cli

ROOT = Path(__file__).parent
EXAMPLES = ROOT / "static" / "examples"
ID_RE = re.compile(r"[\w\- ]{1,80}")
TITLE_RE = re.compile(r"^\s*title\s*:\s*(.+?)\s*$", re.I | re.M)

app = Flask(__name__, static_folder=ROOT / "static", static_url_path="/static")
app.config["TABS"] = ROOT / "tabs"
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


def tabs_dir():
    return Path(app.config["TABS"])


def title_of(text):
    m = TITLE_RE.search(text)
    return m.group(1) if m else "Untitled"


def slugify(title):
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:40] or "tab"


def tab_path(tab_id):
    if not ID_RE.fullmatch(tab_id) or tab_id.strip() != tab_id:
        abort(404)
    return tabs_dir() / f"{tab_id}.txt"


def read_text_field():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        abort(400, "expected JSON with a 'text' field")
    return data["text"]


def write_atomic(path, text):
    # Write to a temp file and rename, so a crash never leaves a half-written tab.
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, path)


def seed():
    """On first run, start with the examples."""
    tabs_dir().mkdir(parents=True, exist_ok=True)
    if not any(tabs_dir().glob("*.txt")):
        for f in EXAMPLES.glob("*.txt"):
            shutil.copy(f, tabs_dir() / f.name)


@app.get("/")
def index():
    return send_from_directory(ROOT / "static", "index.html")


@app.get("/api/tabs")
def list_tabs():
    tabs = []
    for p in tabs_dir().glob("*.txt"):
        if ID_RE.fullmatch(p.stem):
            tabs.append({"id": p.stem, "title": title_of(p.read_text(encoding="utf-8", errors="replace"))})
    tabs.sort(key=lambda t: t["title"].lower())
    return jsonify(tabs)


@app.get("/api/tabs/<tab_id>")
def get_tab(tab_id):
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    text = path.read_text(encoding="utf-8", errors="replace")
    return jsonify({"id": tab_id, "title": title_of(text), "text": text})


@app.put("/api/tabs/<tab_id>")
def save_tab(tab_id):
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    text = read_text_field()
    write_atomic(path, text)
    return jsonify({"id": tab_id, "title": title_of(text)})


@app.post("/api/tabs")
def create_tab():
    text = read_text_field()
    base = slugify(title_of(text))
    tab_id, n = base, 2
    while (tabs_dir() / f"{tab_id}.txt").exists():
        tab_id, n = f"{base}-{n}", n + 1
    write_atomic(tabs_dir() / f"{tab_id}.txt", text)
    return jsonify({"id": tab_id, "title": title_of(text)}), 201


@app.delete("/api/tabs/<tab_id>")
def delete_tab(tab_id):
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    path.unlink()
    return "", 204


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
def api_error(e):
    return jsonify({"error": e.description}), e.code


def main():
    ap = argparse.ArgumentParser(description="drums4all: write drum tabs and practice them with a metronome.")
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to open it from other devices on the network")
    # Not 5000: macOS uses it for AirPlay.
    ap.add_argument("--port", type=int, default=8484)
    ap.add_argument("--open", action="store_true", help="open the app in the browser")
    ap.add_argument("--tabs", type=Path, default=app.config["TABS"], help="folder where the tabs (.txt) are kept")
    args = ap.parse_args()
    app.config["TABS"] = args.tabs
    seed()
    url = f"http://127.0.0.1:{args.port}"
    print(f"drums4all is running at {url}  (tabs in {args.tabs.resolve()})", flush=True)
    print("Keep this window open while you use it; close it (or press Ctrl+C) to stop.", flush=True)
    if args.open:
        threading.Timer(1.0, webbrowser.open, [url]).start()
    # Flask's banner and per-request log only confuse people running it with a double-click.
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    flask_cli.show_server_banner = lambda *args, **kwargs: None
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
