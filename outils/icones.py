"""Fabrique d'icônes pour l'habillage (stickers) : emoji couleur de Windows (Segoe UI Emoji, vectoriel) rendus
en PNG détourés haute définition, et cartes dessinées (calendrier, code-barres, coupon).

    python outils/icones.py emoji <nom-fichier> <emoji> [--taille 600]
    python outils/icones.py calendrier <nom-fichier> <jour> <MOIS>
    python outils/icones.py code-barres <nom-fichier> [texte]
    python outils/icones.py coupon <nom-fichier> <texte> [--couleur #F0443A] [--legende COUPON]
    python outils/icones.py photo <nom-fichier> <image> [--rayon 0.045] [--recadre x0 y0 x1 y1]
        (photos / logos du web : coins légèrement arrondis, jamais de bords bruts ; sans watermark, bonne définition)

Les PNG sont écrits dans A-AJOUTER/images ; « studio ajouter » les installe ensuite dans la bibliothèque."""
import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SORTIE = ROOT / "A-AJOUTER" / "images"
EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"
POL = ROOT / "bibliotheque" / "polices"
SS = 2  # sur-échantillonnage pour des bords propres


def police(nom, taille):
    return ImageFont.truetype(str(POL / f"{nom}.ttf"), int(taille * SS))


def fin(im, nom, marge=12):
    """Réduit (anti-crénelage), détoure au plus juste et enregistre."""
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    bb = im.getchannel("A").getbbox()
    im = im.crop(bb)
    out = Image.new("RGBA", (im.width + 2 * marge, im.height + 2 * marge), (0, 0, 0, 0))
    out.paste(im, (marge, marge))
    SORTIE.mkdir(parents=True, exist_ok=True)
    p = SORTIE / f"{nom}.png"
    out.save(p)
    print(p)
    return p


def emoji(nom, car, taille=600):
    f = ImageFont.truetype(EMOJI, int(taille * SS * 0.8))
    im = Image.new("RGBA", (int(taille * SS * 1.4), int(taille * SS * 1.4)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((taille * SS * 0.1, taille * SS * 0.1), car, font=f, embedded_color=True)
    return fin(im, nom)


def calendrier(nom, jour, mois):
    W, H, r = 520 * SS, 560 * SS, 70 * SS
    im = Image.new("RGBA", (W + 40 * SS, H + 80 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 20 * SS, 60 * SS
    d.rounded_rectangle((x0, y0, x0 + W, y0 + H), r, fill="#FFFFFF", outline="#D9D9DE", width=6 * SS)
    band = 160 * SS
    d.rounded_rectangle((x0, y0, x0 + W, y0 + band), r, fill="#F0443A")
    d.rectangle((x0, y0 + band - r, x0 + W, y0 + band), fill="#F0443A")
    for bx in (x0 + W * 0.28, x0 + W * 0.72):  # anneaux
        d.rounded_rectangle((bx - 22 * SS, y0 - 50 * SS, bx + 22 * SS, y0 + 40 * SS), 22 * SS, fill="#3A3A44")
    fm = police("poppins-bold", 66)
    d.text((x0 + W / 2, y0 + band / 2 + 4 * SS), mois, font=fm, fill="#FFFFFF", anchor="mm")
    fj, fe = police("poppins-black", 250), police("poppins-black", 92)
    jw = d.textlength(jour, font=fj)
    if jw > W * 0.84:                      # « 25-27 » : le chiffre se réduit pour tenir dans la page
        fj = police("poppins-black", 250 * W * 0.84 / jw)
        jw = d.textlength(jour, font=fj)
    ew = d.textlength("er", font=fe) if jour == "1" else 0
    cx = x0 + (W - jw - ew) / 2
    cy = y0 + band + (H - band) / 2 + 18 * SS
    d.text((cx, cy), jour, font=fj, fill="#26262C", anchor="lm")
    if ew:
        d.text((cx + jw + 4 * SS, cy - 70 * SS), "er", font=fe, fill="#26262C", anchor="lm")
    return fin(im, nom)


def code_barres(nom, texte="ID PRODUIT"):
    W, H, r = 620 * SS, 380 * SS, 48 * SS
    im = Image.new("RGBA", (W + 40 * SS, H + 40 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 20 * SS, 20 * SS
    d.rounded_rectangle((x0, y0, x0 + W, y0 + H), r, fill="#FFFFFF", outline="#D9D9DE", width=6 * SS)
    ft = police("poppins-black", 50)
    d.text((x0 + W / 2, y0 + 62 * SS), texte, font=ft, fill="#26262C", anchor="mm")
    rnd = random.Random(7)
    bx, bx1, by0, by1 = x0 + 60 * SS, x0 + W - 60 * SS, y0 + 115 * SS, y0 + H - 85 * SS
    x = bx
    while x < bx1:
        w = rnd.choice((4, 4, 6, 8, 12)) * SS
        if x + w > bx1:
            break
        d.rectangle((x, by0, x + w, by1), fill="#111114")
        x += w + rnd.choice((4, 6, 8, 10)) * SS
    fd = police("poppins-bold", 34)
    d.text((x0 + W / 2, y0 + H - 45 * SS), "3 760248 519036", font=fd, fill="#26262C", anchor="mm")
    return fin(im, nom)


def interdit(nom):
    """Panneau « interdit » : anneau rouge + barre, centre transparent (se pose sur un objet)."""
    D, e = 600 * SS, 64 * SS
    im = Image.new("RGBA", (D + 20 * SS, D + 20 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    o = 10 * SS
    d.ellipse((o, o, o + D, o + D), outline="#F23A30", width=e)
    import math
    r = D / 2 - e / 2
    c = o + D / 2
    a = math.radians(45)
    d.line((c - r * math.cos(a), c - r * math.sin(a), c + r * math.cos(a), c + r * math.sin(a)), fill="#F23A30", width=e)
    return fin(im, nom)


def coupon(nom, texte, couleur="#F0443A", legende="COUPON"):
    W, H, r = 640 * SS, 330 * SS, 44 * SS
    im = Image.new("RGBA", (W + 40 * SS, H + 40 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 20 * SS, 20 * SS
    d.rounded_rectangle((x0, y0, x0 + W, y0 + H), r, fill=couleur)
    nr = 44 * SS  # encoches de ticket
    for cx in (x0, x0 + W):
        d.ellipse((cx - nr, y0 + H / 2 - nr, cx + nr, y0 + H / 2 + nr), fill=(0, 0, 0, 0))
    lx = x0 + W * 0.26  # pointillés
    for yy in range(int(y0 + 34 * SS), int(y0 + H - 34 * SS), int(30 * SS)):
        d.rounded_rectangle((lx - 5 * SS, yy, lx + 5 * SS, yy + 16 * SS), 5 * SS, fill=(255, 255, 255, 150))
    fl = police("poppins-bold", 40)
    talon = "%" if "%" in texte else "$" if "$" in texte else "€" if "€" in texte else "+"
    d.text((x0 + W * 0.13, y0 + H / 2), talon, font=police("poppins-black", 84), fill=(255, 255, 255, 235), anchor="mm")
    ft = police("poppins-black", 130)
    tw = d.textlength(texte, font=ft)
    zone = W * 0.54
    if tw > zone:
        ft = police("poppins-black", 130 * zone / tw)
    d.text((x0 + W * 0.61, y0 + H / 2 - 22 * SS), texte, font=ft, fill="#FFFFFF", anchor="mm")
    d.text((x0 + W * 0.61, y0 + H - 58 * SS), legende, font=fl, fill=(255, 255, 255, 220), anchor="mm")
    return fin(im, nom)


def tampon(nom, texte, couleur="#E0241B", rotation=-11):
    """Tampon encreur (« BLOQUÉ », « VALIDÉ »…) : double cadre, encre irrégulière, légèrement penché."""
    ft = police("poppins-black", 150)
    tmp = Image.new("RGBA", (10, 10))
    tw = ImageDraw.Draw(tmp).textlength(texte, font=ft)
    W, H = int(tw + 150 * SS), int(260 * SS)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8 * SS, 8 * SS, W - 8 * SS, H - 8 * SS), 34 * SS, outline=couleur, width=16 * SS)
    d.rounded_rectangle((34 * SS, 34 * SS, W - 34 * SS, H - 34 * SS), 20 * SS, outline=couleur, width=6 * SS)
    d.text((W / 2, H / 2 + 6 * SS), texte, font=ft, fill=couleur, anchor="mm")
    rnd = np.random.default_rng(3)  # encre usée : petits manques aléatoires
    a = np.array(im.getchannel("A")).astype(np.float32)
    bruit = rnd.random((H // (6 * SS) + 1, W // (6 * SS) + 1))
    bruit = np.array(Image.fromarray((bruit * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)) / 255
    a *= np.clip(0.55 + bruit * 0.9, 0, 1) * np.where(rnd.random((H, W)) < 0.015, 0, 1)
    im.putalpha(Image.fromarray(np.clip(a * 0.92, 0, 255).astype(np.uint8)))
    im = im.rotate(rotation, resample=Image.BICUBIC, expand=True)
    return fin(im, nom)


def bouton(nom, texte, fond="#FFFFFF", encre="#111114"):
    """Bouton / pastille façon interface (ex. « LIEN EN BIO ») avec une icône de lien dessinée."""
    ft = police("poppins-black", 78)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = tmp.textlength(texte, font=ft)
    H = 150 * SS
    W = int(tw + H * 1.55 + 70 * SS)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), H // 2, fill=fond)
    cx, cy, r = H * 0.62, H / 2, H * 0.36                      # pastille de l'icône
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=encre)
    for dx in (-1, 1):                                          # deux maillons de chaîne penchés
        mx, my = cx + dx * r * 0.28, cy - dx * r * 0.28
        lw, lh = r * 0.95, r * 0.48
        maillon = Image.new("RGBA", (int(lw * 2), int(lw * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(maillon).rounded_rectangle((lw - lw / 2, lw - lh / 2, lw + lw / 2, lw + lh / 2), lh / 2,
                                                  outline=fond, width=int(9 * SS))
        maillon = maillon.rotate(45, resample=Image.BICUBIC)
        im.alpha_composite(maillon, (int(mx - lw), int(my - lw)))
    d.text((cx + r + 34 * SS, cy + 4 * SS), texte, font=ft, fill=encre, anchor="lm")
    return fin(im, nom)


def etiquette_produit(nom, texte="ID PRODUIT"):
    """Étiquette de vêtement en kraft (trou + ficelle) avec code-barres : l'« identifiant produit »."""
    W, H = 520 * SS, 780 * SS
    im = Image.new("RGBA", (W + 60 * SS, H + 200 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 30 * SS, 170 * SS
    c = 90 * SS  # coins coupés en haut
    d.polygon([(x0 + c, y0), (x0 + W - c, y0), (x0 + W, y0 + c), (x0 + W, y0 + H), (x0, y0 + H), (x0, y0 + c)], fill="#D9B98C")
    d.rounded_rectangle((x0 + 26 * SS, y0 + 150 * SS, x0 + W - 26 * SS, y0 + H - 26 * SS), 26 * SS, fill="#FFFFFF")
    hx, hy = x0 + W / 2, y0 + 70 * SS
    d.ellipse((hx - 28 * SS, hy - 28 * SS, hx + 28 * SS, hy + 28 * SS), fill=(0, 0, 0, 0), outline="#B08D5E", width=8 * SS)
    d.line((hx, hy - 20 * SS, hx - 120 * SS, 10 * SS), fill="#8A6A45", width=7 * SS)       # ficelle
    ft = police("poppins-black", 62)
    d.text((x0 + W / 2, y0 + 245 * SS), texte, font=ft, fill="#1A1A1E", anchor="mm")
    fs = police("poppins-bold", 34)
    d.text((x0 + W / 2, y0 + 320 * SS), "SWEAT · TAILLE M", font=fs, fill="#6A6A72", anchor="mm")
    rnd = random.Random(11)
    bx, bx1, by0, by1 = x0 + 70 * SS, x0 + W - 70 * SS, y0 + 400 * SS, y0 + 620 * SS
    x = bx
    while x < bx1:
        w = rnd.choice((4, 4, 6, 8, 12)) * SS
        if x + w > bx1:
            break
        d.rectangle((x, by0, x + w, by1), fill="#111114")
        x += w + rnd.choice((4, 6, 8, 10)) * SS
    d.text((x0 + W / 2, y0 + 672 * SS), "3 760248 519036", font=police("poppins-bold", 34), fill="#26262C", anchor="mm")
    return fin(im, nom)


def laser(nom, longueur=640, couleur=(255, 40, 40)):
    """Rayon de lecteur code-barres : trait rouge vif avec halo."""
    W, H = (longueur + 80) * SS, 90 * SS
    a = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    bord = np.clip(np.minimum(xx - 40 * SS, W - 40 * SS - xx) / (60 * SS), 0, 1)
    a = np.exp(-((yy - H / 2) / (4 * SS)) ** 2) + 0.45 * np.exp(-((yy - H / 2) / (16 * SS)) ** 2)
    a = np.clip(a * bord, 0, 1)
    rgb = np.zeros((H, W, 3), np.float32) + np.array(couleur, np.float32)
    coeur = np.exp(-((yy - H / 2) / (2 * SS)) ** 2)[..., None]
    rgb = rgb * (1 - 0.6 * coeur) + 255 * 0.6 * coeur
    im = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), "RGBA")
    return fin(im, nom, marge=4)


def telephone(nom, image, legende="", likes="12,4K"):
    """Maquette de téléphone affichant une image (ex. une prise du créateur) avec une interface de vidéo courte
    générique (cœur, commentaires, partage, légende) — sans logo de marque."""
    W, H, b = 560 * SS, 1100 * SS, 20 * SS
    im = Image.new("RGBA", (W + 40 * SS, H + 40 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 20 * SS, 20 * SS
    d.rounded_rectangle((x0, y0, x0 + W, y0 + H), 86 * SS, fill="#111114")
    sw, sh = W - 2 * b, H - 2 * b
    ecran = Image.open(image).convert("RGB")
    r = max(sw / ecran.width, sh / ecran.height)
    ecran = ecran.resize((int(ecran.width * r) + 1, int(ecran.height * r) + 1), Image.LANCZOS)
    ecran = ecran.crop(((ecran.width - sw) // 2, (ecran.height - sh) // 2, (ecran.width - sw) // 2 + sw, (ecran.height - sh) // 2 + sh))
    ecran = ecran.convert("RGBA")
    grad = np.zeros((sh, sw), np.float32)                        # dégradé sombre en bas (lisibilité)
    grad[:] = np.clip((np.arange(sh)[:, None] - sh * 0.62) / (sh * 0.38), 0, 1) * 0.7
    ombre = Image.fromarray((grad * 255).astype(np.uint8))
    ecran.alpha_composite(Image.merge("RGBA", (Image.new("L", (sw, sh), 0),) * 3 + (ombre,)))
    masque = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, sw - 1, sh - 1), 68 * SS, fill=255)
    im.paste(ecran, (x0 + b, y0 + b), masque)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0 + W / 2 - 70 * SS, y0 + b + 18 * SS, x0 + W / 2 + 70 * SS, y0 + b + 58 * SS), 20 * SS, fill="#000000")
    ix = x0 + W - b - 62 * SS                                    # colonne d'icônes à droite
    fc = police("poppins-bold", 26)
    for k, (forme, txt) in enumerate((("coeur", likes), ("bulle", "842"), ("fleche", "1 203"))):
        cy = y0 + H * 0.52 + k * 130 * SS
        s = 30 * SS
        if forme == "coeur":
            d.ellipse((ix - s, cy - s * 0.9, ix, cy + s * 0.1), fill="#FF2D55")
            d.ellipse((ix, cy - s * 0.9, ix + s, cy + s * 0.1), fill="#FF2D55")
            d.polygon([(ix - s * 0.97, cy - s * 0.25), (ix + s * 0.97, cy - s * 0.25), (ix, cy + s * 0.95)], fill="#FF2D55")
        elif forme == "bulle":
            d.ellipse((ix - s, cy - s * 0.85, ix + s, cy + s * 0.75), fill="#FFFFFF")
            d.polygon([(ix - s * 0.5, cy + s * 0.4), (ix - s * 0.9, cy + s * 1.0), (ix - s * 0.05, cy + s * 0.6)], fill="#FFFFFF")
        else:
            d.polygon([(ix - s, cy + s * 0.6), (ix + s, cy - s * 0.1), (ix - s * 0.2, cy - s * 0.9), (ix - s * 0.2, cy - s * 0.45),
                       (ix - s * 0.9, cy - s * 0.2)], fill="#FFFFFF")
        d.text((ix, cy + s * 1.55), txt, font=fc, fill="#FFFFFF", anchor="mm")
    if legende:
        fl = police("poppins-black", 40 if len(legende) <= 20 else 33)
        d.text((x0 + b + 34 * SS, y0 + H - b - 150 * SS), "@actu.rep", font=police("poppins-bold", 30), fill="#FFFFFF", anchor="lm")
        d.text((x0 + b + 34 * SS, y0 + H - b - 96 * SS), legende, font=fl, fill="#FFFFFF", anchor="lm")
    return fin(im, nom)


def carte_logo(nom, src, W=600, H=400, fond="#FFFFFF"):
    """Logo (de marque, d'agent…) centré dans une carte blanche arrondie de taille fixe : grilles homogènes."""
    W, H = W * SS, H * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, W - 1, H - 1), int(H * 0.12), fill=fond)
    lg = Image.open(src).convert("RGBA")
    bb = lg.getbbox()
    lg = lg.crop(bb) if bb else lg
    r = min(W * 0.78 / lg.width, H * 0.70 / lg.height)
    lg = lg.resize((int(lg.width * r), int(lg.height * r)), Image.LANCZOS)
    im.alpha_composite(lg, ((W - lg.width) // 2, (H - lg.height) // 2))
    return fin(im, nom)


def pastille(nom, texte, style="normal"):
    """Pastille de texte : normal (blanche), fort (orange, mise en avant), barre (blanche, barrée d'un trait rouge)."""
    ft = police("poppins-black", 80)
    tw = ImageDraw.Draw(Image.new("RGBA", (10, 10))).textlength(texte, font=ft)
    H = 150 * SS
    W = int(tw + 110 * SS)
    im = Image.new("RGBA", (W + 40 * SS, H + 40 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fond, encre = {"fort": ("#FF7A1A", "#FFFFFF"), "ok": ("#12A150", "#FFFFFF"),
                   "froid": ("#DDF1FF", "#1F5FD6")}.get(style, ("#FFFFFF", "#15151A"))
    if style == "ok":                        # coche dessinée à gauche du texte
        W += int(H * 0.8)
        im = Image.new("RGBA", (W + 40 * SS, H + 40 * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
    d.rounded_rectangle((20 * SS, 20 * SS, 20 * SS + W, 20 * SS + H), H // 2, fill=fond)
    if style == "ok":
        cx, cy, r = 20 * SS + H * 0.62, 20 * SS + H / 2, H * 0.3
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#FFFFFF")
        d.line([(cx - r * 0.5, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.42), (cx + r * 0.55, cy - r * 0.38)],
               fill=fond, width=int(r * 0.32), joint="curve")
        d.text((20 * SS + H * 1.05 + (W - H * 1.05) / 2, 20 * SS + H / 2 + 4 * SS), texte, font=ft, fill=encre, anchor="mm")
    else:
        d.text((20 * SS + W / 2, 20 * SS + H / 2 + 4 * SS), texte, font=ft, fill=encre, anchor="mm")
    if style == "barre":
        d.line((6 * SS, 20 * SS + H * 0.78, W + 34 * SS, 20 * SS + H * 0.22), fill="#E0241B", width=16 * SS)
    return fin(im, nom)


def bandeau_info(nom, titre, etiquette="FLASH INFO"):
    """Bandeau façon chaîne d'info : pastille rouge + barre blanche avec le titre."""
    fe, ft = police("poppins-black", 54), police("poppins-black", 64)
    dd = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    we, wt = dd.textlength(etiquette, font=fe) + 70 * SS, dd.textlength(titre, font=ft) + 80 * SS
    H = 130 * SS
    im = Image.new("RGBA", (int(we + wt), int(H + 70 * SS)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 70 * SS, we + wt, 70 * SS + H), 26 * SS, fill="#FFFFFF")
    d.rounded_rectangle((0, 0, we, 88 * SS), 22 * SS, fill="#E0241B")
    d.text((we / 2, 44 * SS), etiquette, font=fe, fill="#FFFFFF", anchor="mm")
    d.text((40 * SS, 70 * SS + H / 2 + 4 * SS), titre, font=ft, fill="#15151A", anchor="lm")
    return fin(im, nom)


def carte_mystere(nom, legende="PROCHAINE MARQUE ?"):
    """Carte « mystère » : grand point d'interrogation (qui sera la prochaine ?)."""
    W, H = 520 * SS, 560 * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 60 * SS, fill="#1B1B22")
    d.text((W / 2, H * 0.43), "?", font=police("poppins-black", 330), fill="#FFB11A", anchor="mm")
    d.text((W / 2, H * 0.86), legende, font=police("poppins-black", 42), fill="#FFFFFF", anchor="mm")
    return fin(im, nom)


def graphique_hausse(nom, titre="DIFFICULTÉ"):
    """Carte graphique : courbe qui monte en flèche (« de plus en plus compliqué »)."""
    W, H = 620 * SS, 440 * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 48 * SS, fill="#FFFFFF")
    d.text((44 * SS, 60 * SS), titre, font=police("poppins-black", 50), fill="#15151A", anchor="lm")
    x0, y0, x1, y1 = 60 * SS, 120 * SS, W - 60 * SS, H - 50 * SS
    for k in range(4):
        yy = y0 + (y1 - y0) * k / 3
        d.line((x0, yy, x1, yy), fill="#E6E6EC", width=3 * SS)
    pts = [(0, 0.08), (0.2, 0.12), (0.38, 0.1), (0.55, 0.3), (0.7, 0.42), (0.85, 0.7), (1.0, 0.95)]
    P = [(x0 + (x1 - x0) * u, y1 - (y1 - y0) * v) for u, v in pts]
    d.line(P, fill="#E0241B", width=14 * SS, joint="curve")
    (xa, ya), (xb, yb) = P[-2], P[-1]
    import math
    ang = math.atan2(yb - ya, xb - xa)
    L = 46 * SS
    d.polygon([(xb + 14 * SS * math.cos(ang), yb + 14 * SS * math.sin(ang)),
               (xb - L * math.cos(ang - 0.5), yb - L * math.sin(ang - 0.5)),
               (xb - L * math.cos(ang + 0.5), yb - L * math.sin(ang + 0.5))], fill="#E0241B")
    return fin(im, nom)


def plaque_pnj(nom, titre="PNJ", niveau="Niv. 1", vie=0.35, maxi=False):
    """Plaque de personnage façon jeu vidéo (nom + niveau + barre de vie), à placer au-dessus d'une tête."""
    W, H = 560 * SS, 170 * SS
    im = Image.new("RGBA", (W, H + 40 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bord = "#FFC21A" if maxi else "#FFFFFF"
    d.rounded_rectangle((0, 0, W - 1, H), 30 * SS, fill=(16, 16, 24, 215), outline=bord, width=6 * SS)
    d.polygon([(W / 2 - 26 * SS, H - 2), (W / 2 + 26 * SS, H - 2), (W / 2, H + 34 * SS)], fill=bord)
    d.text((34 * SS, 52 * SS), titre, font=police("poppins-black", 60), fill="#FFFFFF", anchor="lm")
    d.text((W - 34 * SS, 52 * SS), niveau, font=police("poppins-black", 48), fill="#FFC21A" if maxi else "#7CFF6B", anchor="rm")
    x0, y0, x1, y1 = 34 * SS, 102 * SS, W - 34 * SS, 138 * SS
    d.rounded_rectangle((x0, y0, x1, y1), 18 * SS, fill="#3A3A46")
    d.rounded_rectangle((x0, y0, x0 + (x1 - x0) * vie, y1), 18 * SS, fill="#FFC21A" if maxi else "#4CDB5A")
    return fin(im, nom)


def medaille(nom, rang):
    """Médaille de classement (#1 or, #2 argent, #3 bronze) avec rubans."""
    coul = {1: ("#F5C542", "#B8860B"), 2: ("#D9DDE3", "#8C939C"), 3: ("#E0995A", "#9A5B24")}[rang]
    D = 420 * SS
    im = Image.new("RGBA", (D, int(D * 1.25)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for dx, c in ((-1, "#E0241B"), (1, "#1F5FD6")):  # rubans
        d.polygon([(D / 2 + dx * 20 * SS, D * 0.62), (D / 2 + dx * 150 * SS, D * 1.22), (D / 2 + dx * 60 * SS, D * 1.12),
                   (D / 2 + dx * 5 * SS, D * 1.24), (D / 2 - dx * 80 * SS, D * 0.66)], fill=c)
    d.ellipse((20 * SS, 20 * SS, D - 20 * SS, D - 20 * SS), fill=coul[1])
    d.ellipse((50 * SS, 50 * SS, D - 50 * SS, D - 50 * SS), fill=coul[0])
    d.text((D / 2, D / 2 + 8 * SS), f"#{rang}", font=police("poppins-black", 170), fill="#FFFFFF", anchor="mm",
           stroke_width=6 * SS, stroke_fill=coul[1])
    return fin(im, nom)


def bulle_commentaire(nom, pseudo, texte, likes="2 431"):
    """Commentaire façon appli (avatar, pseudo, texte, cœur)."""
    W, H = 760 * SS, 220 * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 44 * SS, fill="#FFFFFF")
    d.ellipse((34 * SS, 44 * SS, 154 * SS, 164 * SS), fill="#FF7A1A")
    d.text((94 * SS, 106 * SS), pseudo[0].upper(), font=police("poppins-black", 64), fill="#FFFFFF", anchor="mm")
    d.text((184 * SS, 72 * SS), pseudo, font=police("poppins-bold", 36), fill="#8A8A94", anchor="lm")
    d.text((184 * SS, 134 * SS), texte, font=police("poppins-black", 50), fill="#15151A", anchor="lm")
    hx, hy, s = W - 70 * SS, 90 * SS, 22 * SS
    d.ellipse((hx - s, hy - s * 0.9, hx, hy + s * 0.1), fill="#FF2D55")
    d.ellipse((hx, hy - s * 0.9, hx + s, hy + s * 0.1), fill="#FF2D55")
    d.polygon([(hx - s * 0.97, hy - s * 0.25), (hx + s * 0.97, hy - s * 0.25), (hx, hy + s * 0.95)], fill="#FF2D55")
    d.text((hx, hy + 52 * SS), likes, font=police("poppins-bold", 26), fill="#8A8A94", anchor="mm")
    return fin(im, nom)


def confettis(nom, n=90, graine=5):
    """Explosion de confettis (rectangles et ronds colorés) autour d'un centre vide."""
    import math
    W = H = 900 * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rnd = random.Random(graine)
    couls = ["#FFC21A", "#FF2D55", "#1F5FD6", "#12A150", "#FF7A1A", "#B45CFF", "#FFFFFF"]
    for _ in range(n):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.28, 0.48) * W
        x, y = W / 2 + r * math.cos(a), H / 2 + r * math.sin(a)
        s = rnd.uniform(14, 30) * SS
        p = Image.new("RGBA", (int(s * 2.4), int(s * 2.4)), (0, 0, 0, 0))
        dp = ImageDraw.Draw(p)
        c = rnd.choice(couls)
        if rnd.random() < 0.6:
            dp.rectangle((s * 0.7, s * 0.95, s * 1.7, s * 1.45), fill=c)
        else:
            dp.ellipse((s * 0.8, s * 0.8, s * 1.6, s * 1.6), fill=c)
        p = p.rotate(rnd.uniform(0, 360), resample=Image.BICUBIC)
        im.alpha_composite(p, (int(x - p.width / 2), int(y - p.height / 2)))
    return fin(im, nom)


def drapeau_chine(nom):
    """Drapeau de la Chine (rouge, 5 étoiles jaunes), coins arrondis."""
    import math
    W, H = 600 * SS, 400 * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 26 * SS, fill="#DE2910")

    def etoile(cx, cy, r, rot=0.0):
        pts = []
        for k in range(10):
            a = rot - math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.382
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill="#FFDE00")
    u = H / 20
    etoile(5 * u, 5 * u, 3 * u)
    for (x, y) in ((10, 2), (12, 4), (12, 7), (10, 9)):
        etoile(x * u, y * u, u, math.atan2(5 - y, 5 - x) + math.pi / 2)
    return fin(im, nom)


def trajet(nom, depart="VENDEUR", arrivee="ENTREPÔT", alerte="+ DÉLAI"):
    """Carte « trajet » : deux étapes reliées par des pointillés, avec une alerte de retard au milieu."""
    W, H = 900 * SS, 360 * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 60 * SS, W - 1, H - 1), 48 * SS, fill="#FFFFFF")
    fe = police("poppins-black", 50)
    cy = 60 * SS + (H - 60 * SS) * 0.62
    for x, t in ((150 * SS, depart), (W - 150 * SS, arrivee)):
        d.ellipse((x - 26 * SS, cy - 26 * SS, x + 26 * SS, cy + 26 * SS), fill="#15151A")
        d.text((x, cy - 70 * SS), t, font=fe, fill="#15151A", anchor="mm")
    for x in range(int(200 * SS), int(W - 200 * SS), int(44 * SS)):
        d.rounded_rectangle((x, cy - 7 * SS, x + 24 * SS, cy + 7 * SS), 7 * SS, fill="#9A9AA6")
    fa = police("poppins-black", 46)
    tw = d.textlength(alerte, font=fa)
    d.rounded_rectangle((W / 2 - tw / 2 - 30 * SS, 0, W / 2 + tw / 2 + 30 * SS, 100 * SS), 50 * SS, fill="#E0241B")
    d.text((W / 2, 52 * SS), alerte, font=fa, fill="#FFFFFF", anchor="mm")
    return fin(im, nom)


def photo(nom, src, rayon=0.045, recadre=None, largeur_max=1400):
    """Photo / logo rectangulaire -> PNG aux coins LÉGÈREMENT arrondis (règle de l'utilisateur : jamais de bords
    bruts). rayon = fraction du petit côté ; recadre = (x0, y0, x1, y1) en fractions pour cadrer le sujet.
    L'ombre portée est ajoutée au montage (add_stickers)."""
    im = Image.open(src).convert("RGBA")
    if recadre:
        x0, y0, x1, y1 = recadre
        im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
    if im.width > largeur_max:
        im = im.resize((largeur_max, round(im.height * largeur_max / im.width)), Image.LANCZOS)
    r = max(6, int(min(im.size) * rayon))
    masque = Image.new("L", (im.width * SS, im.height * SS), 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, im.width * SS - 1, im.height * SS - 1), r * SS, fill=255)
    masque = masque.resize(im.size, Image.LANCZOS)            # bord anti-crénelé
    im.putalpha(Image.fromarray(np.minimum(np.array(im.getchannel("A")), np.array(masque))))
    SORTIE.mkdir(parents=True, exist_ok=True)
    p = SORTIE / f"{nom}.png"
    im.save(p)
    print(p)
    return p


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("emoji"); a.add_argument("nom"); a.add_argument("car"); a.add_argument("--taille", type=int, default=600)
    a = sp.add_parser("calendrier"); a.add_argument("nom"); a.add_argument("jour"); a.add_argument("mois")
    a = sp.add_parser("code-barres"); a.add_argument("nom"); a.add_argument("texte", nargs="?", default="ID PRODUIT")
    a = sp.add_parser("coupon"); a.add_argument("nom"); a.add_argument("texte")
    a.add_argument("--couleur", default="#F0443A"); a.add_argument("--legende", default="COUPON")
    a = sp.add_parser("photo"); a.add_argument("nom"); a.add_argument("src")
    a.add_argument("--rayon", type=float, default=0.045)
    a.add_argument("--recadre", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    g = ap.parse_args()
    if g.cmd == "photo":
        photo(g.nom, g.src, g.rayon, g.recadre)
    elif g.cmd == "emoji":
        emoji(g.nom, g.car, g.taille)
    elif g.cmd == "calendrier":
        calendrier(g.nom, g.jour, g.mois)
    elif g.cmd == "code-barres":
        code_barres(g.nom, g.texte)
    else:
        coupon(g.nom, g.texte, g.couleur, g.legende)


if __name__ == "__main__":
    main()
