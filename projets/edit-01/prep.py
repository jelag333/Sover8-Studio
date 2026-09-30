"""Préparation des plans de l'edit (v2) : ralenti fluide façon Twixtor + courbe de vitesse (velocity).

Pour chaque plan : interpolation par flux optique à 120 i/s (ffmpeg minterpolate), puis remappage temporel avec
une courbe de vitesse « velocity edit » (rapide près des coupes, ralenti au centre), sortie 60 i/s. Chaque image
de sortie est unique : c'est ce qui rend l'edit « smooth » (les clips 24 i/s répétaient chaque image 2 à 3 fois)."""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI))
from edit import CHOIX, CLIPS, DEMI, ROLES, TOTAL  # noqa: E402

OUT = ICI / "plans"
OUT.mkdir(exist_ok=True)
INTERP = 120
FPS = 60
W, H = 1080, 1920

# vitesse relative par rôle : (au centre, aux bords). Le gros plan et le rire sont les plus ralentis.
VITESSE = {"lunettes": (0.55, 1.5), "profil": (0.5, 1.4), "gros-plan": (0.45, 1.3), "rire": (0.5, 1.6),
           "bras": (0.5, 1.6), "marche": (0.6, 1.3)}


def courbe(n, vmin, vmax):
    """Vitesse image par image (n images) : cloche inversée, lisse ; renvoie les positions source cumulées (s)."""
    u = (np.arange(n) + 0.5) / n
    v = vmin + (vmax - vmin) * np.abs(2 * u - 1) ** 2.2
    return np.concatenate([[0.0], np.cumsum(v / FPS)])[:n]


def plans():
    out = []
    for k in range(2):
        for i, (t, role) in enumerate(ROLES):
            debut = round(k * DEMI + t)
            fin = round(k * DEMI + ROLES[i + 1][0]) if i + 1 < len(ROLES) else round((k + 1) * DEMI)
            fin = min(fin, TOTAL)
            clip, src = CHOIX[k][role]
            out.append({"n": len(out), "debut": debut, "fin": fin, "clip": clip, "src": src, "role": role})
    return out


def prepare(p):
    n = round((p["fin"] - p["debut"]) * FPS / 1000) + 2        # +2 images de marge
    vmin, vmax = VITESSE[p["role"]]
    pos = courbe(n, vmin, vmax)
    longueur = pos[-1] + 0.1
    dst = OUT / f"plan{p['n']:02d}.mp4"
    if dst.exists():
        return dst
    tmp = OUT / f"_interp{p['n']:02d}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{p['src']:.3f}", "-t", f"{longueur + 0.15:.3f}", "-i", CLIPS[p["clip"]],
                    "-an", "-vf", f"scale={W}:{H}:flags=lanczos,minterpolate=fps={INTERP}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", str(tmp)], check=True)
    # lecture des images interpolées puis remappage selon la courbe de vitesse
    idx = np.round(pos * INTERP).astype(int)                    # croissant : lecture en flux, sans tout charger
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(tmp), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-g", "10",
                            "-pix_fmt", "yuv420p", str(dst)], stdin=subprocess.PIPE)
    taille = W * H * 3
    cur, img = -1, None
    for i in idx:
        while cur < i:
            b = dec.stdout.read(taille)
            if len(b) < taille:
                break
            img, cur = b, cur + 1
        enc.stdin.write(img)
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    tmp.unlink()
    return dst


if __name__ == "__main__":
    ps = plans()
    with ThreadPoolExecutor(3) as ex:
        for d in ex.map(prepare, ps):
            print("ok", d.name)
    (OUT / "plans.json").write_text(json.dumps(ps, indent=1), encoding="utf-8")
