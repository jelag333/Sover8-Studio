"""Habillage IMG_2856 -> plan.json (zooms, motion design, transitions flash, SFX, sous-titres, musique).
Les temps des objets et des sons sont pris sur les MOTS (fonction W) : ils suivent le montage automatiquement."""
import json
import re
from pathlib import Path

ICI = Path(__file__).parent
tl = json.loads((ICI / ".timeline.json").read_text(encoding="utf-8"))
clips = json.loads((ICI / ".clips-dyn.json").read_text(encoding="utf-8"))
R = {r["nom"]: r for r in tl["reperes"]}

# ---------------------------------------------------------------- sous-titres (d'abord : les mots servent de repères)
brut = json.loads((ICI / ".mots-dyn.json").read_text(encoding="utf-8"))
mots = []
for w in brut:
    m = w["mot"]
    if (m.startswith("'") or m.startswith("-")) and mots:   # « s'il », « attendez-vous », « inscris-toi »
        mots[-1]["mot"] += m
        mots[-1]["fin_ms"] = w["fin_ms"]
        continue
    mots.append({"mot": m, "debut_ms": w["debut_ms"], "fin_ms": w["fin_ms"], "prise": w["prise"]})


def fusion(i, n, texte):
    mots[i:i + n] = [{"mot": texte, "debut_ms": mots[i]["debut_ms"], "fin_ms": mots[i + n - 1]["fin_ms"],
                      "prise": mots[i]["prise"]}]


i = 0
while i < len(mots):
    m = mots[i]["mot"]
    nxt = [x["mot"] for x in mots[i + 1:i + 3]]
    if m == "Sugar" and nxt[:1] and nxt[0].startswith("Goo"):
        fusion(i, 2, "Sugargoo,")
    elif m == "moins" and nxt[:2] == ["40", "%"]:
        fusion(i, 3, "-40%")
    elif m == "moins" and nxt[:2] == ["500", "$"]:
        fusion(i, 3, "-500$")
    elif m == "De" and i and mots[i - 1]["mot"].startswith("prix"):   # « de prix [et] de valeur » : « et » avalé
        mots.insert(i, {"mot": "et", "debut_ms": mots[i]["debut_ms"] - 90, "fin_ms": mots[i]["debut_ms"],
                        "prise": mots[i]["prise"]})
        i += 1
    i += 1

# premier mot de chaque prise = attaque réelle (Whisper le place mal). On repère la prise par son NOM, jamais par
# le texte du mot : « c'est », « et », « en » existent aussi au milieu des phrases (bug corrigé le 2026-09-26)
for r in tl["reperes"]:
    j = next(j for j, m in enumerate(mots) if m["prise"] == r["nom"])
    mots[j]["debut_ms"] = r["attaque_ms"]
for j in range(1, len(mots)):
    mots[j]["debut_ms"] = max(mots[j]["debut_ms"], mots[j - 1]["debut_ms"] + 90)
for j in range(len(mots) - 1):
    mots[j]["fin_ms"] = max(mots[j]["debut_ms"] + 60, min(mots[j]["fin_ms"], mots[j + 1]["debut_ms"]))

LIGNES = [
    "Ça y est les gars,", "c'est fini,", "c'est la fin", "de la REP.",
    "C'est pas à cause", "d'une loi,", "ni à cause", "de la douane,", "c'est les agents", "qui deviennent",
    "de plus en plus", "stricts.",
    "Si on prend l'exemple", "de Sugargoo,", "ils ont encore bloqué", "plein de marques.",
    "Gucci, Chanel,", "Hermès, Stüssy.", "Donc en fait,", "c'est même plus", "une question", "de prix et de valeur",
    "de l'item,", "mais de marque.",
    "Et personne", "ne pourra te dire", "quelle est", "la prochaine marque", "ou sur quelle agence", "ça arrivera.",
    "Donc bien sûr, non,", "c'est pas la fin", "de la seconde main,", "mais attendez-vous", "à ce que dans",
    "les mois et les années", "qui arrivent,",
    "ce soit de plus en plus", "compliqué à commander", "certaines marques.",
    "En tout cas", "sur Boonbuy,", "toutes ces marques", "sont encore disponibles,", "donc si tu veux", "commander",
    "et ne pas rater ça,", "inscris-toi avec le lien", "qui est dans ma bio", "pour avoir -40%", "et -500$ en coupon",
    "sur ta livraison.",
]
n = sum(len(l.split()) for l in LIGNES)
if n != len(mots):
    for j, m in enumerate(mots):
        print(j, m["mot"], m["debut_ms"])
    raise SystemExit(f"lignes : {n} mots, transcription : {len(mots)}")
k = 0
for l in LIGNES:
    for t in l.split():
        mots[k]["mot"] = t
        k += 1


def cle(m):
    return re.sub(r"[,.!?]", "", m).lower()


def W(mot, apres=0, n=1):
    """Instant (ms, montage) où le mot est prononcé : n-ième occurrence après `apres`."""
    for m in mots:
        if m["debut_ms"] >= apres and cle(m["mot"]) == mot:
            n -= 1
            if n == 0:
                return m["debut_ms"]
    raise KeyError(mot)


def fin_plan(nom, marge=60):
    return R[nom]["plan_ms"][1] - marge


def rel(nom, t):
    return t - R[nom]["plan_ms"][0]


# ---------------------------------------------------------------- zooms (cadrent la personne : visage à 36 %)
def zoom(nom, t, z, d, pourquoi, cible="visage"):
    out = {"t_ms": rel(nom, t), "zoom": z, "cible": cible, "duree_ms": d, "pourquoi": pourquoi}
    if cible == "visage":
        out["ecran_y"] = 0.36
    return out


a_cta = R["CTA"]["attaque_ms"]
Z = {
    "Accroche": {"zooms": [zoom("Accroche", W("fin"), 1.5, 700, "« c'est la FIN de la REP » : le choc de l'accroche.")]},
    "Cause": {"zooms": [zoom("Cause", W("agents"), 1.4, 700, "La vraie cause (« c'est LES AGENTS ») : la révélation.")]},
    "Sugargoo": {},
    "Marques": {"zoom": 1.15},
    "Personne": {"zooms": [zoom("Personne", W("personne"), 1.35, 900, "L'incertitude (« personne ne pourra te dire ») : rapprochement lent.")]},
    "Fin": {"zooms": [zoom("Fin", W("non"), 1.5, 700, "« NON, c'est pas la fin » : la réponse à l'accroche, cadre serré.")]},
    "Compliqué": {"zoom": 1.15},
    "CTA": {"zooms": [zoom("CTA", W("boonbuy"), 1.35, 700, "La solution (« sur BOONBUY ») : on se rapproche."),
                      zoom("CTA", W("inscris-toi"), 1.0, 900, "L'offre : plan large pour le bouton et les coupons.", cible="plan")]},
}
for c in clips:
    c.update(Z.get(c["nom"], {}))

# ---------------------------------------------------------------- motion design (aucun emoji)
t_ag, t_don = W("agents"), W("donc", apres=R["Marques"]["attaque_ms"])
t_toutes, t_donc_cta = W("marques", apres=a_cta), W("commander", apres=a_cta)  # grille de fin : plus longue (retour utilisateur)
S = [
    dict(id="bandeau-fin-de-la-rep", x=0.5, y=0.64, largeur=0.86, apparait_ms=60, disparait_ms=fin_plan("Accroche"),
         pourquoi="Accroche : bandeau « FLASH INFO » façon chaîne d'info, le ton de l'annonce."),
    dict(id="pastille-une-loi-barre", x=0.3, y=0.57, largeur=0.4, apparait_ms=W("loi"), disparait_ms=t_ag,
         pourquoi="« pas à cause d'une LOI » : la pastille arrive déjà barrée."),
    dict(id="pastille-la-douane-barre", x=0.68, y=0.66, largeur=0.5, apparait_ms=W("douane"), disparait_ms=t_ag,
         pourquoi="« ni de la DOUANE » : barrée aussi (même geste, même son)."),
    dict(id="pastille-les-agents", x=0.5, y=0.62, largeur=0.56, apparait_ms=t_ag, disparait_ms=fin_plan("Cause"),
         pourquoi="« c'est LES AGENTS » : la vraie cause, en orange, remplace les deux fausses pistes."),
    dict(id="logo-sugargoo", x=0.5, y=0.6, largeur=0.56, apparait_ms=W("sugargoo"), disparait_ms=fin_plan("Sugargoo", 330),
         pourquoi="« l'exemple de SUGARGOO » : le logo de l'agent (site officiel)."),
    dict(id="tampon-bloque", x=0.5, y=0.6, largeur=0.6, apparait_ms=W("bloqué"), disparait_ms=fin_plan("Sugargoo", 330),
         lueur="aucune", pop=1.35, pourquoi="« ils ont encore BLOQUÉ » : le tampon s'écrase sur le logo."),
    dict(id="logo-gucci", x=0.28, y=0.5, largeur=0.4, apparait_ms=W("gucci"), disparait_ms=t_don,
         pourquoi="Les marques citées, une par une sur leur nom, en grille 2 × 2 centrée."),
    dict(id="logo-chanel", x=0.72, y=0.5, largeur=0.4, apparait_ms=W("chanel"), disparait_ms=t_don, pourquoi="Chanel."),
    dict(id="logo-hermes", x=0.28, y=0.655, largeur=0.4, apparait_ms=W("hermès"), disparait_ms=t_don, pourquoi="Hermès."),
    dict(id="logo-stussy", x=0.72, y=0.655, largeur=0.4, apparait_ms=W("stüssy"), disparait_ms=t_don, pourquoi="Stüssy."),
    dict(id="pastille-prix-barre", x=0.3, y=0.57, largeur=0.32, apparait_ms=W("prix"), disparait_ms=fin_plan("Marques"),
         pourquoi="« plus une question de PRIX… »"),
    dict(id="pastille-valeur-barre", x=0.7, y=0.57, largeur=0.42, apparait_ms=W("valeur"), disparait_ms=fin_plan("Marques"),
         pourquoi="« …ni de VALEUR… » (barrées)"),
    dict(id="pastille-marque", x=0.5, y=0.68, largeur=0.52, apparait_ms=W("marque", apres=W("valeur")), disparait_ms=fin_plan("Marques"),
         pourquoi="« …mais de MARQUE » : la bonne réponse en orange, sous les deux barrées."),
    dict(id="carte-prochaine-marque", x=0.5, y=0.635, largeur=0.33, apparait_ms=W("prochaine"), disparait_ms=fin_plan("Personne"),
         pourquoi="« la PROCHAINE marque » : carte mystère, personne ne sait."),
    dict(id="graphique-difficulte", x=0.5, y=0.6, largeur=0.58, apparait_ms=W("compliqué"), disparait_ms=fin_plan("Compliqué"),
         pourquoi="« de plus en plus COMPLIQUÉ » : la courbe qui monte en flèche."),
    dict(id="logo-boonbuy", x=0.5, y=0.6, largeur=0.3, apparait_ms=W("boonbuy"), disparait_ms=t_toutes,
         pourquoi="« sur BOONBUY » : le logo de l'agent."),
    dict(id="logo-gucci", x=0.28, y=0.5, largeur=0.4, apparait_ms=t_toutes, disparait_ms=t_donc_cta,
         pourquoi="« TOUTES ces marques » : la même grille qu'avant revient…"),
    dict(id="logo-chanel", x=0.72, y=0.5, largeur=0.4, apparait_ms=t_toutes + 180, disparait_ms=t_donc_cta, pourquoi="…en cascade…"),
    dict(id="logo-hermes", x=0.28, y=0.655, largeur=0.4, apparait_ms=t_toutes + 360, disparait_ms=t_donc_cta, pourquoi="…"),
    dict(id="logo-stussy", x=0.72, y=0.655, largeur=0.4, apparait_ms=t_toutes + 540, disparait_ms=t_donc_cta, pourquoi="…"),
    dict(id="tampon-disponibles", x=0.5, y=0.58, largeur=0.78, apparait_ms=W("disponibles"), disparait_ms=t_donc_cta,
         lueur="aucune", pop=1.35, pourquoi="« encore DISPONIBLES » : tampon vert, la réponse au tampon rouge « BLOQUÉ »."),
    dict(id="bouton-lien-en-bio", x=0.5, y=0.6, largeur=0.6, apparait_ms=W("lien"), disparait_ms=W("pour", apres=W("lien")),
         pourquoi="« le LIEN dans ma bio » : le bouton."),
    dict(id="icone-coupon-moins-40", x=0.5, y=0.62, largeur=0.4, apparait_ms=W("-40%"), disparait_ms=fin_plan("CTA", 350),
         deplacements=[{"t_ms": W("-500$") - 150, "x": 0.28, "y": 0.62}], pourquoi="« -40 % »…"),
    dict(id="icone-coupon-moins-500", x=0.72, y=0.62, largeur=0.4, apparait_ms=W("-500$"), disparait_ms=fin_plan("CTA", 350),
         pourquoi="…et « -500 $ » côte à côte."),
]

# ---------------------------------------------------------------- transitions : flash blanc + déclencheur photo
coupes = [R["Cause"]["plan_ms"][0], R["Personne"]["plan_ms"][0], R["CTA"]["plan_ms"][0]]
F = [dict(t_ms=t, couleur="#FFFFFF", pic=45, montee_ms=30, descente_ms=240,
          pourquoi="Transition entre deux idées : flash d'appareil photo sur la coupe.") for t in coupes]

# ---------------------------------------------------------------- sound design
X = [dict(id="clic-de-photo-09", t_ms=t - 20, calage="debut", sous_voix_db=13,
          pourquoi="Transition flash : déclencheur d'appareil photo.") for t in coupes] + [
    dict(id="impact-doux", t_ms=W("fin"), sous_voix_db=14, pourquoi="« c'est la FIN de la REP » : impact, avec le zoom."),
    dict(id="minimal-pop-click-ui-3-198303", t_ms=W("loi"), sous_voix_db=15, pourquoi="Pastille « loi »."),
    dict(id="minimal-pop-click-ui-3-198303", t_ms=W("douane"), sous_voix_db=15, pourquoi="Pastille « douane » : même son, même geste."),
    dict(id="pop-bloup", t_ms=t_ag, sous_voix_db=13, pourquoi="« LES AGENTS » : pop plus rond, c'est la bonne réponse."),
    dict(id="cinemear-graphix-pop-finger-drum-on-a-tiny-vase", t_ms=W("sugargoo"), sous_voix_db=13, pourquoi="Logo Sugargoo."),
    dict(id="punch", t_ms=W("bloqué") + 40, sous_voix_db=14, pourquoi="Le tampon « BLOQUÉ » s'écrase."),
] + [dict(id="click-02", t_ms=W(b), calage="debut", sous_voix_db=16, pourquoi=f"{b} : clic de liste, un par marque.")
     for b in ("gucci", "chanel", "hermès", "stüssy")] + [
    dict(id="pop-bloup", t_ms=W("marque", apres=W("valeur")), sous_voix_db=13, pourquoi="« mais de MARQUE »."),
    dict(id="jug-pop-3-186888", t_ms=W("prochaine"), sous_voix_db=13, pourquoi="Carte mystère."),
    dict(id="cinematic-ease-out-1", t_ms=W("non"), calage="debut", sous_voix_db=13, pourquoi="Zoom « non, c'est pas la fin »."),
    dict(id="whoosh-air-court", t_ms=W("compliqué"), sous_voix_db=15, pourquoi="La courbe qui monte."),
    dict(id="cinemear-graphix-pop-finger-drum-on-a-tiny-vase", t_ms=W("boonbuy"), sous_voix_db=13, pourquoi="Logo Boonbuy."),
    dict(id="punch", t_ms=W("disponibles") + 40, sous_voix_db=14, pourquoi="Tampon « DISPONIBLES » : même coup que « BLOQUÉ » (écho)."),
    dict(id="click-02", t_ms=W("lien"), calage="debut", sous_voix_db=13, pourquoi="Le bouton « lien en bio »."),
    dict(id="cash-register-3", t_ms=W("-40%"), sous_voix_db=13, pourquoi="« -40 % »."),
    dict(id="coins", t_ms=W("-500$"), calage="debut", pourquoi="« -500 $ »."),
]

# retour utilisateur : les objets arrivaient un peu après le mot -> apparition 150 ms AVANT le mot
# (horodatages Whisper souvent tardifs + le pop met un instant à devenir lisible) ; les sons d'apparition suivent
AVANCE = 100
for s_ in S:
    if s_["apparait_ms"] > 200:
        s_["apparait_ms"] -= AVANCE
for x in X:
    if x["id"] not in ("clic-de-photo-09", "impact-doux", "cinematic-ease-out-1"):
        x["t_ms"] -= AVANCE

CLES = [{"mot": "REP.", "t_ms": W("rep")}, {"mot": "agents", "t_ms": t_ag}, {"mot": "bloqué", "t_ms": W("bloqué")},
        {"mot": "marque.", "t_ms": W("marque", apres=W("valeur"))}, {"mot": "non,", "t_ms": W("non")},
        {"mot": "disponibles,", "t_ms": W("disponibles")}, {"mot": "-40%", "t_ms": W("-40%")}, {"mot": "-500$", "t_ms": W("-500$")}]

plan = {
    "nom": "img2856", "format": "9:16", "export": {"resolution": "1080p", "fps": 30},
    "_notes": "Dérush serré (J-cuts 50 ms), source 1440p étalonnée, zooms qui cadrent, motion design sans emoji, "
              "transitions flash, SFX, God's Plan en fond.",
    "voix": {"fichier": (ICI / "rushes" / "voix-dyn.wav").as_posix(), "volume": 1.0},
    "lueur_defaut": "ombre",
    "musique": {"id": "god-s-plan", "source_debut_ms": 24750 - R["Cause"]["attaque_ms"], "volume": 0.09,
                "volume_sous_voix": 0.05, "fondu_entree_ms": 120, "fondu_sortie_ms": 700,
                "pourquoi": "God's Plan : tempo posé (77 BPM) qui colle au ton info, son très TikTok ; drop calé sur la fin "
                            "de l'accroche ; plus bas que d'habitude car la musique est chantée."},
    "clips": clips, "stickers": S, "flashs": F, "sfx": X,
    "sous_titres": {"preset": "sover8-pop", "mots": mots, "cles": CLES, "lignes": LIGNES},
}
(ICI / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"plan.json : {len(clips)} plans, {len(S)} objets, {len(F)} flashs, {len(X)} SFX, {len(mots)} mots")
