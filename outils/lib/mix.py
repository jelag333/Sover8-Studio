"""Niveaux pour le sound design : chaque SFX est calé à X dB sous la voix (jamais au hasard, jamais fort)."""
import json
from pathlib import Path

import numpy as np

from . import analyse
from .catalogue import sha256
from .config import BIB, CACHE

# écart sous le niveau MÉDIAN de la voix (dB). Apparitions (pop, clic, magie) : -3 dB par rapport au premier essai, sur retour utilisateur (« légèrement trop fort ; si l'oreille l'entend c'est bien, sinon pas grave »)
SOUS_VOIX = {"pop": 14, "clic": 16, "whoosh": 13, "magie": 14, "notification": 13, "comique": 10, "impact": 12,
             "transition": 14, "riser": 15, "downlifter": 15, "meme": 11}
GAIN_MAX = 0.8


def _win_db(x, sr, win_ms):
    n = max(1, int(sr * win_ms / 1000))
    k = len(x) // n
    if k == 0:
        return np.array([-120.0])
    r = np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r)


def voice_level(path):
    """Niveau typique de la parole (dBFS) : médiane des fenêtres de 400 ms où quelqu'un parle."""
    path = Path(path)
    cache = CACHE / f"{sha256(path)[:16]}-voix-db.json"
    if cache.exists():
        return json.loads(cache.read_text())["db"]
    x = analyse.decode_mono(path)
    w = _win_db(x, analyse.SR, 400)
    speech = w[w > w.max() - 25]
    db = float(np.median(speech))
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"db": db}))
    return db


def sfx_level(entry):
    """Niveau perçu du SFX (dBFS) : fenêtre de 100 ms la plus forte."""
    if "niveau_pic_db" in entry.get("tech", {}):
        return entry["tech"]["niveau_pic_db"]
    x = analyse.decode_mono(BIB / entry["fichier"])
    return float(_win_db(x, analyse.SR, 100).max())


def gain(entry, voice_db, sous_voix_db=None):
    role = entry.get("usage", {}).get("role", "pop")
    under = SOUS_VOIX.get(role, 14) if sous_voix_db is None else float(sous_voix_db)
    g = 10 ** ((voice_db - under - sfx_level(entry)) / 20)
    return round(min(GAIN_MAX, g), 3)
