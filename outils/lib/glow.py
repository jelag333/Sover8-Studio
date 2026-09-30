"""Lueur façon « Deep Glow » (After Effects) pré-calculée pour un visuel détouré.

Principe de Deep Glow : plusieurs halos de rayons croissants additionnés avec une décroissance exponentielle,
un cœur lumineux près du bord, une traîne très large et très douce, puis une compression douce (pas de bord dur).
Le résultat est un PNG transparent plus grand que l'objet (marge), centré sur lui, à placer juste derrière.
"""
import hashlib
from pathlib import Path

import numpy as np

from .config import CACHE

VERSION = 2
# rayons en fraction de la plus grande dimension de l'objet, et poids de chaque halo
SIGMAS = (0.018, 0.04, 0.085, 0.16, 0.30)   # rayon élargi (retour utilisateur)
POIDS = (0.7, 0.7, 0.55, 0.42, 0.3)        # plus de poids dans les halos larges : pas de liseré
MARGE = 0.75


def _blur(a, sigma):
    import cv2
    if sigma < 24:
        return cv2.GaussianBlur(a, (0, 0), sigma)
    k = max(1, int(sigma // 12))  # grands rayons : calcul en basse résolution (identique à l'œil, bien plus rapide)
    small = cv2.resize(a, (a.shape[1] // k, a.shape[0] // k), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / k)
    return cv2.resize(small, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_CUBIC)


def soft_shadow(src, flou=0.035):
    """Ombre portée diffuse (sans couleur) : silhouette noire floutée, à placer décalée sous l'objet.
    Renvoie (chemin_png, marge_px)."""
    import cv2
    src = Path(src)
    key = hashlib.sha1(f"ombre{src.read_bytes()[:4096]}{src.stat().st_size}{flou}{VERSION}".encode()).hexdigest()[:14]
    out = CACHE / "glow" / f"{src.stem}-ombre-{key}.png"
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    md = max(h, w)
    pad = int(0.15 * md)
    if out.exists():
        return out, pad
    out.parent.mkdir(parents=True, exist_ok=True)
    a = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    a[pad:pad + h, pad:pad + w] = im[:, :, 3].astype(np.float32) / 255
    alpha = _blur(a, flou * md)
    res = np.dstack([np.zeros(a.shape + (3,), np.uint8), np.clip(alpha * 255, 0, 255).astype(np.uint8)])
    cv2.imwrite(str(out), res)
    return out, pad


def reflet_images(src, n=15, largeur=0.16, intensite=0.8):
    """Light sweep : n images d'une bande de lumière diagonale qui traverse l'objet, découpées à SA forme (alpha
    de l'objet × bande). Affichées une par image par-dessus l'objet, elles donnent un reflet qui balaie la surface."""
    import cv2
    src = Path(src)
    key = hashlib.sha1(f"reflet{src.read_bytes()[:4096]}{src.stat().st_size}{n}{largeur}{intensite}".encode()).hexdigest()[:12]
    base = CACHE / "reflet" / f"{src.stem}-{key}"
    outs = [base.with_name(f"{base.name}-{k:02d}.png") for k in range(n)]
    if all(o.exists() for o in outs):
        return outs
    base.parent.mkdir(parents=True, exist_ok=True)
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    a = im[:, :, 3].astype(np.float32) / 255 if im.shape[2] == 4 else np.ones((h, w), np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    diag = (xx / w + 0.45 * yy / h) / 1.45                        # 0 (haut gauche) -> 1 (bas droite)
    for k, o in enumerate(outs):
        c = -0.25 + 1.5 * k / (n - 1)                              # la bande entre et sort complètement
        band = np.exp(-((diag - c) / (largeur / 2)) ** 2) + 0.35 * np.exp(-((diag - c + 0.09) / (largeur / 5)) ** 2)
        alpha = np.clip(a * band * intensite, 0, 1)
        res = np.dstack([np.full((h, w, 3), 255, np.uint8), (alpha * 255).astype(np.uint8)])
        cv2.imwrite(str(o), res)
    return outs


def deep_glow(src, couleur="#FFC21A", intensite=1.0, rayon=1.0):
    """Renvoie (chemin_png, marge_px) ; mis en cache selon l'image, la couleur, l'intensité et le rayon
    (rayon < 1 : lueur plus serrée, « petit glow »)."""
    import cv2
    src = Path(src)
    key = hashlib.sha1(f"{src.read_bytes()[:4096]}{src.stat().st_size}{couleur}{intensite}{rayon}{VERSION}".encode()).hexdigest()[:14]
    out = CACHE / "glow" / f"{src.stem}-{key}.png"
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    md = max(h, w) * rayon
    pad = int(MARGE * md)
    if out.exists():
        return out, pad
    out.parent.mkdir(parents=True, exist_ok=True)
    a = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    a[pad:pad + h, pad:pad + w] = im[:, :, 3].astype(np.float32) / 255
    total = np.zeros_like(a)
    for s, p in zip(SIGMAS, POIDS):
        total += p * _blur(a, s * md)
    total /= sum(POIDS)
    alpha = 1 - np.exp(-2.6 * intensite * total)          # compression douce : jamais de bord dur
    core = _blur(a, SIGMAS[0] * md)                        # cœur lumineux près du bord de l'objet
    hexa = couleur.lstrip("#")
    tint = np.array([int(hexa[i:i + 2], 16) for i in (4, 2, 0)], np.float32)  # BGR
    rgb = tint[None, None, :] * (1 - 0.12 * core[..., None]) + 255 * 0.12 * core[..., None]  # cœur à peine éclairci
    res = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    cv2.imwrite(str(out), res)
    return out, pad
