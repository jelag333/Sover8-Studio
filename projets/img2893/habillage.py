"""Habillage IMG_2893 (« Top 3 des doudounes de PNJ ») -> plan.json.
Nouveautés testées : plaque de PNJ façon jeu vidéo au-dessus de la tête (placée par suivi du visage, niveau qui
monte : 1 -> 50 -> MAX), médailles de classement, vraies photos produits, roulement de tambour avant la révélation,
confettis + corne de fête, tampon « FINITO »."""
import json
import re
import sys
from pathlib import Path

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI.parent.parent / "outils"))
tl = json.loads((ICI / ".timeline.json").read_text(encoding="utf-8"))
clips = json.loads((ICI / ".clips-dyn.json").read_text(encoding="utf-8"))
R = {r["nom"]: r for r in tl["reperes"]}
C = {c["nom"]: c for c in clips}

# ---------------------------------------------------------------- mots (repères de tout l'habillage)
mots = []
for w in json.loads((ICI / ".mots-dyn.json").read_text(encoding="utf-8")):
    m = w["mot"]
    if (m.startswith("'") or m.startswith("-")) and mots:
        mots[-1]["mot"] += m
        mots[-1]["fin_ms"] = w["fin_ms"]
        continue
    mots.append({"mot": m, "debut_ms": w["debut_ms"], "fin_ms": w["fin_ms"], "prise": w["prise"]})


def fusion(i, n, texte):
    mots[i:i + n] = [{"mot": texte, "debut_ms": mots[i]["debut_ms"], "fin_ms": mots[i + n - 1]["fin_ms"],
                      "prise": mots[i]["prise"]}]


i = 0
while i < len(mots):
    if mots[i]["mot"] == "dis" and [x["mot"] for x in mots[i + 1:i + 3]] == ["le", "moi"]:
        fusion(i, 3, "dis-le-moi")
    i += 1

for r in tl["reperes"]:  # premier mot de chaque prise = attaque réelle (repéré par la PRISE, jamais par le texte)
    j = next(j for j, m in enumerate(mots) if m["prise"] == r["nom"])
    mots[j]["debut_ms"] = r["attaque_ms"]
for j in range(1, len(mots)):
    mots[j]["debut_ms"] = max(mots[j]["debut_ms"], mots[j - 1]["debut_ms"] + 90)
for j in range(len(mots) - 1):
    mots[j]["fin_ms"] = max(mots[j]["debut_ms"] + 60, min(mots[j]["fin_ms"], mots[j + 1]["debut_ms"]))

LIGNES = [
    "Top 3 des doudounes", "de PNJ", "pour cet hiver.",
    "On commence", "par le top 3,", "c'est la Moncler", "Maya noire brillante,", "celle-là les gars,", "elle est finito.",
    "En top 2,", "on a cette doudoune", "Canada Goose", "noire mate,", "il me semble", "que c'est la Mac Milan,",
    "mais je ne suis pas sûr.",
    "Bref, si t'as ça,", "t'es aussi", "un gros PNJ.",
    "Et le top 1", "selon la communauté", "Discord", "de 100 000 membres", "qui se trouve", "dans ma bio d'ailleurs.",
    "C'est cette doudoune", "Burberry,", "donc si tu l'as,", "dis-le-moi en commentaire", "et félicitations", "mon frérot,",
    "tu es le plus gros PNJ", "que je connaisse.",
]
n = sum(len(l.split()) for l in LIGNES)
if n != len(mots):
    for j, m in enumerate(mots):
        print(j, m["prise"], m["mot"])
    raise SystemExit(f"lignes : {n} mots, transcription : {len(mots)}")
k = 0
for l in LIGNES:
    for t in l.split():
        mots[k]["mot"] = t
        k += 1


def W(mot, apres=0, n=1):
    for m in mots:
        if m["debut_ms"] >= apres and re.sub(r"[,.!?]", "", m["mot"]).lower() == mot:
            n -= 1
            if n == 0:
                return m["debut_ms"]
    raise KeyError(mot)


A = {nom: R[nom]["attaque_ms"] for nom in R}
fin_plan = lambda nom, marge=60: R[nom]["plan_ms"][1] - marge
rel = lambda nom, t: t - R[nom]["plan_ms"][0]

# ---------------------------------------------------------------- tête (suivi du visage) : où poser la plaque PNJ
from lib import suivi
_track = suivi.track_face(clips[0]["fichier"])


PLAQUE_L = 0.46
POINTE = 0.0452 * PLAQUE_L / 0.46        # distance centre de la plaque -> pointe (fraction de la hauteur d'écran)


def tete(t):
    """(x, y) écran du centre de la plaque, au temps t du montage (plan large) : la POINTE se pose 20 px au-dessus
    du haut de la casquette. Calibré sur le rush : haut de la casquette ≈ centre du visage - 0,83 × hauteur du visage."""
    nom = next(n for n in R if R[n]["plan_ms"][0] <= t < R[n]["plan_ms"][1])
    p = suivi.at(_track, C[nom]["debut_ms"] + (t - R[nom]["plan_ms"][0]))
    x = p["cx"] / 1440
    y = (p["cy"] - 0.83 * p["h"]) / 2560 - 0.0105 - POINTE
    return round(min(0.75, max(0.25, x)), 4), round(max(0.06, y), 4)


def piste(t0, t1, pas=100):
    """Motion track : positions de la tête toutes les 100 ms (la plaque suit ses mouvements)."""
    return [{"t_ms": t, "x": tete(t)[0], "y": tete(t)[1]} for t in range(t0 + pas, t1, pas)]


# ---------------------------------------------------------------- zooms (jamais pendant une plaque PNJ)
def zoom(nom, t, z, d, pourquoi, cible="visage"):
    o = {"t_ms": rel(nom, t), "zoom": z, "cible": cible, "duree_ms": d, "pourquoi": pourquoi}
    if cible == "visage":
        o["ecran_y"] = 0.36
    return o


t_bur = W("burberry")
Z = {
    "Top3": {"zooms": [zoom("Top3", W("finito"), 1.4, 600, "La chute (« elle est FINITO ») : punch serré.")]},
    "Top2": {"zoom": 1.15},
    "Top1": {"zooms": [zoom("Top1", W("top", apres=A["Top1"]), 1.3, 1200, "Suspense du top 1 : rapprochement lent pendant le roulement de tambour.")]},
    "Burberry": {"zooms": [zoom("Burberry", t_bur, 1.35, 600, "La révélation (BURBERRY)."),
                           zoom("Burberry", W("félicitations"), 1.0, 900, "Retour large : la plaque « PNJ niv. MAX » arrive au-dessus de sa tête.", cible="plan")]},
}
for c in clips:
    c.update(Z.get(c["nom"], {}))

# ---------------------------------------------------------------- motion design
t_pnj1, t_pnj2, t_pnj3 = W("pnj"), W("pnj", apres=A["PNJ2"]), W("pnj", apres=A["Burberry"])
coin = dict(x=0.71, y=0.46, largeur=0.2)            # médaille sur le coin haut-DROIT de la carte (le visage est à gauche)
produit = dict(x=0.5, y=0.6, largeur=0.44, pop=1.3)
S = [
    dict(id="bandeau-top3-doudounes-pnj", x=0.5, y=0.64, largeur=0.86, apparait_ms=60, disparait_ms=fin_plan("Accroche"),
         pourquoi="Accroche : bandeau « CLASSEMENT — TOP 3 DOUDOUNES DE PNJ » dès la première image."),
    dict(id="plaque-pnj-niv1", **dict(zip(("x", "y"), tete(t_pnj1 - 100))), largeur=PLAQUE_L, apparait_ms=t_pnj1, disparait_ms=fin_plan("Accroche"),
         lueur="aucune", suivi_ms=220, deplacements=piste(t_pnj1 - 100, fin_plan("Accroche") + 250), pourquoi="« de PNJ » : plaque de personnage de jeu vidéo au-dessus de sa tête, niveau 1."),
    dict(id="produit-moncler-maya-noire", **produit, apparait_ms=W("moncler"), disparait_ms=fin_plan("Top3"),
         pourquoi="« la MONCLER Maya noire brillante » : la vraie doudoune (photo officielle)."),
    dict(id="medaille-3", **coin, lueur="#E0995A", lueur_rayon=0.6, lueur_opacite=95, lueur_intensite=1.6, lueur_anim=True, reflet={}, apparait_ms=W("3", apres=A["Top3"]), disparait_ms=fin_plan("Top3"), pourquoi="« top 3 » : médaille de bronze."),
    dict(id="tampon-finito", x=0.5, y=0.62, largeur=0.56, apparait_ms=W("finito"), disparait_ms=fin_plan("Top3"), lueur="aucune",
         pop=1.35, pourquoi="« elle est FINITO » : tampon rouge sur la Moncler."),
    dict(id="produit-canada-goose-macmillan-noire", **produit, apparait_ms=W("canada"), disparait_ms=fin_plan("PNJ2"),
         pourquoi="« Canada Goose noire mate » : la vraie doudoune ; elle reste pendant « si t'as ça »."),
    dict(id="medaille-2", **coin, lueur="#DCE1E8", lueur_rayon=0.6, lueur_opacite=95, lueur_intensite=1.6, lueur_anim=True, reflet={}, apparait_ms=W("2", apres=A["Top2"]), disparait_ms=fin_plan("PNJ2"), pourquoi="« top 2 » : médaille d'argent."),
    dict(id="plaque-pnj-niv50", **dict(zip(("x", "y"), tete(t_pnj2 - 100))), largeur=PLAQUE_L, apparait_ms=t_pnj2, disparait_ms=fin_plan("PNJ2"),
         lueur="aucune", suivi_ms=220, deplacements=piste(t_pnj2 - 100, fin_plan("PNJ2") + 250), pourquoi="« t'es aussi un gros PNJ » : la plaque revient, niveau 50."),
    dict(id="logo-discord", x=0.5, y=0.6, largeur=0.56, apparait_ms=W("discord"), disparait_ms=W("qui", apres=W("discord")),
         pourquoi="« la communauté DISCORD »."),
    dict(id="pastille-100k-membres", x=0.5, y=0.69, largeur=0.62, apparait_ms=W("100"), disparait_ms=W("qui", apres=W("discord")),
         pourquoi="« 100 000 membres »."),
    dict(id="bouton-lien-en-bio", x=0.5, y=0.62, largeur=0.6, apparait_ms=W("bio"), disparait_ms=fin_plan("Top1"),
         pourquoi="« dans ma bio » : le bouton."),
    dict(id="produit-burberry-doudoune-noire", **produit, apparait_ms=t_bur, disparait_ms=W("dis-le-moi"), reflet={"t_ms": t_bur + 600},
         pourquoi="La révélation : la doudoune Burberry (photo officielle), sur le flash et l'impact."),
    dict(id="medaille-1", **coin, lueur="#F5C542", lueur_rayon=0.6, lueur_opacite=95, lueur_intensite=1.6, lueur_anim=True, reflet={}, apparait_ms=W("1", apres=A["Top1"]), disparait_ms=W("dis-le-moi"),
         pourquoi="« le top 1 » : médaille d'or… seule, sans doudoune : suspense jusqu'à la révélation."),
    dict(id="commentaire-burberry", x=0.5, y=0.64, largeur=0.72, apparait_ms=W("commentaire"), disparait_ms=W("mon", apres=A["Burberry"]),
         pourquoi="« dis-le-moi en COMMENTAIRE » : un faux commentaire d'abonné."),
    dict(id="confettis", x=0.5, y=0.5, largeur=1.0, apparait_ms=W("félicitations"), disparait_ms=t_pnj3 - 150, lueur="aucune", pop=1.15,
         pourquoi="« FÉLICITATIONS » : explosion de confettis autour de lui."),
    dict(id="plaque-pnj-max", **dict(zip(("x", "y"), tete(t_pnj3 - 100))), largeur=PLAQUE_L, apparait_ms=t_pnj3, disparait_ms=fin_plan("Burberry", 250),
         lueur="aucune", suivi_ms=220, deplacements=piste(t_pnj3 - 100, fin_plan("Burberry")), pourquoi="« le plus gros PNJ que je connaisse » : plaque dorée, niveau MAX (fin du running gag)."),
]
AVANCE = 100  # les objets apparaissent 100 ms avant le mot (lisibles quand il est prononcé)
for s in S:
    if s["apparait_ms"] > 200:
        s["apparait_ms"] -= AVANCE
    if s.get("reflet") == {}:                     # reflet juste après la fin du pop
        s["reflet"] = {"t_ms": s["apparait_ms"] + 650}

# ---------------------------------------------------------------- transitions flash + déclencheur photo
coupes = [R["Top2"]["plan_ms"][0], R["Top1"]["plan_ms"][0], R["Burberry"]["plan_ms"][0]]
F = [dict(t_ms=t, couleur="#FFFFFF", pic=45, montee_ms=30, descente_ms=240, pourquoi="Transition flash entre deux rangs.")
     for t in coupes]

# ---------------------------------------------------------------- sound design (nouveaux : 8-bit, ding, tambour, fête, level-up)
duree_tambour = t_bur - A["Top1"]
X = [dict(id="clic-de-photo-09", t_ms=t - 20, calage="debut", sous_voix_db=13, pourquoi="Transition flash : déclencheur photo.")
     for t in coupes[:2]] + [
    dict(id="8-bit-bounce", t_ms=t_pnj1 - AVANCE, calage="debut", sous_voix_db=15, pourquoi="Plaque PNJ niv. 1 : son de jeu vidéo."),
    dict(id="short-punchy-sine-wave-ding-4-d-211755", t_ms=W("3", apres=A["Top3"]) - AVANCE, calage="debut", sous_voix_db=16, pourquoi="Médaille #3."),
    dict(id="pop-bloup", t_ms=W("moncler") - AVANCE, sous_voix_db=13, pourquoi="La Moncler apparaît."),
    dict(id="punch", t_ms=W("finito") - 60, sous_voix_db=14, pourquoi="Le tampon FINITO s'écrase."),
    dict(id="comical-disappointment", t_ms=W("finito") + 250, calage="debut", sous_voix_db=13, pourquoi="« finito » : déception comique."),
    dict(id="short-punchy-sine-wave-ding-4-d-211755", t_ms=W("2", apres=A["Top2"]) - AVANCE, calage="debut", sous_voix_db=16, pourquoi="Médaille #2."),
    dict(id="jug-pop-1-186886", t_ms=W("canada") - AVANCE, pourquoi="La Canada Goose apparaît (pop grave)."),
    dict(id="8-bit-bounce", t_ms=t_pnj2 - AVANCE, calage="debut", sous_voix_db=15, pourquoi="Plaque PNJ niv. 50 : même son (running gag)."),
    dict(id="drumroll", t_ms=A["Top1"], calage="debut", source_debut_ms=max(0, 4662 - duree_tambour), sous_voix_db=20,
         pourquoi="Roulement de tambour pendant l'annonce du top 1 : il finit pile sur la révélation."),
    dict(id="short-punchy-sine-wave-ding-4-d-211755", t_ms=W("1", apres=A["Top1"]) - AVANCE, calage="debut", sous_voix_db=16, pourquoi="Médaille #1."),
    dict(id="cinemear-graphix-pop-finger-drum-on-a-tiny-vase", t_ms=W("discord") - AVANCE, sous_voix_db=14, pourquoi="Logo Discord."),
    dict(id="click-02", t_ms=W("bio") - AVANCE, calage="debut", sous_voix_db=14, pourquoi="Bouton lien en bio."),
    dict(id="clic-de-photo-09", t_ms=coupes[2] - 20, calage="debut", sous_voix_db=13, pourquoi="Flash de la révélation."),
    dict(id="impact-doux", t_ms=t_bur - AVANCE, sous_voix_db=12, pourquoi="Révélation BURBERRY : impact sur la fin du tambour."),
    dict(id="minimal-pop-click-ui-3-198303", t_ms=W("commentaire") - AVANCE, sous_voix_db=15, pourquoi="Le commentaire."),
    dict(id="party-horn", t_ms=W("félicitations") - AVANCE, calage="debut", sous_voix_db=13, pourquoi="« félicitations » : corne de fête + confettis."),
    dict(id="am-level-up-02", t_ms=t_pnj3 - AVANCE, calage="debut", sous_voix_db=14, pourquoi="PNJ niveau MAX : level-up."),
]

CLES = [{"mot": "PNJ", "t_ms": t_pnj1}, {"mot": "finito.", "t_ms": W("finito")}, {"mot": "PNJ.", "t_ms": t_pnj2},
        {"mot": "Discord", "t_ms": W("discord")}, {"mot": "Burberry,", "t_ms": t_bur}, {"mot": "PNJ", "t_ms": t_pnj3}]

plan = {
    "nom": "img2893", "format": "9:16", "export": {"resolution": "1080p", "fps": 30},
    "_notes": "Top 3 doudounes de PNJ : plaques PNJ jeu vidéo, médailles, photos produits, tambour, confettis ; Timeless (instrumental).",
    "voix": {"fichier": (ICI / "rushes" / "voix-dyn.wav").as_posix(), "volume": 1.0},
    "lueur_defaut": "ombre",
    "musique": {"id": "timeless-instrumental", "source_debut_ms": 23750 - A["Top3"], "volume": 0.08, "volume_sous_voix": 0.05,
                "fondu_entree_ms": 120, "fondu_sortie_ms": 700,
                "pourquoi": "Timeless (instrumental) : très trend et SANS chant (aucune concurrence avec la voix) ; drop calé sur le début du classement."},
    "clips": clips, "stickers": S, "flashs": F, "sfx": X,
    "sous_titres": {"preset": "sover8-pop", "mots": mots, "cles": CLES, "lignes": LIGNES},
}
(ICI / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"plan.json : {len(clips)} plans, {len(S)} objets, {len(F)} flashs, {len(X)} SFX, {len(mots)} mots")
print("plaques :", tete(t_pnj1), tete(t_pnj2), tete(t_pnj3 + 300))
