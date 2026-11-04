"""drums4all: web app to write drum tabs and practice them with a metronome.

The tabs are plain .txt files in tabs/, optionally one folder deep
(tabs/exercises/paradiddle.txt); you can also edit them by hand.
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
NAME_RE = re.compile(r"[\w\- ]{1,80}")
FOLDER_RE = re.compile(r"[\w\- ]{1,40}")
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


def valid_name(name, pattern=NAME_RE):
    return bool(pattern.fullmatch(name)) and name.strip() == name


def split_id(tab_id):
    """"exercises/paradiddle" -> ("exercises", "paradiddle"); no folder -> ("", name)."""
    folder, _, name = tab_id.rpartition("/")
    if not valid_name(name) or (folder and not valid_name(folder, FOLDER_RE)):
        return None
    return folder, name


def tab_path(tab_id):
    if not split_id(tab_id):
        abort(404)
    return tabs_dir() / f"{tab_id}.txt"


def read_folder():
    data = request.get_json(silent=True) or {}
    folder = data.get("folder") or ""
    if not isinstance(folder, str) or (folder and not valid_name(folder, FOLDER_RE)):
        abort(400, "invalid folder name (letters, numbers, spaces, - and _)")
    return folder


def free_id(folder, base):
    """The first id not taken: base, base-2, base-3..."""
    prefix = f"{folder}/" if folder else ""
    tab_id, n = prefix + base, 2
    while (tabs_dir() / f"{tab_id}.txt").exists():
        tab_id, n = f"{prefix}{base}-{n}", n + 1
    return tab_id


def remove_if_empty(folder_path):
    if folder_path != tabs_dir() and not any(folder_path.iterdir()):
        folder_path.rmdir()


def tab_info(tab_id, text):
    return {"id": tab_id, "title": title_of(text), "folder": split_id(tab_id)[0]}


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
    if not any(tabs_dir().glob("*.txt")) and not any(tabs_dir().glob("*/*.txt")):
        for f in EXAMPLES.glob("*.txt"):
            shutil.copy(f, tabs_dir() / f.name)


@app.get("/")
def index():
    return send_from_directory(ROOT / "static", "index.html")


@app.get("/api/tabs")
def list_tabs():
    tabs = []
    for p in [*tabs_dir().glob("*.txt"), *tabs_dir().glob("*/*.txt")]:
        tab_id = p.relative_to(tabs_dir()).with_suffix("").as_posix()
        if split_id(tab_id):
            tabs.append(tab_info(tab_id, p.read_text(encoding="utf-8", errors="replace")))
    tabs.sort(key=lambda t: (t["folder"].lower(), t["title"].lower()))
    return jsonify(tabs)


@app.get("/api/tabs/<path:tab_id>")
def get_tab(tab_id):
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    text = path.read_text(encoding="utf-8", errors="replace")
    return jsonify({**tab_info(tab_id, text), "text": text})


@app.put("/api/tabs/<path:tab_id>")
def save_tab(tab_id):
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    text = read_text_field()
    write_atomic(path, text)
    return jsonify(tab_info(tab_id, text))


@app.post("/api/tabs")
def create_tab():
    text = read_text_field()
    folder = read_folder()
    tab_id = free_id(folder, slugify(title_of(text)))
    (tabs_dir() / folder).mkdir(parents=True, exist_ok=True)
    write_atomic(tabs_dir() / f"{tab_id}.txt", text)
    return jsonify(tab_info(tab_id, text)), 201


@app.post("/api/tabs/<path:tab_id>/move")
def move_tab(tab_id):
    """Put a tab in another folder ("" = no folder). Returns its new id."""
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    folder = read_folder()
    if folder == split_id(tab_id)[0]:
        return jsonify(tab_info(tab_id, path.read_text(encoding="utf-8", errors="replace")))
    new_id = free_id(folder, split_id(tab_id)[1])
    (tabs_dir() / folder).mkdir(parents=True, exist_ok=True)
    os.replace(path, tabs_dir() / f"{new_id}.txt")
    remove_if_empty(path.parent)
    return jsonify(tab_info(new_id, (tabs_dir() / f"{new_id}.txt").read_text(encoding="utf-8", errors="replace")))


@app.delete("/api/tabs/<path:tab_id>")
def delete_tab(tab_id):
    path = tab_path(tab_id)
    if not path.exists():
        abort(404)
    path.unlink()
    remove_if_empty(path.parent)
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
