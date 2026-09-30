"""Chemins du studio et accès aux outils externes (tsrct, ffmpeg, ffprobe)."""
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIB = ROOT / "bibliotheque"
CATALOGUE = BIB / "catalogue.json"
APERCUS = BIB / "apercus"
RECETTES = ROOT / "recettes"
PROJETS = ROOT / "Projets"
INBOX = ROOT / "A-AJOUTER"
CACHE = ROOT / ".studio-work" / "cache"
PAGE = ROOT / "catalogue.html"

TSRCT_VERSION = "0.2.0"

# type -> (dossier, extensions acceptées)
TYPES = {
    "sfx": ("sfx", {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}),
    "musique": ("musiques", {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}),
    "ambiance": ("ambiances", {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}),
    "vfx": ("vfx", {".mp4", ".mov", ".m4v"}),
    "image": ("images", {".png", ".jpg", ".jpeg", ".webp"}),
    "police": ("polices", {".ttf", ".otf", ".ttc"}),
    "texte-fx": ("textes-fx", {".json"}),
    "sous-titres": ("sous-titres", {".json"}),
}
AUDIO_EXT = TYPES["sfx"][1]
VIDEO_EXT = TYPES["vfx"][1]


class OutilManquant(RuntimeError):
    pass


def _first(paths):
    for p in paths:
        if p and Path(p).is_file():
            return str(p)
    return None


def tsrct_path():
    found = _first([
        os.environ.get("TSRCT"),
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract\bin\tsrct.cmd") if os.name == "nt" else None,
        str(Path.home() / "Library/Application Support/Tesseract/bin/tsrct"),
        shutil.which("tsrct"),
    ])
    if not found:
        raise OutilManquant("tsrct introuvable : lance installer.ps1")
    return found


def _winget_bin(name):
    base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    hits = glob.glob(os.path.join(base, "Gyan.FFmpeg*", "*", "bin", name + ".exe"))
    return hits[0] if hits else None


def ffmpeg_path(name="ffmpeg"):
    found = shutil.which(name) or (_winget_bin(name) if os.name == "nt" else None)
    if not found:
        raise OutilManquant(f"{name} introuvable : lance installer.ps1")
    return found


def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    return subprocess.run([str(c) for c in cmd], **kw)


def tsrct(*args, check=True):
    """Lance tsrct et renvoie la réponse JSON (ou le texte brut)."""
    r = run([tsrct_path(), *args])
    if check and r.returncode != 0:
        raise RuntimeError(f"tsrct {' '.join(map(str, args[:2]))} a échoué :\n{r.stderr.strip() or r.stdout.strip()}")
    out = r.stdout.strip()
    try:
        return json.loads(out) if out else {}
    except json.JSONDecodeError:
        return out


def ffprobe(path):
    r = run([ffmpeg_path("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe ne lit pas {path} : {r.stderr.strip()}")
    return json.loads(r.stdout)


def say(*a):
    print(*a, flush=True)


def fail(msg, code=1):
    print(f"ERREUR : {msg}", file=sys.stderr, flush=True)
    sys.exit(code)
