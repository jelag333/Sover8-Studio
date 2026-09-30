"""Dérush dynamique IMG_2893 : coupes serrées + J-cuts.

Chaque prise est réduite à sa parole (attaque réelle -> fin réelle). Les phrases s'enchaînent avec un blanc
très court (BLANC) ; les queues et les attaques se chevauchent en fondu croisé dans une piste voix pré-mixée.
La vidéo coupe APRÈS l'arrivée du son de la phrase suivante (J-cut : on entend avant de voir).
Sorties : rushes/voix-dyn.wav (voix du montage), .timeline.json (repères), clips du plan."""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ICI = Path(__file__).parent
PROXY = "C:/Users/mtzti/Downloads/IMG_2893.MOV"   # rush 4K original : les prises retenues sont encodées directement
# colorimétrie douce (appliquée à l'encodage des prises) : légère courbe en S (contraste), vibrance (couleurs
# plus vives sans brûler la peau), saturation +6 %, pointe de chaleur, micro-netteté après la réduction du 4K
ETALO = ("curves=all='0/0 0.25/0.23 0.5/0.5 0.75/0.77 1/1',vibrance=intensity=0.22,"
         "eq=saturation=1.06:gamma=0.99,colorbalance=rm=0.015:bm=-0.015:rh=0.01:bh=-0.01,unsharp=5:5:0.35")
FPS = 30
IMG = 1000 / FPS

PRISES = [
    ("Accroche", 29.85, 32.16),
    ("Top3", 40.38, 45.40, "strict"),  # « On commence par le top 3, c'est la Moncler… finito » d'une traite (2e formulation)
    ("Top2", 109.99, 114.84),
    ("PNJ2", 116.06, 118.18),
    ("Top1", 177.17, 181.06),
    ("Burberry", 223.04, 228.97),
]
PRE, POST = 0.045, 0.110   # son gardé avant l'attaque / après la fin (souffle, résonance)
FONDU_IN, FONDU_OUT = 0.030, 0.080
BLANC = 0.050               # blanc entre la fin d'une phrase et l'attaque de la suivante (50 ms : demande utilisateur)
J = 2 * IMG / 1000          # la vidéo coupe 2 images après l'attaque du son suivant
DEBUT, FIN = 0.040, 0.350   # respiration au tout début / à la toute fin
HOP = 0.005


def lire(p):
    with wave.open(str(p)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def env_db(x, sr):
    h = int(sr * HOP)
    n = len(x) // h
    r = np.sqrt(np.mean(x[: n * h].reshape(n, h) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(r + 1e-9)


def bornes(e, a, b, seuil):
    """Attaque et fin réelles de la parole de la zone [a, b] (s).

    On part de la première / dernière image franchement parlée de la zone (médiane - 12 dB), puis on
    s'étend vers l'extérieur tant que le signal reste au-dessus du seuil (consonnes douces, résonance),
    sans jamais sauter un creux : une autre prise collée juste avant ou après n'est pas reprise."""
    ia, ib = int(a / HOP), int(b / HOP)
    zone = e[ia:ib]
    fort = np.median(zone[zone > np.percentile(zone, 30)]) - 12
    p = int((a - 0.10) / HOP)
    while e[p] < fort:
        p += 1
    lim = p - int(0.25 / HOP)
    while p > lim and e[p - 1] > seuil:
        p -= 1
    q = int((b + 0.10) / HOP)
    while e[q] < fort:
        q -= 1
    lim = q + int(0.30 / HOP)
    while q < lim and e[q + 1] > seuil:
        q += 1
    return p * HOP, (q + 1) * HOP


def main():
    x, sr = lire(ICI / "rushes" / "voix-48k.wav")
    e = env_db(x, sr)
    fond = np.percentile(e, 10)
    seuil = fond + 12
    zones = []
    for n, a, b, *opt in PRISES:  # « strict » : on coupe pile au début donné (pas d'extension vers l'arrière)
        on, off = bornes(e, a, b, seuil)
        zones.append((n, a if "strict" in opt else on, off))

    # placement : attaque(i) = fin(i-1) + BLANC ; t0 = début de la timeline
    pos, t = [], DEBUT
    for i, (n, on, off) in enumerate(zones):
        if i:
            t = pos[-1][2] + BLANC
        pos.append((n, t, t + (off - on)))           # (nom, attaque, fin) sur la timeline
    total = pos[-1][2] + FIN

    # voix pré-mixée : chaque phrase avec fondus, sommée (chevauchement = fondu croisé)
    out = np.zeros(int(total * sr) + sr, np.float32)
    # niveau égal d'une prise à l'autre : chaque prise est ramenée au niveau médian des prises (±6 dB max)
    def niveau(on, off):
        s = x[int(on * sr):int(off * sr)]
        h = int(sr * 0.05)
        r = 20 * np.log10(np.sqrt(np.mean(s[: len(s) // h * h].reshape(-1, h) ** 2, axis=1)) + 1e-9)
        return float(np.median(r[r > r.max() - 25]))
    niv = [niveau(on, off) for _, on, off in zones]
    ref = float(np.median(niv))
    for (n, on, off), (_, ta, tb), nv in zip(zones, pos, niv):
        s0, s1 = on - PRE, off + POST
        g = 10 ** (np.clip(ref - nv, -6, 6) / 20)
        print(f"  niveau {n:10s} {nv:6.1f} dB -> gain {20 * np.log10(g):+.1f} dB")
        seg = x[int(s0 * sr):int(s1 * sr)].copy() * g
        fi, fo = int(FONDU_IN * sr), int(FONDU_OUT * sr)
        seg[:fi] *= np.linspace(0, 1, fi) ** 2
        seg[-fo:] *= np.linspace(1, 0, fo) ** 2
        d = int((ta - PRE) * sr)
        if d < 0:
            seg, d = seg[-d:], 0
        out[d:d + len(seg)] += seg
    out = out[: int(total * sr)]
    brut = ICI / ".tesseract-work" / "voix-dyn-brut.wav"
    brut.parent.mkdir(exist_ok=True)
    with wave.open(str(brut), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    # niveau : voix à -15 LUFS, crêtes < -1.5 dB (la voix du rush était à -23 LUFS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                    "highpass=f=70,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120:makeup=2,"
                    "loudnorm=I=-15:TP=-1.5:LRA=7", "-ar", "48000", "-ac", "1",
                    str(ICI / "rushes" / "voix-dyn.wav")], check=True)

    # vidéo : coupe(i) = attaque(i) + J, calée sur la grille d'images
    grille = lambda s: round(s * 1000 / IMG) * IMG
    coupes = [0.0] + [grille(ta + J) for _, ta, _ in pos[1:]] + [grille(total)]
    clips, reperes = [], []
    for i, ((n, on, off), (_, ta, tb)) in enumerate(zip(zones, pos)):
        dec = ta - on                                  # timeline = source + dec
        m0, m1 = round(coupes[i]), round(coupes[i + 1])
        c0, c1 = m0 / 1000, m1 / 1000
        clips.append({"nom": n, "fichier": PROXY, "debut_ms": round((c0 - dec) * 1000),
                      "fin_ms": round((c0 - dec) * 1000) + (m1 - m0), "volume": 0.0})
        reperes.append({"nom": n, "source_attaque": round(on, 3), "source_fin": round(off, 3),
                        "attaque_ms": round(ta * 1000), "fin_ms": round(tb * 1000),
                        "decalage_ms": round(dec * 1000, 1), "plan_ms": [round(c0 * 1000), round(c1 * 1000)]})
        print(f"{n:12s} source {on:7.3f}-{off:7.3f} | voix {ta:6.3f}-{tb:6.3f} | image {c0:6.3f}-{c1:6.3f}")
    print(f"fond {fond:.1f} dB, seuil {seuil:.1f} dB, total {total:.2f} s")
    (ICI / ".timeline.json").write_text(json.dumps({"total_ms": round(total * 1000), "reperes": reperes},
                                                   ensure_ascii=False, indent=2), encoding="utf-8")
    clips = selects(clips)
    (ICI / ".clips-dyn.json").write_text(json.dumps(clips, ensure_ascii=False, indent=2), encoding="utf-8")


def selects(clips, marge=400):
    """Source courte : seulement les prises utilisées (± marge), en images clés rapprochées.
    Le rendu n'a plus à parcourir un rush de 6 min en 1440p pour chaque plan (export bien plus rapide)."""
    import math
    work = ICI / ".tesseract-work" / "selects"
    work.mkdir(parents=True, exist_ok=True)
    out, liste, off = [], [], 0
    for i, c in enumerate(clips):
        s0 = math.floor(max(0, c["debut_ms"] - marge) / IMG) * IMG
        s1 = math.ceil((c["fin_ms"] + marge) / IMG) * IMG
        seg = work / f"seg{i}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(s0 - IMG / 2) / 1000:.4f}", "-i", PROXY, "-frames:v", str(round((s1 - s0) / IMG)),
                        "-an", "-vf", f"fps={FPS},scale=1440:2560:flags=lanczos,{ETALO}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", "15",
                        "-pix_fmt", "yuv420p", str(seg)], check=True)
        liste.append(f"file '{seg.as_posix()}'")
        d = dict(c)
        d["fichier"] = (ICI / "rushes" / "selects-1440.mp4").as_posix()
        d["debut_ms"] = round(off + c["debut_ms"] - s0)
        d["fin_ms"] = d["debut_ms"] + (c["fin_ms"] - c["debut_ms"])
        d["source_rush_ms"] = [c["debut_ms"], c["fin_ms"]]
        out.append(d)
        off += s1 - s0
    (work / "liste.txt").write_text("\n".join(liste), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "liste.txt"), "-c", "copy",
                    str(ICI / "rushes" / "selects-1440.mp4")], check=True)
    # contrôle image par image : la coupe au milieu d'un rush peut tomber une image trop tôt ou trop tard
    # (horodatages du proxy hors grille). On compare avec le rush et on corrige le calage à l'image près.
    sel = (ICI / "rushes" / "selects-1440.mp4").as_posix()
    for d in out:
        am = (math.floor((d["debut_ms"] + 700) / IMG) + 0.5) * IMG
        a = _image(sel, am)
        ecarts = [float(np.abs(a - _image(PROXY, d["source_rush_ms"][0] + (am - d["debut_ms"]) + k * IMG + IMG / 4, f"scale=1440:2560,{ETALO},scale=144:256")).mean())
                  for k in (-1, 0, 1)]
        k = (-1, 0, 1)[int(np.argmin(ecarts))]
        if min(ecarts) > ecarts[1] - 0.3:   # écart insignifiant : on ne touche pas au calage
            k = 0
        if k:
            d["debut_ms"] = round(d["debut_ms"] - k * IMG)
            d["fin_ms"] = d["debut_ms"] + (d["source_rush_ms"][1] - d["source_rush_ms"][0])
        print(f"  {d['nom']:12s} calage {k:+d} image (écarts {[round(e, 2) for e in ecarts]})")
    print(f"selects : {len(out)} prises, {off / 1000:.2f} s")
    return out


def _image(f, t, vf="scale=144:256"):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t / 1000:.4f}", "-i", f, "-frames:v", "1", "-vf", vf,
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).astype(np.float32)


if __name__ == "__main__":
    main()
