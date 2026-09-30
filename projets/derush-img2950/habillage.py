"""Habillage du dérush dynamique IMG_2950 -> plan.json (zooms, objets, flashs, SFX, sous-titres).

Les temps ci-dessous sont écrits sur le montage de référence (v2 : 100 ms entre phrases) et recalés
automatiquement (fonction M) sur le montage actuel produit par dynamique.py (.timeline.json)."""
import json
from pathlib import Path

ICI = Path(__file__).parent
tl = json.loads((ICI / ".timeline.json").read_text(encoding="utf-8"))
clips = json.loads((ICI / ".clips-dyn.json").read_text(encoding="utf-8"))
R = {r["nom"]: r for r in tl["reperes"]}

# attaques de chaque phrase dans le montage de référence
REF = [("Accroche", 40), ("TikTok", 1830), ("Identifiant", 6185), ("Étiquette", 10390), ("Blocage", 12980),
       ("Rassure", 17015), ("Agents", 19700), ("CTA", 23195)]


def M(t):
    """Temps du montage de référence -> temps du montage actuel (chaque phrase garde son calage interne)."""
    nom, a = REF[0]
    for n, x in REF:
        if t >= x - 60:
            nom, a = n, x
    return int(round(t - a + R[nom]["attaque_ms"]))


def rel(nom, t):
    return M(t) - R[nom]["plan_ms"][0]


# ---------------------------------------------------------------- zooms : on CADRE la personne (plan serré)
# visage à 36 % de la hauteur, zoom 1.35 à 1.6 : tête et épaules remplissent l'image (source 1440p, net)
def zoom(nom, t, z, d, pourquoi, cible="visage", ecran_y=0.36):
    out = {"t_ms": rel(nom, t), "zoom": z, "cible": cible, "duree_ms": d, "pourquoi": pourquoi}
    if cible == "visage":
        out["ecran_y"] = ecran_y
    return out


Z = {
    "Accroche": {"zooms": [zoom("Accroche", 640, 1.55, 700,
                                "Accroche : « la fin de la REP » est le choc ; punch serré sur « REP », il nous regarde droit dans les yeux.")]},
    "TikTok": {"zooms": [zoom("TikTok", 5190, 1.4, 700,
                              "Promesse (« je vous explique ça maintenant ») : on cadre en plan poitrine, il s'adresse à nous.")]},
    "Identifiant": {},
    "Étiquette": {"zoom": 1.15},
    "Blocage": {"zooms": [zoom("Blocage", 15640, 1.6, 600,
                               "Conséquence (« le colis est BLOQUÉ ») : le plan le plus serré de la vidéo, avec le flash rouge et l'interdit.")]},
    "Rassure": {"zooms": [zoom("Rassure", 17140, 1.35, 900,
                               "Retournement (« je te rassure ») : rapprochement plus lent et moins serré, ton rassurant.")]},
    "Agents": {"zoom": 1.15},
    "CTA": {"zooms": [zoom("CTA", 23600, 1.5, 700,
                           "Rappel de l'accroche (« c'est TOUJOURS PAS la fin de la REP ») : la chute, même cadre serré que l'accroche."),
                      zoom("CTA", 24420, 1.0, 900,
                           "Nouvelle idée (l'offre) : on rend l'image large pour laisser la place aux coupons.", cible="plan")]},
}
for c in clips:
    c.update(Z.get(c["nom"], {}))

# ---------------------------------------------------------------- objets (motion design)
# lueur : pas de lueur jaune ici (elle venait des vêtements jaunes de la vidéo mode) ; ombre portée diffuse
# noire + ombre nette : les objets se détachent du fond clair (fenêtre) sans halo coloré
S = [
    dict(id="icone-calendrier-1er-novembre", x=0.5, y=0.62, largeur=0.3, apparait_ms=1000, disparait_ms=1860,
         pourquoi="« le 1ER NOVEMBRE » : la date arrive sur « 1er », c'est l'info clé de l'accroche (carte dessinée)."),
    dict(id="tel-rep-1", x=0.5, y=0.6, largeur=0.3, apparait_ms=2570, disparait_ms=3490,
         pourquoi="« PLEIN de TikTok » : une vidéo verticale sur « plein », avec SES propres prises de l'accroche…"),
    dict(id="tel-rep-2", x=0.2, y=0.63, largeur=0.25, rotation=-8, apparait_ms=2890, disparait_ms=3490,
         pourquoi="…puis deux autres, penchées, en cascade sur « TikTok » : tout le monde en parle."),
    dict(id="tel-rep-3", x=0.8, y=0.63, largeur=0.25, rotation=8, apparait_ms=3000, disparait_ms=3490,
         pourquoi="Troisième vidéo, décalée de 110 ms pour la cascade."),
    dict(id="etiquette-produit-id", x=0.5, y=0.6, largeur=0.32, apparait_ms=7685, disparait_ms=9640,
         pourquoi="« chaque ARTICLE » : l'étiquette du vêtement, avec son code-barres."),
    dict(id="laser-scan", x=0.5, y=0.625, largeur=0.25, apparait_ms=8625, disparait_ms=9250, lueur="aucune",
         trajet={"a": [0.5, 0.692], "debut_ms": 8660, "fin_ms": 9160, "arc": 0.0},
         pourquoi="« un IDENTIFIANT produit » : le laser d'un lecteur balaie le code-barres (avec le bip)."),
    dict(id="photo-declaration-douane-cn22", x=0.5, y=0.6, largeur=0.7, pop=1.2, apparait_ms=9785, disparait_ms=10420,
         pourquoi="« sur la DÉCLARATION » : une vraie déclaration CN 22 de colis Chine (photo Wikimedia, domaine public)."),
    dict(id="photo-etiquette-colis-douane", x=0.5, y=0.615, largeur=0.7, pop=1.2, apparait_ms=11050, disparait_ms=16980,
         pourquoi="« une ÉTIQUETTE qui dit ce qu'il y a dans le colis » : une vraie étiquette douane collée sur un colis "
                  "venu de Chine (photo Wikimedia, domaine public). Elle reste pendant tout le problème."),
    dict(id="tampon-bloque", x=0.5, y=0.615, largeur=0.58, apparait_ms=15660, disparait_ms=16980, lueur="aucune", pop=1.35,
         pourquoi="« le colis est BLOQUÉ » : un tampon rouge « BLOQUÉ » s'écrase sur l'étiquette."),
    dict(id="logo-boonbuy", x=0.5, y=0.6, largeur=0.3, apparait_ms=20300, disparait_ms=21100,
         pourquoi="« comme BOONBUY » : le logo de l'agent (fourni par l'utilisateur), coins arrondis + ombre portée."),
    dict(id="bouton-lien-en-bio", x=0.5, y=0.6, largeur=0.6, apparait_ms=26195, disparait_ms=26860,
         pourquoi="« le LIEN qui est dans ma bio » : un bouton d'interface, c'est l'action demandée."),
    dict(id="icone-coupon-moins-40", x=0.5, y=0.62, largeur=0.4, apparait_ms=26895, disparait_ms=29560,
         deplacements=[{"t_ms": 27700, "x": 0.28, "y": 0.62}],
         pourquoi="« MOINS 40 % » : le coupon rouge au centre, puis il glisse à gauche…"),
    dict(id="icone-coupon-moins-500", x=0.72, y=0.62, largeur=0.4, apparait_ms=27835, disparait_ms=29560,
         pourquoi="…pour laisser la place au coupon vert « MOINS 500 $ » : les deux offres côte à côte jusqu'à la fin."),
]
for s in S:
    s["apparait_ms"], s["disparait_ms"] = M(s["apparait_ms"]), M(s["disparait_ms"])
    for d in s.get("deplacements", []):
        d["t_ms"] = M(d["t_ms"])

# ---------------------------------------------------------------- flashs (nouvel habillage, à valider)
F = [
    dict(t_ms=15660, couleur="#FF2A1F", pic=18, montee_ms=60, descente_ms=520,
         pourquoi="« BLOQUÉ » : bref voile rouge d'alerte, en même temps que le zoom serré, l'interdit et le son d'erreur."),
    dict(t_ms=17015, couleur="#FFFFFF", pic=30, montee_ms=40, descente_ms=380,
         pourquoi="« Je te rassure » : flash blanc sur la coupe, il marque le retournement (on passe du problème à la solution)."),
]
for f in F:
    f["t_ms"] = M(f["t_ms"])

# ---------------------------------------------------------------- sound design
X = [
    dict(id="impact-doux", t_ms=680, sous_voix_db=14,
         pourquoi="Choc de l'accroche (« REP ») : impact grave et doux, synchronisé avec le zoom punch."),
    dict(id="apparition", t_ms=2570, pourquoi="Premier téléphone (« plein ») : pop léger."),
    dict(id="minimal-pop-click-ui-3-198303", t_ms=2890, sous_voix_db=15,
         pourquoi="Les deux téléphones suivants : un seul petit clic, plus bas et plus sec, pour la cascade."),
    dict(id="cinematic-ease-out-1", t_ms=5190, calage="debut", sous_voix_db=13,
         pourquoi="Zoom de la promesse (courbe ease-out) : Motion SFX de la même courbe, le son épouse la caméra."),
    dict(id="pop-bloup", t_ms=7685, sous_voix_db=13, pourquoi="Apparition de l'article : pop rond."),
    dict(id="beep", t_ms=8625, calage="debut", sous_voix_db=17,
         pourquoi="Code-barres : bip de scanner, très bas (son pur, il perce vite)."),
    dict(id="paper-ease-out-1", t_ms=9785, calage="debut", sous_voix_db=13,
         pourquoi="La déclaration : bruit de papier qui suit le pop du document."),
    dict(id="jug-pop-3-186888", t_ms=11050, sous_voix_db=12, pourquoi="Apparition de l'étiquette."),
    dict(id="punch", t_ms=15700, sous_voix_db=12,
         pourquoi="« bloqué » : le coup sourd du tampon qui s'écrase, avec le flash rouge et le zoom serré."),
    dict(id="cinematic-ease-out-2", t_ms=17140, calage="debut", sous_voix_db=15,
         pourquoi="Zoom lent du retournement : souffle doux de la même courbe, plus bas que celui de la promesse."),
    dict(id="cinemear-graphix-pop-finger-drum-on-a-tiny-vase", t_ms=20300, sous_voix_db=13,
         pourquoi="Apparition du logo Boonbuy : pop net et court."),
    dict(id="impact-doux", t_ms=23600, sous_voix_db=15,
         pourquoi="« c'est TOUJOURS PAS la fin de la REP » : le même impact que l'accroche, rappel sonore de la phrase du début."),
    dict(id="click-02", t_ms=26195, calage="debut", sous_voix_db=13, pourquoi="« le lien dans ma bio » : clic, on appelle à cliquer."),
    dict(id="cash-register-3", t_ms=26895, sous_voix_db=13, pourquoi="« -40 % » : caisse enregistreuse, c'est l'argent économisé."),
    dict(id="coins", t_ms=27835, calage="debut", pourquoi="« -500 $ » : pièces, deuxième gain, son différent du premier."),
]
for x in X:
    x["t_ms"] = M(x["t_ms"])

# ---------------------------------------------------------------- sous-titres
brut = json.loads((ICI / ".mots-dyn.json").read_text(encoding="utf-8"))
mots = []
for w in brut:
    m = w["mot"]
    if m.startswith("'") and mots:            # apostrophes : « s » + « 'il » -> « s'il »
        mots[-1]["mot"] += m
        mots[-1]["fin_ms"] = w["fin_ms"]
        continue
    mots.append({"mot": m, "debut_ms": w["debut_ms"], "fin_ms": w["fin_ms"]})


def fusion(i, n, texte):
    mots[i:i + n] = [{"mot": texte, "debut_ms": mots[i]["debut_ms"], "fin_ms": mots[i + n - 1]["fin_ms"]}]


REMPLACE = {"A": "À", "bref": "Bref,", "rep": "REP", "bio": "bio,", "coupons": "coupon", "livraison": "livraison."}
i = 0
while i < len(mots):
    m = mots[i]["mot"]
    nxt = [x["mot"] for x in mots[i + 1:i + 3]]
    if m == "tu" and nxt[:1] == ["as"]:
        fusion(i, 2, "t'as")
    elif m == "moins" and nxt[:2] == ["40", "%"]:
        fusion(i, 3, "-40%")
    elif m == "moins" and nxt[:2] == ["500", "dollars"]:
        fusion(i, 3, "-500$")
    elif m.lower().startswith(("boon", "boom", "boun")):
        mots[i]["mot"] = "Boonbuy"            # orthographe exacte donnée par l'utilisateur
    else:
        mots[i]["mot"] = REMPLACE.get(m, m)
    i += 1

# première parole de chaque phrase = attaque réelle ; au moins 90 ms entre deux apparitions
# (Whisper place mal le premier mot d'une prise) : on retrouve les premiers mots dans l'ordre du montage
PREMIERS = ["c'est", "vous", "à", "en", "et", "je", "les", "bref,"]
j = 0
for r, p in zip(tl["reperes"], PREMIERS):
    while j < len(mots) and mots[j]["mot"].lower() != p:
        j += 1
    if j == len(mots):
        raise SystemExit(f"premier mot introuvable : {r['nom']}")
    mots[j]["debut_ms"] = r["attaque_ms"]
    j += 1
for j in range(1, len(mots)):
    mots[j]["debut_ms"] = max(mots[j]["debut_ms"], mots[j - 1]["debut_ms"] + 90)
for j in range(len(mots) - 1):
    mots[j]["fin_ms"] = max(mots[j]["debut_ms"] + 60, min(mots[j]["fin_ms"], mots[j + 1]["debut_ms"]))

LIGNES = [
    "C'est la fin", "de la REP,", "le 1er novembre.",
    "Vous avez sûrement", "dû voir plein", "de TikTok concernant", "le 1er novembre", "et la fin de la REP",
    "et je vous explique", "ça maintenant.",
    "À partir", "du 1er novembre,", "chaque article", "doit avoir", "un identifiant produit", "sur la déclaration.",
    "En gros,", "ce sera une étiquette", "qui dit exactement", "ce qu'il y a", "dans le colis.",
    "Et s'il n'y a pas", "cette étiquette", "ou que la déclaration", "est fausse,", "le colis est bloqué",
    "et reste", "à la frontière.",
    "Je te rassure", "tout de suite,", "c'est pas toi", "qui remplis ça,", "c'est ton agent", "qui s'en occupe.",
    "Les agents", "comme Boonbuy", "ont déjà trouvé", "des solutions", "à ce problème,", "donc ne vous",
    "inquiétez pas.",
    "Bref,", "c'est toujours pas", "la fin de la REP", "et si tu veux", "commander", "en t'inscrivant",
    "avec le lien", "qui est dans ma bio,", "t'as -40%", "et -500$ en coupon", "sur ta livraison.",
]
n = sum(len(l.split()) for l in LIGNES)
if n != len(mots):
    for j, m in enumerate(mots):
        print(j, m["mot"])
    raise SystemExit(f"lignes : {n} mots, transcription : {len(mots)}")
k = 0
for l in LIGNES:  # le texte affiché est celui des lignes (orthographe, ponctuation)
    for t in l.split():
        mots[k]["mot"] = t
        k += 1

CLES = [{"mot": "REP", "t_ms": 680}, {"mot": "identifiant", "t_ms": 8625}, {"mot": "bloqué", "t_ms": 15660},
        {"mot": "agent", "t_ms": 18895}, {"mot": "toujours", "t_ms": 23615}, {"mot": "-40%", "t_ms": 26895},
        {"mot": "-500$", "t_ms": 27835}]
for c in CLES:
    c["t_ms"] = M(c["t_ms"])

plan = {
    "nom": "derush-img2950", "format": "9:16", "export": {"resolution": "1080p", "fps": 30},
    "_notes": "v3 : 50 ms entre phrases, source 1440p, zooms qui cadrent, ombre diffuse au lieu de la lueur jaune, "
              "flashs, sound design enrichi, Boonbuy.",
    "voix": {"fichier": (ICI / "rushes" / "voix-dyn.wav").as_posix(), "volume": 1.0},
    "lueur_defaut": "ombre",
    # musique : son TikTok choisi par l'utilisateur, ~20 dB sous la voix (repère W3C / pratique
    # TikTok : -18 à -25 dB). Calage : la retombée du beat (28 s) tombe sur le problème (« Et s'il n'y a pas cette
    # étiquette ») et le drop (32 s) sur le retournement « Je te rassure » -> début de lecture à 32 000 - attaque(Rassure).
    "musique": {"id": "gravitational-forces-by-blaumodus-muffled-tiktok-extended-version",
                "source_debut_ms": 2000 - R["TikTok"]["attaque_ms"], "volume": 0.12, "volume_sous_voix": 0.08,
                "fondu_entree_ms": 120, "fondu_sortie_ms": 700,
                "pourquoi": "Son TikTok choisi par l'utilisateur (déjà étouffé : pas d'EQ). Son drop (2 s) tombe sur la fin "
                            "de l'accroche ; ~20 dB sous la voix."},
    "clips": clips, "stickers": S, "flashs": F, "sfx": X,
    "sous_titres": {"preset": "sover8-pop", "mots": mots, "cles": CLES, "lignes": LIGNES,
                    "pourquoi": "Découpe au sens, écrite à la main ; couleur sur 7 mots : le choc (REP), la règle "
                                "(identifiant), la conséquence (bloqué), la solution (agent), la chute (toujours) et l'offre (-40 %, -500 $)."},
}
(ICI / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"plan.json : {len(clips)} plans, {len(S)} objets, {len(F)} flashs, {len(X)} SFX, {len(mots)} mots")
