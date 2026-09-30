"""Préparation v3 des plans (analyse profonde de la référence, image par image) :
- ralenti fluide par flux optique (120 i/s) + loi de temps propre à chaque rôle ;
- gros plan : pendant le N&B l'image avance, puis REVERSE (rembobinage en 60 ms) à la reprise de la couleur ;
- profil : image RETOURNÉE EN MIROIR sur les temps (2 fenêtres), avec à chaque bascule 1 image d'interpolation
  par flux optique entre l'image et son miroir (le « smear » de la référence)."""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI))
from edit import CHOIX, CLIPS, DEMI, ROLES, TOTAL  # noqa: E402

OUT = ICI / "plans3"
OUT.mkdir(exist_ok=True)
INTERP, FPS, W, H = 120, 60, 1080, 1920
IMG = 1000 / FPS

VITESSE = {"lunettes": (0.6, 1.3), "profil": (0.55, 1.2), "gros-plan": (0.5, 0.5), "rire": (0.6, 1.3),
           "bras": (0.6, 1.4), "marche": (0.7, 1.2)}
# fenêtres relatives au début de la séquence (ms), relevées sur la référence
MIROIRS = [(1050, 1133), (1250, 1317)]
BASCULES = [1033, 1133, 1233, 1317]
NB_REVERSE = [(1800, 2067, 2130)]           # (début N&B, fin N&B = début du rembobinage, fin du rembobinage)


def plans():
    out = []
    for k in range(2):
        for i, (t, role) in enumerate(ROLES):
            debut = round(k * DEMI + t)
            fin = round(k * DEMI + ROLES[i + 1][0]) if i + 1 < len(ROLES) else round((k + 1) * DEMI)
            clip, src = CHOIX[k][role]
            out.append({"n": len(out), "k": k, "debut": debut, "fin": min(fin, TOTAL), "clip": clip, "src": src, "role": role})
    return out


def loi_temps(p, n):
    """Position source (s, depuis src) de chaque image de sortie."""
    vmin, vmax = VITESSE[p["role"]]
    u = (np.arange(n) + 0.5) / n
    v = vmin + (vmax - vmin) * np.abs(2 * u - 1) ** 2.2
    tau = np.concatenate([[0.0], np.cumsum(v / FPS)])[:n]
    if p["role"] == "gros-plan":             # N&B : l'image avance ; puis REVERSE (retour à l'état d'avant le N&B)
        base, cur, avant, apres = p["k"] * DEMI, 0.0, None, None
        tau = np.zeros(n)
        for i in range(n):
            g = p["debut"] + i * IMG - base
            a, b, c = NB_REVERSE[0]
            if a <= g < b:
                if avant is None:
                    avant = cur
                tau[i] = apres = cur
                cur += 1.1 / FPS                 # le N&B avance plus vite : le rembobinage se voit
            elif b <= g < c and avant is not None:
                x = (g - b) / (c - b)
                tau[i] = apres + (avant - apres) * x * x * (3 - 2 * x)
                cur = avant
            else:
                tau[i] = cur
                cur += vmin / FPS
    return tau


def bascule(img):
    """Image d'interpolation entre l'image et son miroir (flux optique DIS, t = 0,5) : le smear de la référence."""
    a = img
    b = np.ascontiguousarray(img[:, ::-1])
    sa, sb = cv2.resize(a, (270, 480)), cv2.resize(b, (270, 480))
    ga, gb = cv2.cvtColor(sa, cv2.COLOR_RGB2GRAY), cv2.cvtColor(sb, cv2.COLOR_RGB2GRAY)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    fab, fba = dis.calc(ga, gb, None), dis.calc(gb, ga, None)
    fab = cv2.resize(fab, (W, H)) * (W / 270)
    fba = cv2.resize(fba, (W, H)) * (W / 270)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    wa = cv2.remap(a, gx - 0.5 * fab[..., 0], gy - 0.5 * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wb = cv2.remap(b, gx - 0.5 * fba[..., 0], gy - 0.5 * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(wa, 0.5, wb, 0.5, 0)


def prepare(p):
    n = round((p["fin"] - p["debut"]) / IMG) + 2
    tau = loi_temps(p, n)
    dst = OUT / f"plan{p['n']:02d}.mp4"
    lo, hi = float(tau.min()), float(tau.max())
    tmp = OUT / f"_interp{p['n']:02d}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{p['src'] + lo:.3f}", "-t", f"{hi - lo + 0.2:.3f}", "-i", CLIPS[p["clip"]],
                    "-an", "-vf", f"scale={W}:{H}:flags=lanczos,minterpolate=fps={INTERP}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", str(tmp)], check=True)
    idx = np.round((tau - lo) * INTERP).astype(int)
    besoin = set(idx.tolist())
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(tmp), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    taille, stock, j, der = W * H * 3, {}, 0, None
    while j <= max(besoin):
        b = dec.stdout.read(taille)
        if len(b) < taille:
            break
        der = b
        if j in besoin:
            stock[j] = b
        j += 1
    dec.stdout.close()
    dec.wait()
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-g", "10", "-pix_fmt", "yuv420p", str(dst)],
                           stdin=subprocess.PIPE)
    base = p["k"] * DEMI
    for i, ix in enumerate(idx):
        img = np.frombuffer(stock.get(ix, der), np.uint8).reshape(H, W, 3)
        if p["role"] == "profil":
            g = p["debut"] + i * IMG - base
            if any(abs(g - c) < IMG / 2 for c in BASCULES):
                img = bascule(img)
            elif any(a <= g < b for a, b in MIROIRS):
                img = img[:, ::-1]
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
    enc.stdin.close()
    enc.wait()
    tmp.unlink()
    return dst


if __name__ == "__main__":
    ps = plans()
    seul = [int(a) for a in sys.argv[1:]]
    with ThreadPoolExecutor(3) as ex:
        for d in ex.map(prepare, [p for p in ps if not seul or p["n"] in seul]):
            print("ok", d.name, flush=True)
    (OUT / "plans.json").write_text(json.dumps(ps, indent=1), encoding="utf-8")
