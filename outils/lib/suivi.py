"""Suivi du visage (OpenCV) : position et taille du visage dans le temps, pour cadrer zooms et recadrages."""
import json
from pathlib import Path

import numpy as np

from .catalogue import sha256
from .config import CACHE, ROOT, say

MODEL = ROOT / "outils" / "modeles" / "face_detection_yunet_2023mar.onnx"


def track_face(path, step_ms=125, force=False):
    """Renvoie [{t_ms, cx, cy, h}] en pixels source (visage le plus grand), lissé, trous interpolés."""
    import cv2
    path = Path(path)
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"{sha256(path)[:16]}-visage-{step_ms}.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text(encoding="utf-8"))
    say(f"  suivi du visage dans {path.name}…")
    if not MODEL.exists():
        raise RuntimeError(f"modèle YuNet absent ({MODEL}) : lance installer.ps1")
    cap = cv2.VideoCapture(str(path))
    det = None
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 25) * 1000
    raw = []
    t = 0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, t)
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        k = 540 / w
        small = cv2.resize(frame, None, fx=k, fy=k)
        if det is None:
            det = cv2.FaceDetectorYN.create(str(MODEL), "", (small.shape[1], small.shape[0]), 0.6, 0.3, 50)
        _, faces = det.detect(small)
        if faces is not None and len(faces):
            x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])[:4]
            raw.append((t, (x + fw / 2) / k, (y + fh / 2) / k, fh / k))
        else:
            raw.append((t, None, None, None))
        t += step_ms
    cap.release()
    ts = np.array([r[0] for r in raw], float)
    out = []
    ok = np.array([r[1] is not None for r in raw])
    if ok.sum() < 2:
        raise RuntimeError("visage introuvable dans la vidéo")
    cols = []
    for i in (1, 2, 3):
        v = np.array([r[i] if r[i] is not None else np.nan for r in raw], float)
        # rejet des détections aberrantes (écart > 3 médianes locales), interpolation, lissage
        med = np.array([np.nanmedian(v[max(0, j - 4):j + 5]) for j in range(len(v))])
        v[np.abs(v - med) > 0.25 * np.nanmedian(np.array([r[3] for r in raw if r[3]]) * 4)] = np.nan
        good = ~np.isnan(v)
        v = np.interp(ts, ts[good], v[good])
        v = np.convolve(np.pad(v, 3, mode="edge"), np.ones(7) / 7, mode="valid")
        cols.append(v)
    for j, tt in enumerate(ts):
        out.append({"t_ms": int(tt), "cx": round(float(cols[0][j]), 1), "cy": round(float(cols[1][j]), 1),
                    "h": round(float(cols[2][j]), 1), "detecte": bool(ok[j])})
    cache.write_text(json.dumps(out), encoding="utf-8")
    return out


def at(track, t_ms):
    """Position du visage interpolée à l'instant t_ms."""
    ts = [p["t_ms"] for p in track]
    return {k: float(np.interp(t_ms, ts, [p[k] for p in track])) for k in ("cx", "cy", "h")}
