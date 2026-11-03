"""Build the sampled drum kits in static/kits/ from Hydrogen drumkits.

    python tools/build_kits.py <folder with the extracted kits>

Needs ffmpeg and numpy. The folder must contain AVLDrumkits-BlackPearl-2023/, AVLDrumkits-BlondeBop/ (from the Hydrogen
sound library on SourceForge) and GMRockKit/ (from the Hydrogen repo, data/drumkits/GMRockKit).

For every sound four velocity layers are kept (ghost, soft, normal, accent). Each sound is
normalized on its loudest layer, so the layers keep their natural dynamics, then scaled by a mix
gain. Trailing silence is cut and the result is written as FLAC plus a kits.json manifest.
"""

import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "static" / "kits"
SR = 44100
MAX_LEN = {"crash": 3.5, "ride": 3.0, "ride_bell": 3.0, "hh_open": 2.0}
MIX = {
    "kick": 1.0, "snare": 0.9, "rim": 0.8, "hh_closed": 0.55, "hh_open": 0.55, "hh_pedal": 0.5,
    "crash": 0.6, "ride": 0.55, "ride_bell": 0.6, "tom_hi": 0.85, "tom_mid": 0.85, "tom_floor": 0.9,
}

AVL_LAYERS = ["2", "3", "4", "5"]
GM_LAYERS = ["Soft", "Med", "Hard", "Hardest"]

KITS = {
    "pearl": {
        "name": "Pearl (rock)",
        "dir": "AVLDrumkits-BlackPearl-2023/AVLDrumkits-BlackPearl-2023",
        "credit": "AVL Drumkits Black Pearl 2023 by Glen MacArthur, CC BY-SA",
        "layers": AVL_LAYERS,
        "sounds": {
            "kick": "36-Pearl-22-Kick-{}", "snare": "38-Pearl-14-Snare-{}", "rim": "37-Pearl-14-SideStick-{}",
            "hh_closed": "42-Sabian-13-HatClosed-{}", "hh_open": "46-Sabian-13-HatSemi-{}",
            "hh_pedal": "44-Sabian-13-HatPedal-{}", "crash": "49-SabianAA-16-Crash-{}",
            "ride": "51-SabianAAX-20-Ride-{}", "ride_bell": "53-SabianAAX-20-RideBell-{}",
            "tom_hi": "45-Pearl-12-Tom-{}", "tom_mid": ("45-Pearl-12-Tom-{}", 0.84),
            "tom_floor": "41-Pearl-16-FloorTom-{}",
        },
    },
    "tama": {
        "name": "Tama (jazz)",
        "dir": "AVLDrumkits-BlondeBop/AVLDrumkits-BlondeBop",
        "credit": "AVL Drumkits Blonde Bop by Glen MacArthur, CC BY-SA",
        "layers": AVL_LAYERS,
        "sounds": {
            "kick": "36-TAMA-18-Kick-{}", "snare": "38-TAMA-13-Snare-{}", "rim": "37-TAMA-13-SideStick-{}",
            "hh_closed": "42-Zildjian-13-HatClosed-{}", "hh_open": "46-Zildjian-13-HatSemi-{}",
            "hh_pedal": "44-Zildjian-13-HatPedal-{}", "crash": "49-Paiste2002-16-Crash-{}",
            "ride": "51-SabianAAX-20-RideTip-{}", "ride_bell": "53-SabianAAX-20-RideBell-{}",
            "tom_hi": "45-TAMA-10-Tom-{}", "tom_mid": ("45-TAMA-10-Tom-{}", 0.84),
            "tom_floor": "41-TAMA-14-FloorTom-{}",
        },
    },
    "gmrock": {
        "name": "GM Rock",
        "dir": "GMRockKit",
        "credit": "Hydrogen GMRockKit by Glen MacArthur / Sebastian Moors, GPL",
        "layers": GM_LAYERS,
        "sounds": {
            "kick": "Kick-{}", "snare": "Snare-{}", "rim": "SnareRimshot-{}",
            "hh_closed": "HatClosed-{}", "hh_open": "HatOpen-{}", "hh_pedal": "HatPedal-{}",
            "crash": "Crash-{}", "ride": "Ride-{}", "ride_bell": "Bell-{}",
            "tom_hi": "Tom1-{}", "tom_mid": "Tom2-{}", "tom_floor": "TomFloor-{}",
        },
    },
}


def read(path, rate=1.0):
    """Mono float samples at SR; `rate` < 1 lowers the pitch (used to make a second tom)."""
    filters = f"asetrate={SR * rate},aresample={SR}" if rate != 1.0 else f"aresample={SR}"
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-af", filters,
                        "-ac", "1", "-c:a", "pcm_s16le", tmp.name], check=True)
        with wave.open(tmp.name) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return data.astype(np.float32) / 32768


def trim(x, max_len):
    # Start right at the attack (some samples have a few ms of silence, which would sound late)
    # and cut where it stays below -60 dB, with a short fade so nothing clicks.
    peak = np.abs(x).max()
    start = max(0, int(np.argmax(np.abs(x) > peak * 0.1)) - int(0.002 * SR))
    loud = np.flatnonzero(np.abs(x) > 0.001)
    end = min(len(x), (loud[-1] + 1) if len(loud) else len(x), start + int(max_len * SR))
    x = x[start:end].copy()
    fade = min(len(x), int(0.02 * SR))
    x[len(x) - fade:] *= np.linspace(1, 0, fade)
    return x


def write_flac(x, path):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", "-", "-c:a", "flac", str(path)], input=pcm.tobytes(), check=True)


def main(src):
    src = Path(src)
    manifest = {}
    for kit_id, kit in KITS.items():
        out_dir = OUT / kit_id
        out_dir.mkdir(parents=True, exist_ok=True)
        sounds = {}
        for name, spec in kit["sounds"].items():
            pattern, rate = spec if isinstance(spec, tuple) else (spec, 1.0)
            layers = [read(src / kit["dir"] / (pattern.format(v) + ".wav"), rate) for v in kit["layers"]]
            gain = 0.89 * MIX[name] / max(np.abs(layers[-1]).max(), 1e-6)  # loudest layer to about -1 dB
            files = []
            for i, x in enumerate(layers):
                fname = f"{name}-{i}.flac"
                write_flac(trim(x * gain, MAX_LEN.get(name, 1.5)), out_dir / fname)
                files.append(f"{kit_id}/{fname}")
            sounds[name] = files
            print(f"{kit_id:7s} {name:10s} {len(files)} layers")
        manifest[kit_id] = {"name": kit["name"], "credit": kit["credit"], "sounds": sounds}
    (OUT / "kits.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
