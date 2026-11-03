# drums4all: notes for Claude

Web app to write drum tabs (drumtabs.app style), see them as sheet music and practice with a metronome.
The user is a drummer practising with it; they talk in European Portuguese, but **everything in the app, code,
comments, examples and docs is in English**.

## Rules

- **Never make git commits** (not even with a different author). The user commits everything themselves and wants
  only their own commits in the repo. Don't add Claude attribution anywhere. At the time of writing the GitHub repo
  doesn't exist yet; the user will create it.
- Don't touch the user's tabs in `tabs/` unless asked (it's their data and it's git-ignored). Back them up first if
  you must change them.
- Keep the app working both **with the Flask server** and **as a static site** (any static host, tabs in
  localStorage). The user does **not** want to publish it from this repo (no GitHub Pages workflow); the README
  only explains how others can host their own copy.
  Use relative URLs in the page (`static/...`, `api/tabs`), never absolute ones.

## Run and test

```sh
.venv/bin/python app.py [--port 8484] [--tabs DIR] [--open] [--host 0.0.0.0]
.venv/bin/python -m unittest discover -s tests          # API tests
```

Port 8484 (5000 clashes with AirPlay on macOS). For UI checks use headless Chrome through the DevTools protocol
(`google-chrome --headless=new --remote-debugging-port=... --remote-allow-origins=* --autoplay-policy=no-user-gesture-required`
+ `websocket-client` in the venv): run the server with `--tabs` pointing to a scratch folder, evaluate JS
(`S`, `R`, `lib`, `store`, `sheetBoxes`, `buildMidi`, `exportPdf`, ...), take screenshots and look at them.
Convert PDFs with `pdftoppm` to look at them. Audio can't be heard in tests: check buffers/WAV/MIDI numerically.

## Layout

- `app.py`: Flask. `/` serves `static/index.html`; `/api/tabs` lists/gets/creates/updates/deletes `tabs/*.txt`
  (atomic writes, ids are slugs of the title). Seeds `tabs/` from `static/examples/` when empty.
- `static/index.html`: the whole front end, one file, sections marked `// ------ name`:
  tab model (parse/serialize), sounds, scheduling, state, transport, controls, editing, note picker, keyboard,
  library (serverStore / localStore), exports (wav, MIDI, PDF), grid editor (canvas), sheet music (VexFlow), frame loop.
- `static/examples/*.txt` + `examples.json` (list used by the static-site mode).
- `static/kits/<kit>/<sound>-<0..3>.flac` + `kits.json`: sampled kits, 4 velocity layers (ghost, soft, normal,
  accent). Rebuild with `tools/build_kits.py <dir with extracted Hydrogen kits>` (ffmpeg + numpy). Sources:
  AVL Drumkits Black Pearl 2023 and Blonde Bop (CC BY-SA), Hydrogen GMRockKit (GPL). Samples are trimmed to start
  at the attack (≤ 2 ms), or they sound late.
- `static/vendor/`: VexFlow 4.2.3, jsPDF 2.5.1, svg2pdf.js 2.2.3 (kept local, offline).
- `start.sh` / `start.command` / `start.bat`: double-click launchers for non-technical users
  (create `.venv`, `pip install -r requirements.txt`, `app.py --open`). The `.bat` and `.command` were never run on
  real Windows/macOS.
- `docs/screenshots/`: README images (1440×900 headless Chrome: `funk` example playing, note picker on the snare,
  `rudiments` sheet). Retake them after visible UI changes.

## Tab model and format

- Text format: `Title:`, `Tempo:`, `Time:` headers; one row per instrument (`C R HH T1 T2 S FT B HF`), `|` between
  bars, one character per grid step; optional `TS|3/4|4/4|` row for per-bar time signatures; count line ignored.
- Optional `ST|RLU-|` row: sticking (`bar.sticking`, same length as the bar), drawn as bold letters under the
  notes on the sheet/PDF. The grid shows it as an extra `ST` row (`gridRows`, `rowOf`, `setRow`); resample/
  time-signature/copy/paste/clear carry it.
- Model: each bar has its own `beats/unit` and one `steps` count shared by all instruments (`steps/beats` =
  subdivision: 2 eighths, 3 triplets, 4 sixteenths...). Rests are `-`. `serialize(parse(x))` must round-trip.
- Symbols: `o x` hit, upper case accent, `g` ghost, `f` flam, `x` on S = rim, `o` on HH = open, `b` on R = bell.
- BPM always counts quarter notes. Grid edits re-serialize the whole file into the canonical format.

## Decisions the user made (don't undo them)

- **Sheet music must look like drumtabs.app**: percussion clef, **one voice, all stems up** (bass drum in the same
  chord), **flat beams**, accented snare (`O`/`X`) drawn as **x notehead + `>`**, open hi-hat as **circled x**
  (`x3`), triplets marked with a **small italic "3"** next to the accent (VexFlow's Tuplet is created for the
  timing but not drawn), tempo mark at the top, bar numbers at line starts. Positions: crash above the staff with a
  ledger line, hi-hat in the space above the staff, ride on the top line. Generous spacing (`SHEET_SPACING`, `SYS_H`),
  same on screen and in the PDF.
- **Note entry**: click a cell → a picker menu with the notes for that instrument (no double-click / toggling).
  Keyboard typing also works.
- **Look**: background `#181818`, rexim's Gruber Darker colours **without the yellow** (niagara blue-grey for
  notes/active, brown for accents, wisteria for ghosts, green play, red stop/playhead), monospace UI, flat and calm,
  "not AI-looking". Sheet on a light paper.
- **Sounds**: real recorded acoustic kits (the user disliked synthesized drums). The metronome sounds are synthesized
  (beep, woodblock, cowbell).
- Name **drums4all**; README credits drumtabs.app as the inspiration (author unknown, Ko-fi `treefordev`).

## Ideas not done yet

- Triplets/subdivision per beat (today it's per bar).
- Rimshot vs accent look the same on the snare in the sheet (both x + `>`), on purpose like drumtabs.
- Pearl/Tama kits have no fully open hi-hat sample (semi-open is used) and one rack tom (tom 2 is it pitched down).
- Launchers untested on Windows/macOS; static hosting only tested locally (sub-folder served by `http.server`).
