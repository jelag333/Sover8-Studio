"""Habillage IMG_2859 (« Ton prochain haul va prendre du retard » : vacances en Chine) -> plan.json."""
import json
import re
from pathlib import Path

ICI = Path(__file__).parent
tl = json.loads((ICI / ".timeline.json").read_text(encoding="utf-8"))
clips = json.loads((ICI / ".clips-dyn.json").read_text(encoding="utf-8"))
R = {r["nom"]: r for r in tl["reperes"]}
A = {n: R[n]["attaque_ms"] for n in R}

# ---------------------------------------------------------------- mots
mots = []
for w in json.loads((ICI / ".mots-dyn.json").read_text(encoding="utf-8")):
    m = w["mot"]
    if (m.startswith("'") or m.startswith("-")) and mots:
        mots[-1]["mot"] += m
        mots[-1]["fin_ms"] = w["fin_ms"]
        continue
    mots.append({"mot": m, "debut_ms": w["debut_ms"], "fin_ms": w["fin_ms"], "prise": w["prise"]})


def fusion(i, n, texte):
    mots[i:i + n] = [{"mot": texte, "debut_ms": mots[i]["debut_ms"], "fin_ms": mots[i + n - 1]["fin_ms"], "prise": mots[i]["prise"]}]


i = 0
while i < len(mots):
    nxt = [x["mot"] for x in mots[i + 1:i + 3]]
    if mots[i]["mot"] == "moins" and nxt[:2] == ["40", "%"]:
        fusion(i, 3, "-40%")
    elif mots[i]["mot"] == "moins" and nxt[:2] == ["500", "$"]:
        fusion(i, 3, "-500$")
    elif mots[i]["mot"] == "tu" and nxt[:2] == ["es", "à"]:
        fusion(i, 3, "t'as")
    i += 1

for r in tl["reperes"]:  # premier mot de chaque prise = attaque réelle (repéré par la prise)
    j = next(j for j, m in enumerate(mots) if m["prise"] == r["nom"])
    mots[j]["debut_ms"] = r["attaque_ms"]
for j in range(1, len(mots)):
    mots[j]["debut_ms"] = max(mots[j]["debut_ms"], mots[j - 1]["debut_ms"] + 90)
for j in range(len(mots) - 1):
    mots[j]["fin_ms"] = max(mots[j]["debut_ms"] + 60, min(mots[j]["fin_ms"], mots[j + 1]["debut_ms"]))

LIGNES = [
    "Ton prochain haul", "va prendre du retard.",
    "Eh oui,", "du 25 au 27 septembre", "et du 1er au 7 octobre,", "il y aura", "des vacances en Chine.",
    "Le point positif,", "c'est que Boonbuy", "ne part pas en vacances,", "donc il reste ouvert,", "ça tourne",
    "comme d'habitude,", "que ce soit", "les achats,", "les photos QC,", "l'expédition, etc.", "Tout reste", "comme d'habitude.",
    "Le point pas ouf,", "c'est concernant", "les vendeurs,", "parce que chez eux,", "on n'a aucune information,",
    "ça va dépendre", "de chaque vendeur.",
    "Certains vont rester", "comme d'habitude", "et d'autres vont partir", "en vacances.",
    "Donc tu risques", "d'avoir des délais", "supplémentaires", "de ton vendeur", "jusqu'à l'entrepôt", "Boonbuy.",
    "Et le point", "vraiment compliqué,", "c'est qu'après les fêtes,", "l'hiver arrive.",
    "Les compagnies aériennes", "vont couper les vols,", "c'est-à-dire", "moins de vols,", "moins de place", "dans les soutes.",
    "Donc forcément", "plus cher", "et potentiellement", "plus de délai aussi.",
    "Donc si tu avais", "un haul en tête,", "fais-le maintenant", "avant le 25,", "comme ça tu n'auras", "pas de problème.",
    "Et comme d'habitude,", "t'as -40%", "et -500$ en coupon", "en t'inscrivant", "avec le lien", "qui est dans ma bio.",
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


fin_plan = lambda nom, marge=60: R[nom]["plan_ms"][1] - marge
rel = lambda nom, t: t - R[nom]["plan_ms"][0]


def zoom(nom, t, z, d, pourquoi, cible="visage"):
    o = {"t_ms": rel(nom, t), "zoom": z, "cible": cible, "duree_ms": d, "pourquoi": pourquoi}
    if cible == "visage":
        o["ecran_y"] = 0.36
    return o


Z = {
    "Accroche": {"zooms": [zoom("Accroche", W("retard"), 1.45, 600, "« va prendre du RETARD » : le choc de l'accroche.")]},
    "Positif": {"zooms": [zoom("Positif", W("positif"), 1.3, 800, "« le point POSITIF » : bonne nouvelle, on se rapproche.")]},
    "Vendeurs": {"zooms": [zoom("Vendeurs", W("ouf"), 1.35, 700, "« le point PAS OUF » : changement de ton.")]},
    "Certains": {"zoom": 1.15},
    "Hiver": {"zooms": [zoom("Hiver", W("compliqué"), 1.45, 700, "« VRAIMENT COMPLIQUÉ » : le point le plus grave.")]},
    "Cher": {"zoom": 1.15},
    "Maintenant": {"zooms": [zoom("Maintenant", W("maintenant"), 1.4, 600, "« fais-le MAINTENANT » : l'appel à agir.")]},
}
for c in clips:
    c.update(Z.get(c["nom"], {}))

# ---------------------------------------------------------------- motion design
a_pos, a_cta = A["Positif"], A["CTA"]
t_ouvert = W("ouvert")
S = [
    dict(id="bandeau-haul-retard", x=0.5, y=0.64, largeur=0.9, apparait_ms=60, disparait_ms=fin_plan("Accroche"),
         pourquoi="Accroche : bandeau « ALERTE — TON HAUL VA PRENDRE DU RETARD » dès la première image."),
    dict(id="calendrier-25-27-septembre", x=0.3, y=0.58, largeur=0.33, apparait_ms=W("25"), disparait_ms=W("il", apres=A["Dates"]),
         pourquoi="« du 25 au 27 septembre »."),
    dict(id="calendrier-1-7-octobre", x=0.7, y=0.58, largeur=0.33, apparait_ms=W("1er"), disparait_ms=W("il", apres=A["Dates"]),
         pourquoi="« et du 1er au 7 octobre » : les deux périodes côte à côte."),
    dict(id="drapeau-chine", x=0.5, y=0.57, largeur=0.42, apparait_ms=W("vacances", apres=A["Dates"]), disparait_ms=fin_plan("Dates"),
         pourquoi="« des vacances en CHINE » : le drapeau…"),
    dict(id="pastille-vacances-en-chine", x=0.5, y=0.7, largeur=0.62, apparait_ms=W("chine"), disparait_ms=fin_plan("Dates"),
         pourquoi="…et le titre."),
    dict(id="logo-boonbuy", x=0.5, y=0.58, largeur=0.3, apparait_ms=W("boonbuy"), disparait_ms=W("achats") - 150,
         pourquoi="« Boonbuy ne part pas en vacances »."),
    dict(id="tampon-ouvert", x=0.5, y=0.6, largeur=0.62, apparait_ms=t_ouvert, disparait_ms=W("achats") - 150, lueur="aucune", pop=1.35,
         pourquoi="« il reste OUVERT » : tampon vert sur le logo."),
    dict(id="pastille-ok-achats", x=0.5, y=0.55, largeur=0.46, apparait_ms=W("achats"), disparait_ms=fin_plan("Positif"),
         pourquoi="La liste de ce qui continue, cochée une ligne par mot : achats…"),
    dict(id="pastille-ok-photos-qc", x=0.5, y=0.63, largeur=0.54, apparait_ms=W("photos"), disparait_ms=fin_plan("Positif"), pourquoi="…photos QC…"),
    dict(id="pastille-ok-expedition", x=0.5, y=0.71, largeur=0.58, apparait_ms=W("l'expédition"), disparait_ms=fin_plan("Positif"), pourquoi="…expédition."),
    dict(id="pastille-les-vendeurs", x=0.5, y=0.6, largeur=0.58, apparait_ms=W("vendeurs"), disparait_ms=W("aucune") - 150,
         pourquoi="« les VENDEURS » : le sujet du point pas ouf."),
    dict(id="carte-aucune-info", x=0.5, y=0.63, largeur=0.34, apparait_ms=W("aucune"), disparait_ms=fin_plan("Vendeurs"),
         pourquoi="« AUCUNE information » : carte mystère."),
    dict(id="pastille-ils-restent", x=0.5, y=0.57, largeur=0.5, apparait_ms=W("rester"), disparait_ms=fin_plan("Certains"),
         pourquoi="« certains vont RESTER »…"),
    dict(id="pastille-en-vacances", x=0.5, y=0.67, largeur=0.52, apparait_ms=W("vacances", apres=A["Certains"]), disparait_ms=fin_plan("Certains"),
         pourquoi="…« d'autres vont partir EN VACANCES »."),
    dict(id="trajet-vendeur-entrepot", x=0.5, y=0.6, largeur=0.86, apparait_ms=W("délais"), disparait_ms=fin_plan("Delais"),
         pourquoi="« des délais de ton VENDEUR jusqu'à l'ENTREPÔT » : le trajet, avec l'alerte « + DÉLAI »."),
    dict(id="pastille-hiver-arrive", x=0.5, y=0.63, largeur=0.62, apparait_ms=W("l'hiver"), disparait_ms=fin_plan("Hiver"),
         pourquoi="« l'HIVER ARRIVE » : pastille bleu glacé."),
    dict(id="photo-avion-cargo", x=0.5, y=0.6, largeur=0.82, pop=1.2, apparait_ms=W("compagnies"), disparait_ms=fin_plan("Vols"),
         pourquoi="« les compagnies aériennes » : un vrai avion cargo (Wikimedia, domaine public)."),
    dict(id="tampon-annule", x=0.5, y=0.6, largeur=0.62, apparait_ms=W("couper"), disparait_ms=fin_plan("Vols"), lueur="aucune", pop=1.35,
         pourquoi="« vont COUPER les vols » : tampon ANNULÉ sur l'avion."),
    dict(id="graphique-prix", x=0.5, y=0.6, largeur=0.56, apparait_ms=W("cher"), disparait_ms=W("délai", apres=A["Cher"]) - 150,
         pourquoi="« plus CHER » : la courbe du prix qui monte."),
    dict(id="pastille-plus-de-delai", x=0.5, y=0.62, largeur=0.56, apparait_ms=W("délai", apres=A["Cher"]), disparait_ms=fin_plan("Cher"),
         pourquoi="« plus de DÉLAI »."),
    dict(id="calendrier-avant-le-25", x=0.5, y=0.6, largeur=0.3, apparait_ms=W("avant", apres=A["Maintenant"]), disparait_ms=fin_plan("Maintenant"),
         pourquoi="« avant le 25 » : la date limite."),
    dict(id="icone-coupon-moins-40", x=0.5, y=0.62, largeur=0.4, apparait_ms=W("-40%"), disparait_ms=W("avec", apres=a_cta),
         deplacements=[{"t_ms": W("-500$") - 150, "x": 0.28, "y": 0.62}], pourquoi="« -40 % »…"),
    dict(id="icone-coupon-moins-500", x=0.72, y=0.62, largeur=0.4, apparait_ms=W("-500$"), disparait_ms=W("avec", apres=a_cta),
         pourquoi="…et « -500 $ »."),
    dict(id="bouton-lien-en-bio", x=0.5, y=0.62, largeur=0.6, apparait_ms=W("lien", apres=a_cta), disparait_ms=fin_plan("CTA", 250),
         pourquoi="« le lien dans ma bio »."),
]
AVANCE = 100
for s in S:
    if s["apparait_ms"] > 200:
        s["apparait_ms"] -= AVANCE

coupes = [R[n]["plan_ms"][0] for n in ("Positif", "Vendeurs", "Hiver", "Maintenant")]
F = [dict(t_ms=t, couleur="#FFFFFF", pic=45, montee_ms=30, descente_ms=240, pourquoi="Transition flash entre deux idées.") for t in coupes]

B = lambda mot, apres=0: W(mot, apres) - AVANCE   # instant d'apparition de l'objet posé sur ce mot
X = [dict(id="clic-de-photo-09", t_ms=t - 20, calage="debut", sous_voix_db=13, pourquoi="Transition flash : déclencheur photo.") for t in coupes] + [
    dict(id="clock-tension-7", t_ms=0, calage="debut", duree_ms=R["Accroche"]["plan_ms"][1], sous_voix_db=19, pourquoi="Accroche : tic-tac de l'horloge, le retard."),
    dict(id="impact-doux", t_ms=W("retard"), sous_voix_db=14, pourquoi="« RETARD » : impact avec le zoom."),
    dict(id="paper-ease-out-1", t_ms=B("25"), calage="debut", sous_voix_db=15, pourquoi="Les pages de calendrier."),
    dict(id="pop-bloup", t_ms=B("vacances", A["Dates"]), sous_voix_db=14, pourquoi="Le drapeau chinois."),
    dict(id="cinemear-graphix-pop-finger-drum-on-a-tiny-vase", t_ms=B("boonbuy"), sous_voix_db=13, pourquoi="Logo Boonbuy."),
    dict(id="punch", t_ms=t_ouvert - 60, sous_voix_db=14, pourquoi="Tampon OUVERT."),
] + [dict(id="short-punchy-sine-wave-ding-4-d-211755", t_ms=B(m), calage="debut", sous_voix_db=16, pourquoi=f"Coche « {m} » : ding de validation.")
     for m in ("achats", "photos", "l'expédition")] + [
    dict(id="pop-bloup", t_ms=B("vendeurs"), sous_voix_db=13, pourquoi="« les vendeurs »."),
    dict(id="jug-pop-3-186888", t_ms=B("aucune"), sous_voix_db=13, pourquoi="Carte « aucune info »."),
    dict(id="minimal-pop-click-ui-3-198303", t_ms=B("vacances", A["Certains"]), sous_voix_db=15, pourquoi="« en vacances »."),
    dict(id="whoosh-air-court", t_ms=B("délais"), sous_voix_db=15, pourquoi="Le trajet vendeur -> entrepôt."),
    dict(id="cinematic-ease-out-1", t_ms=W("compliqué"), calage="debut", sous_voix_db=14, pourquoi="Zoom « vraiment compliqué »."),
    dict(id="whoosh-air-court", t_ms=B("compagnies"), sous_voix_db=13, pourquoi="L'avion passe : souffle."),
    dict(id="punch", t_ms=W("couper") - 60, sous_voix_db=14, pourquoi="Tampon ANNULÉ (même coup que OUVERT : écho)."),
    dict(id="cinematic-ease-out-2", t_ms=B("cher"), calage="debut", sous_voix_db=15, pourquoi="La courbe du prix qui monte."),
    dict(id="paper-ease-out-1", t_ms=B("avant", A["Maintenant"]), calage="debut", sous_voix_db=15, pourquoi="Calendrier « avant le 25 »."),
    dict(id="cash-register-3", t_ms=B("-40%"), sous_voix_db=13, pourquoi="« -40 % »."),
    dict(id="coins", t_ms=B("-500$"), calage="debut", pourquoi="« -500 $ »."),
    dict(id="click-02", t_ms=B("lien", a_cta), calage="debut", sous_voix_db=14, pourquoi="Le bouton lien en bio."),
]

CLES = [{"mot": "retard.", "t_ms": W("retard")}, {"mot": "Chine.", "t_ms": W("chine")}, {"mot": "ouvert,", "t_ms": t_ouvert},
        {"mot": "vendeurs,", "t_ms": W("vendeurs")}, {"mot": "compliqué,", "t_ms": W("compliqué")},
        {"mot": "maintenant", "t_ms": W("maintenant")}, {"mot": "-40%", "t_ms": W("-40%")}, {"mot": "-500$", "t_ms": W("-500$")}]

plan = {
    "nom": "img2859", "format": "9:16", "export": {"resolution": "1080p", "fps": 30},
    "_notes": "Vacances en Chine / retard des hauls : dérush serré, étalonnage, zooms qui cadrent, motion design sans emoji, flashs, SFX.",
    "voix": {"fichier": (ICI / "rushes" / "voix-dyn.wav").as_posix(), "volume": 1.0},
    "lueur_defaut": "ombre",
    "musique": {"id": "gravitational-forces-by-blaumodus-muffled-tiktok-extended-version", "source_debut_ms": 2000 - A["Dates"],
                "volume": 0.12, "volume_sous_voix": 0.08, "fondu_entree_ms": 120, "fondu_sortie_ms": 700,
                "pourquoi": "Son doux et étouffé, que l'utilisateur a adoré ; drop calé sur les dates."},
    "clips": clips, "stickers": S, "flashs": F, "sfx": X,
    "sous_titres": {"preset": "sover8-pop", "mots": mots, "cles": CLES, "lignes": LIGNES},
}
(ICI / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"plan.json : {len(clips)} plans, {len(S)} objets, {len(F)} flashs, {len(X)} SFX, {len(mots)} mots")
