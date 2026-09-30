"""Analyse profonde de la référence, image par image (60 i/s) :
- miroir : l'image ressemble-t-elle plus à la précédente, ou à la précédente retournée horizontalement ?
- mouvement 2D image->image (points ORB + transformation similitude) : zoom, décalage x/y, rotation ;
- netteté, saturation, luminosité.
Sortie : mesures.json + graphique.png (courbes empilées)."""
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = r"C:\Users\mtzti\Downloads\transfer-01a0e3e7\référence edit\01_tyyvixedit_7667810913499548935.mp4"
cap = cv2.VideoCapture(R)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(cv2.resize(f, (360, 360)))
n = len(frames)
orb = cv2.ORB_create(1500)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def gray(f):
    return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)


def sim(a, b):
    a = cv2.resize(a, (90, 90)).astype(np.float32); b = cv2.resize(b, (90, 90)).astype(np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6); b = (b - b.mean()) / (b.std() + 1e-6)
    return float((a * b).mean())


rows = []
for i in range(n):
    g = gray(frames[i])
    hsv = cv2.cvtColor(frames[i], cv2.COLOR_BGR2HSV)
    r = {"i": i, "t": i / 60, "lum": float(g.mean()), "sat": float(hsv[..., 1].mean()),
         "net": float(cv2.Laplacian(g, cv2.CV_64F).var())}
    if i:
        p = gray(frames[i - 1])
        r["sim"] = sim(p, g)
        r["sim_miroir"] = sim(cv2.flip(p, 1), g)
        # mouvement image précédente -> image courante
        k1, d1 = orb.detectAndCompute(p, None); k2, d2 = orb.detectAndCompute(g, None)
        r.update(zoom=1.0, dx=0.0, dy=0.0, rot=0.0, ok=0)
        if d1 is not None and d2 is not None and len(k1) > 20 and len(k2) > 20:
            m = sorted(bf.match(d1, d2), key=lambda x: x.distance)[:400]
            if len(m) > 15:
                a = np.float32([k1[x.queryIdx].pt for x in m]); b = np.float32([k2[x.trainIdx].pt for x in m])
                M, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=3)
                if M is not None and inl is not None and inl.sum() > 12:
                    s = float(np.hypot(M[0, 0], M[1, 0]))
                    r.update(zoom=s, dx=float(M[0, 2] + (s - 1) * 0) , dy=float(M[1, 2]),
                             rot=float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))), ok=int(inl.sum()))
    rows.append(r)
json.dump(rows, open("mesures.json", "w"), indent=0)

# --- graphique : une courbe par mesure, 3 lignes de temps (0-3.6 s, 3.6-7.2, 7.2-10.8)
W, Hc = 2400, 190
series = [("lum", 0, 200, (230, 230, 230)), ("sat", 0, 140, (255, 170, 60)), ("net", 0, 700, (120, 200, 255)),
          ("sim", -1, 1, (140, 255, 140)), ("sim_miroir", -1, 1, (255, 90, 200)), ("zoom", 0.9, 1.1, (255, 255, 90)),
          ("dx", -40, 40, (90, 255, 255)), ("dy", -40, 40, (255, 120, 120)), ("rot", -4, 4, (200, 150, 255))]
per = 216  # images par ligne (3,6 s)
img = Image.new("RGB", (W, Hc * len(series) * 0 + 3 * (len(series) * 60 + 40)), (18, 18, 22))
d = ImageDraw.Draw(img)
f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)
for ligne in range(3):
    y0 = ligne * (len(series) * 60 + 40) + 20
    for s_i, (key, lo, hi, col) in enumerate(series):
        yb = y0 + s_i * 60
        d.line((60, yb + 50, W - 10, yb + 50), fill=(50, 50, 60))
        d.text((4, yb + 20), key, font=f, fill=col)
        pts = []
        for j in range(per):
            i = ligne * per + j
            if i >= n or key not in rows[i]:
                continue
            v = (rows[i][key] - lo) / (hi - lo)
            pts.append((60 + j * (W - 70) / per, yb + 50 - 48 * max(0, min(1, v))))
        if len(pts) > 1:
            d.line(pts, fill=col, width=2)
    for j in range(0, per + 1, 6):            # graduation tous les 0,1 s
        x = 60 + j * (W - 70) / per
        t = (ligne * per + j) / 60
        d.line((x, y0, x, y0 + len(series) * 60), fill=(45, 45, 55) if j % 30 else (90, 90, 110))
        if j % 30 == 0:
            d.text((x + 2, y0 - 18), f"{t:.1f}s", font=f, fill=(200, 200, 200))
img.save("graphique.png")
print("images", n)
