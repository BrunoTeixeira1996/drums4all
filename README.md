# drums4all

Write drum tabs, see them as sheet music and practice them **with a metronome**, in the browser.

![drums4all: the grid editor with a groove playing, and its sheet music](docs/screenshots/main.png)

<p>
  <img src="docs/screenshots/picker.png" alt="Click a cell and pick the note" width="49%">
  <img src="docs/screenshots/sheet.png" alt="Sheet music with accents and triplets" width="49%">
</p>

## Inspiration and credits

drums4all is very, very much inspired by **[drumtabs.app](https://drumtabs.app/)**: the tab format, the grid editor
and the way the sheet music looks all come from there. Huge props to the developer behind drumtabs.app for a great
tool. If you like this, go use the original and support its author on [Ko-fi](https://ko-fi.com/treefordev).
drums4all only exists because I wanted a metronome and a few practice tools on top of that idea.

## Using it (no technical knowledge needed)

1. **Get the files.** On the GitHub page, click **Code → Download ZIP** and unzip it somewhere (e.g. your Desktop).
2. **Install Python 3** (only once) from <https://www.python.org/downloads/>.
   On Windows, tick **"Add python.exe to PATH"** at the start of the installer.
3. **Start drums4all** by double-clicking the file for your system, inside the unzipped folder:
   - Windows: `start.bat`
   - macOS: `start.command` (the first time, right-click it → **Open** → **Open**)
   - Linux: `start.sh` (or run `./start.sh` in a terminal)

The first start takes a minute (it installs what it needs). Then the browser opens at <http://127.0.0.1:8484>.
Keep the small black window open while you use it; close it to stop drums4all.
Your tabs are saved as `.txt` files in the `tabs` folder.

**On a phone or tablet** (same Wi-Fi as the computer): start it with `./start.sh --host 0.0.0.0`
(on Windows: `.venv\Scripts\python.exe app.py --host 0.0.0.0`) and open `http://<computer-ip>:8484` on the phone.
There is no password, so only do this on your home network.

## What it does

- **Grid on the left, sheet music on the right**, drawn like drumtabs.app. The sheet updates on every change and
  highlights the bar that is playing.
- **Writing notes:** click a cell and pick the note from the menu (normal, accent, ghost, flam, rim, open…),
  or type `o` `O` `x` `X` `g` `f` `b`; `-` or `Del` clears; arrows move the cursor.
- **Per-bar time signature and subdivision:** select a bar and change **Time** (e.g. a single 3/4 bar in a 4/4 song)
  or **Subdivision** (quarter notes, 8th notes, **triplets**, 16th notes, sextuplets, 32nd notes).
  **All bars** applies the selected bar's time signature to the whole tab.
- **Bars:** `+ Bar`, `Dup`, `Delete`, `Clear`, `New line`, `Copy`/`Paste` (`Ctrl+C`/`Ctrl+V`).
- **Title and Tempo** in the toolbar; `+ Instrument` adds ride, mid tom or hi-hat pedal.
- **Undo/redo:** `Ctrl+Z` / `Ctrl+Y`.
- **Text:** the `Text` button shows the tab as `.txt` (handy to paste a tab copied from drumtabs.app).
- Click a bar number to loop just that bar (`Shift`+click extends, click again to clear).
- **Sounds:** three recorded acoustic drum kits (Pearl rock kit, Tama jazz kit, GM Rock) with four velocity layers,
  so ghost notes and accents sound like the real thing, and three metronome sounds (beep, woodblock, cowbell).
- **Legends:** under the grid, what each instrument and symbol means; under the sheet music, a reference staff with
  every drum at its place (hi-hat above the staff, ride on the top line, crash above with a ledger line).
- Metronome with subdivision (÷1 to ÷4), drums on/off (metronome only), one-bar count-in,
  loop and **speed up** automatically (+N BPM every X loops up to a maximum).
- Repetition counter: play the tab (or the selected bars) N times and stop.
- Practice timer: time played this session and today, and an optional countdown (any number of minutes)
  that stops playback at the end of the bar when it runs out.
- Saves automatically. Import/export `.txt`, export `.wav`, **export PDF** (A4 sheet music)
  and **export MIDI** (General MIDI drums on channel 10, with tempo, time signature changes and velocities:
  ghost 40, normal 90, accent 120), to open in GarageBand, MuseScore, a DAW, etc.

BPM always counts quarter notes, so a 6/8 bar lasts three quarter notes and the metronome clicks the eighths.

### Keys

| Key | Action |
|---|---|
| `Space` | play / stop |
| `PgUp` `PgDn` | BPM ±1 (with `Shift`: ±5) |
| arrows, `Tab`, `Home`/`End` | move the cursor (cell, bar, start/end) |
| `o` `O` `x` `X` `g` `f` `b` | write a note |
| `-` `Del` `Backspace` | clear a note |
| `Ctrl+Z` `Ctrl+Y` | undo / redo |
| `Ctrl+C` `Ctrl+V` | copy / paste bar |
| `M` `N` `D` `C` `L` `R` | metronome, clicks per beat, drums, count-in, loop, speed up |
| `Esc` | close the menu / clear the bar loop |

## File format

```
Title: Mixed meter with triplets
Tempo: 90
Time: 4/4

TS|4/4     |3/4   |4/4         |
HH|--x-x-x-|x-x-x-|------------|
 S|----o---|--o---|oooOooOooOoo|
 B|o-------|o---o-|o-----o-----|
   1+2+3+4+ 1+2+3+ 1+a2+a3+a4+a
```

- Each line is an instrument, `|` separates bars.
- **Each character is one step of the grid.** The number of steps sets the subdivision:
  in 4/4, 4 = quarter notes, 8 = 8th notes, 12 = triplets, 16 = 16th notes.
- `TS|...|` (optional) sets the time signature of each bar in that block; otherwise `Time:` applies.
- `ST|...|` (optional) is the sticking, printed under the notes: `R`, `L`, `U` (unison, both hands) or `-`.
  In the grid it is the `ST` row under the instruments: click a cell or type `r` `l` `u`.
- Spaces inside a bar are ignored (`o · o ·` = `o·o·`), so tabs pasted from drumtabs.app work.
- Blank lines separate blocks (lines). The count line `1 + 2 +` and lines starting with `#` are ignored.

| Instrument | | Symbol | |
|---|---|---|---|
| `C` | crash | `-` `.` `·` | rest |
| `R` | ride | `o` `x` | note |
| `HH` | hi-hat | `O` `X` | accent |
| `HF` | hi-hat pedal | `g` | ghost note |
| `T1` `T2` | high / mid tom | `f` | flam |
| `FT` | floor tom | `x` on `S` | rim |
| `S` | snare | `o` on `HH` | open hi-hat |
| `B` | bass drum | `b` on `R` | ride bell |

## For developers

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py                              # http://127.0.0.1:8484
.venv/bin/python -m unittest discover -s tests       # tests
```

- `app.py`: Flask server. Serves the page and a small API (`/api/tabs`) that reads and writes the `.txt` files in
  `tabs/` (created from `static/examples/` on first run; it is in `.gitignore`).
- `static/index.html`: the whole app (grid, sheet music, sounds, metronome, exports). Sound is generated in the
  browser with the Web Audio API and every note is scheduled on the audio clock, so timing is exact. When there is
  no server (static hosting), tabs are kept in the browser's `localStorage` instead.
- `static/kits/`: drum samples (FLAC) and `kits.json`, built by `tools/build_kits.py` (needs ffmpeg and numpy)
  from [Hydrogen](http://hydrogen-music.org/) drumkits.
- `static/vendor/`: VexFlow, jsPDF and svg2pdf.js, kept locally so it works offline.
- `start.sh`, `start.command`, `start.bat`: one-click launchers (create `.venv`, install, run `app.py --open`).

### Hosting your own copy online

drums4all also works as a plain static site, without `app.py`: then each visitor's tabs are saved in their own
browser (the page starts with the examples). To put it on any static host (GitHub Pages on your fork, Netlify,
your own server...), publish `static/index.html` as the site's `index.html` next to the `static/` folder:

```sh
mkdir site
cp static/index.html site/index.html
cp -r static site/static
# upload the contents of site/ (on GitHub Pages, also add an empty site/.nojekyll)
```

All paths in the page are relative, so it also works from a sub-folder like `https://<user>.github.io/drums4all/`.

### Third-party material

- Drum samples:
  - Pearl and Tama kits: AVL Drumkits *Black Pearl 2023* and *Blonde Bop* by Glen MacArthur, CC BY-SA.
  - GM Rock kit: Hydrogen *GMRockKit* by Glen MacArthur / Sebastian Moors, GPL.
- [VexFlow](https://www.vexflow.com/) 4.2.3 (MIT), [jsPDF](https://github.com/parallax/jsPDF) 2.5.1 (MIT),
  [svg2pdf.js](https://github.com/yWorks/svg2pdf.js) 2.2.3 (MIT).
