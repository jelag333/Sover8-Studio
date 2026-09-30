"""Dérush IMG_2950 : affine les points de coupe de chaque prise retenue sur l'énergie de la voix,
puis écrit plan.json (plans bout à bout, sans habillage)."""
import json, sys, wave
from pathlib import Path
import numpy as np

ICI = Path(__file__).parent
PROXY = (ICI / "rushes" / "img2950-1080.mp4").as_posix()

# (nom, début, fin, pourquoi) en secondes : bornes des zones de parole retenues
PRISES = [
    ("Accroche", 24.06, 25.77, "7e et dernière prise de l'accroche : la plus posée, débit net, aucun accroc."),
    ("TikTok", 51.85, 56.10, "Seule prise complète : les essais 38-47 s s'arrêtent en cours de phrase."),
    ("Identifiant", 150.90, 155.02, "5 prises complètes ; celle-ci est la plus fluide (113 s dit « sur chaque déclaration »)."),
    ("Étiquette", 222.18, 224.67, "Dernière prise, la plus courte et la plus claire (« ce qu'il y a dans ce colis »)."),
    ("Blocage", 262.00, 265.93, "Seule prise complète de la conséquence (colis bloqué à la frontière)."),
    ("Rassure", 276.94, 279.53, "Prise complète d'un seul souffle ; la précédente coupe après « tout de suite »."),
    ("Agents", 304.29, 307.67, "Prise avec la fin « donc ne vous inquiétez pas », qui boucle le message."),
    ("CTA", 338.51, 344.88, "Seule prise complète de l'appel à l'action (lien en bio, -40 %, coupon)."),
]
AVANT, APRES = 0.09, 0.16   # respiration gardée avant / après la parole
HOP = 0.005


def charge(p):
    with wave.open(str(p)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def env_db(x, sr):
    h = int(sr * HOP)
    n = len(x) // h
    r = np.sqrt(np.mean(x[: n * h].reshape(n, h) ** 2, axis=1) + 1e-12)
    r = np.convolve(r, np.ones(4) / 4, mode="same")
    return 20 * np.log10(r + 1e-9)


def main():
    x, sr = charge(ICI / "rushes" / "voix-16k.wav")
    e = env_db(x, sr)
    fond = np.percentile(e, 10)
    seuil = fond + 12
    clips, total = [], 0.0
    for nom, a, b, pourquoi in PRISES:
        ia, ib = int(a / HOP), int(b / HOP)
        # début réel : on recule tant que le signal reste au-dessus du seuil (max 300 ms)
        i = ia
        while i > ia - 60 and e[i - 1] > seuil:
            i -= 1
        j = ib
        while j < ib + 60 and e[j + 1] > seuil:
            j += 1
        d, f = i * HOP - AVANT, j * HOP + APRES
        # ne pas mordre sur une parole voisine : on s'arrête au silence le plus proche
        k = int(d / HOP)
        while k < i and e[k] > seuil:
            k += 1
        d = k * HOP if k < i else d
        k = int(f / HOP)
        while k > j and e[k] > seuil:
            k -= 1
        f = k * HOP if k > j else f
        clips.append({"nom": nom, "fichier": PROXY, "debut_ms": int(round(d * 1000)),
                      "fin_ms": int(round(f * 1000)), "volume": 1.0, "pourquoi": pourquoi})
        total += f - d
        print(f"{nom:12s} {a:7.2f}-{b:7.2f} -> {d:7.3f}-{f:7.3f} ({f-d:4.2f} s)")
    print(f"fond {fond:.1f} dB, seuil {seuil:.1f} dB, total {total:.1f} s")
    plan = {"nom": "derush-img2950", "format": "9:16", "export": {"resolution": "1080p", "fps": 30},
            "_notes": "Dérush pur : une prise par phrase, blancs et ratés retirés, aucun habillage.",
            "clips": clips}
    (ICI / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
