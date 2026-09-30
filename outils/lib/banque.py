"""Import d'une banque de sons entière : dédoublonnage, classement par nom/dossier/acoustique, analyse parallèle."""
import collections
import json
import os
import re
import shutil
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from . import analyse, catalogue as C
from .config import APERCUS, BIB, ROOT, ffmpeg_path, ffprobe, run, say

AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".aif", ".aiff"}
VIDEO = {".mp4", ".mov", ".avi", ".m4v"}
FORMAT_PRIO = {".wav": 0, ".aif": 1, ".aiff": 1, ".flac": 2, ".mp3": 3, ".m4a": 4, ".aac": 5, ".ogg": 6,
               ".mp4": 7, ".mov": 8, ".m4v": 8, ".avi": 9}
EXTRACT = ROOT / ".studio-work" / "banque-extrait"

# --------------------------------------------------------------- taxonomie
# (rôle, mots-clés) : testés sur le nom du fichier puis sur les dossiers ; le premier rôle trouvé gagne.
RULES = [
    ("meme", ["mlg", "fahhh", "10 famous", "dbz", "instant transmission", "anime wow", "censor", "censure", "windows", "facebook", "iphone", "macos", "sozeiga", "pegi", "morsay", "nypd", "london chant", "pubg", "chewbaca", "nein nein", "among us", "amongus", "impostor", "imposter", "sabotage", "mario", "fortnite", "victoire royale",
              "discord", "minecraft", "bing chilling", "get out", "smash bros", "chokbar", "spas full", "xp sound",
              "vine boom", "bruh", "oof", "windows xp", "roblox", "lemonstre"]),
    ("tambour", ["drum roll", "drumroll", "roulement", "tambour", "snare roll"]),
    ("rire", ["laugh", "rire", "applause", "applaudissement", "clap", "cheer", "crowd wow"]),
    ("pleurs", ["cry", "pleure", "sob", "weep"]),
    ("comique", ["cartoon", "funny", "stupid", "gag", "bonk", "boing", "awkward", "comical", "fail", "wimpy",
                 "cuckoo", "blushing", "squish", "sprung", "spring", "canard", "quack", "bwop", "flop", "clown",
                 "fart", "pet ", "pet-", "rot ", "burp", "ronflement", "snore", "drole", "silly", "twitch", "vein",
                 "disappointment", "depression", "party horn", "turn around", "question mark", "struggle",
                 "slide whistle", "cartoony", "hollow hit", "bamboo", "anvil", "icky", "trrrr", "confused"]),
    ("alarme", ["alarm", "alarme", "siren", "sirene", "warning"]),
    ("horreur", ["cri", "monstre", "creature", "grognement", "exorcis", "terreur", "inquietante", "etouffement", "douleur", "horror", "horreur", "scream", "creepy", "ghost", "psycho", "bloody", "evil", "demon", "zombie",
                 "doom", "dark gleam", "jumpscare", "jump scare"]),
    ("suspense", ["battement", "coeur", "dun dun", "stand off", "suspense", "tension", "tense", "stress", "heartbeat", "heart beat", "clock", "ticking",
                  "tick tock", "critical", "rattle", "mystere", "mystery", "stinger", "sting", "dramatic music"]),
    ("riser", ["riser", "uplift", "build up", "buildup", "montee", "rise", "reverse cymbal", "reverse"]),
    ("downlifter", ["downlift", "downer", "down lifter", "descente", "power down", "powerdown"]),
    ("glitch", ["glitch", "digital", "error", "static", "bug", "binary", "data", "zap", "bitcrush", "8-bit", "8bit"]),
    ("magie", ["magic", "magical", "sparkle", "scintill", "shine", "twinkle", "gleam", "fairy", "sacred",
               "teleport", "dream", "wish", "spell", "enchant", "shimmer"]),
    ("whoosh", ["whoosh", "woosh", "swoosh", "swish", "swipe", "swoop", "fly by", "flyby", "pass by", "passby",
                "camera whoosh", "swing"]),
    ("cash", ["cha ching", "cash", "coin", "coins", "money", "kaching", "ka-ching", "register", "jackpot", "gem", "treasure", "tresor"]),
    ("notification", ["confirm", "accept", "bips", "bip", "beep", "counter", "counting", "notif", "ding", "chime", "ping", "success", "correct", "win", "score", "level up",
                      "discovery", "done bell", "achievement", "reward", "strawberry", "unlock"]),
    ("explosion", ["explosion", "explode", "blast", "bomb", "kaboom", "detonat"]),
    ("arme", ["gun", "shot", "pistol", "rifle", "cannon", "flintlock", "sword", "katana", "blade", "slice", "sabre",
              "knife", "couteau", "reload", "recharge", "blaster", "laser", "tranche", "arrow", "fleche", "arme"]),
    ("impact", ["impact", "hit", "boom", "punch", "thud", "slam", "bass drop", "sub drop", "808", "kick",
                "smash", "crash", "bone crack", "cracking", "coup", "frappe", "bam", "stomp", "braam", "combat"]),
    ("pop", ["pop", "bubble", "bulle", "blop", "plop", "apparition", "appearance", "appear"]),
    ("clic", ["type delete", "hover", "ui0", "finger snap", "snap", "click", "clic", "tap", "ui ", "ui-", "ui_", "button", "bouton", "interface", "keyboard", "clavier",
              "typing", "highlighter", "mouse", "toggle", "select", "menu"]),
    ("camera", ["camera", "shutter", "photo", "flash", "polaroid"]),
    ("scratch", ["rembobin", "scratch", "rewind", "backspin", "vinyl", "record stop", "ralenti", "slow motion", "slowmo"]),
    ("transition", ["transition", "cymbal", "wipe"]),
    ("musical", ["bells", "conductor", "instrument", "piano", "guitar", "orchestral", "melodic", "melodics", "harp", "violin", "trumpet",
                 "horn", "bell", "vibraslap", "xylophone", "percussion", "gong", "marimba", "synth", "chord"]),
    ("animal", ["animal", "animaux", "bird", "oiseau", "dog", "chien", "cat ", "chat ", "cow", "vache", "horse",
                "cheval", "lion", "wolf", "loup", "sheep", "mouton", "pig", "cochon", "chicken", "poule", "goat"]),
    ("vehicule", ["car ", "voiture", "engine", "moteur", "jet", "plane", "avion", "train", "motorbike", "moto",
                  "klaxon", "rocket", "fusee", "ufo", "torpedo", "vehicule", "helicopter", "truck", "camion"]),
    ("voix", ["breath", "respiration", "voice", "voix", "parole", "speech", "whisper", "chuchot", "gasp", "sigh",
              "soupir", "hmm", "grunt"]),
    ("ambiance", ["thunder", "tonnerre", "rain", "pluie", "stream", "ruisseau", "river", "riviere", "wind ", "vent", "crowd", "city",
                  "forest", "foret", "asmr", "ocean", "waves", "vagues", "nature", "room tone", "roomtone", "night"]),
    ("bruitage", ["chain", "bicycle", "bike", "wrench", "slide", "scissors", "ciseaux", "kitchen timer", "telephone", "numero", "raccrocher", "crissement", "pneu", "clignotant", "craquelement", "machine a ecrire", "prison", "buzzer", "footstep", "pas ", "door", "porte", "glass", "verre", "bottle", "bouteille", "paper", "papier",
                  "water", "eau", "sheet", "drap", "zipper", "fermeture", "chest", "coffre", "creak", "grince",
                  "map", "dig", "repar", "rudder", "balloon", "ballon", "ink", "encre", "metal", "wood", "bois",
                  "cloth", "tissu", "quotidien", "cut", "submerge", "splash", "fire", "feu", "spin", "wheel",
                  "roue", "open", "close", "drop", "fall", "chute"]),
]
# indices par nom de dossier (quand le nom du fichier ne dit rien)
FOLDER_HINTS = {
    "04-riser": "riser", "05-woosh": "whoosh", "06-pop": "pop", "07-impact": "impact", "02-glitch": "glitch",
    "glitch": "glitch", "03-horror": "horreur", "cartoon": "comique", "pet-et-rot": "comique",
    "rire-applaudissement": "rire", "pleure": "pleurs", "roulement-de-tambour": "tambour",
    "suspense-stress": "suspense", "vehicule": "vehicule", "animaux": "animal", "bruitage-arme": "arme",
    "combat": "impact", "explosion": "explosion", "bruitage-parole": "voix", "bruitage-quotidien": "bruitage",
    "bruitages-de-transition": "transition", "epic-transitions": "transition", "08-instrument": "musical",
    "ui-sound-effects": "clic", "interface": "clic", "01-effets-sonores": None, "00-autres": None,
}
FAMILLES = {  # dossier -> famille lisible
    "04-riser": "Risers", "05-woosh": "Whoosh", "06-pop": "Pop", "07-impact": "Impacts", "02-glitch": "Glitch",
    "glitch": "Glitch", "03-horror": "Horreur", "cartoon": "Cartoon", "pet-et-rot": "Pets et rots",
    "rire-applaudissement": "Rires et applaudissements", "pleure": "Pleurs", "roulement-de-tambour": "Tambours",
    "suspense-stress": "Suspense et stress", "vehicule": "Véhicules", "animaux": "Animaux",
    "bruitage-arme": "Armes", "combat": "Combat", "explosion": "Explosions", "bruitage-parole": "Voix et parole",
    "bruitage-quotidien": "Bruitages du quotidien", "bruitages-de-transition": "Transitions",
    "epic-transitions": "Transitions épiques", "08-instrument": "Instruments", "00-autres": "Divers",
    "01-effets-sonores": "Effets sonores", "buitage-autre": "Bruitages divers", "ui-sound-effects": "Interface (UI)",
    "450-cinematic-sound-effects": "Cinématique", "400-tranding-sfx": "Tendance (réseaux)", "336-sfx": "Pack 336 SFX",
    "126-mixed-sound-effcts": "Pack mixte", "1300-sfx": "Motion SFX",
}
EASINGS = ["wheel ease in", "wheel ease out", "wheel easy ease", "ease in", "ease out", "easy ease", "bounce",
           "cubic", "linear", "hit", "shake", "swinging"]
EASING_FR = {"ease in": "accélère (ease in)", "ease out": "ralentit à l'arrivée (ease out)",
             "easy ease": "accélère puis ralentit (easy ease)", "bounce": "rebond", "cubic": "courbe cubique",
             "linear": "vitesse constante", "hit": "arrivée frappée", "shake": "secousse", "swinging": "balancier",
             "wheel ease in": "rotation qui accélère", "wheel ease out": "rotation qui ralentit",
             "wheel easy ease": "rotation douce"}
MEME_WORDS = {"meme"}
USAGE_EXTRA = {
    "motion": dict(
        quand="Son conçu pour un mouvement animé précis (thème {theme}, courbe « {courbe} ») : titres, logos, éléments graphiques qui bougent.",
        eviter="Le poser sur une coupe sans mouvement à l'image ; mélanger plusieurs thèmes dans la même séquence.",
        placement="Début du son = début du mouvement ; le pic ({pic_ms} ms) tombe sur l'arrivée de l'animation.",
        calage="debut", volume=0.35),
    "meme": dict(quand="Référence humoristique connue (réseaux sociaux, jeux vidéo) pour une chute ou une réaction.",
                 eviter="Contenus de marque sérieux ; droits d'auteur à vérifier pour un usage commercial.",
                 placement="Juste après la chute ou sur la réaction ; couper ou baisser la musique au même moment.",
                 calage="debut", volume=0.4),
    "comique": dict(quand="Gag, maladresse, réaction exagérée, moment gênant, chute d'une blague.",
                    eviter="Sujets sérieux ; enchaîner plusieurs gags sonores.",
                    placement="Sur l'action comique (pic à {pic_ms} ms) ; laisser un blanc juste avant.",
                    calage="pic", volume=0.4),
    "horreur": dict(quand="Jumpscare, révélation inquiétante, ambiance sombre ou angoissante.",
                    eviter="Contenus légers ou enfantins.", placement="Pic ({pic_ms} ms) sur la révélation.",
                    calage="pic", volume=0.45),
    "suspense": dict(quand="Faire monter l'attente : avant une révélation, un résultat, un choix.",
                     eviter="Sous une explication importante (distrait).",
                     placement="Démarre quelques secondes avant la révélation, se coupe net dessus.",
                     calage="debut", volume=0.3),
    "magie": dict(quand="Apparition magique, transformation, avant/après, révélation positive, brillance.",
                  eviter="Contextes réalistes ou sérieux.", placement="Pic ({pic_ms} ms) sur l'apparition.",
                  calage="pic", volume=0.35),
    "tambour": dict(quand="Annonce d'un résultat, d'un classement, d'une révélation (roulement puis coup final).",
                    eviter="Plusieurs fois dans la même vidéo.", placement="La fin du roulement tombe sur la révélation.",
                    calage="fin", volume=0.4),
    "pleurs": dict(quand="Réaction triste exagérée (souvent comique).", eviter="Vrai sujet dramatique.",
                   placement="Sur la réaction.", calage="debut", volume=0.35),
    "alarme": dict(quand="Alerte, danger, erreur grave, urgence, « attention ».", eviter="Longtemps sous la voix.",
                   placement="Sur l'apparition du danger ; 1 à 2 s suffisent.", calage="debut", volume=0.3),
    "explosion": dict(quand="Explosion, destruction, révélation énorme, transition très forte.",
                      eviter="Vidéos calmes ; plus d'une par minute.", placement="Pic ({pic_ms} ms) sur l'image clé.",
                      calage="pic", volume=0.5),
    "arme": dict(quand="Tir, lame, coupe nette, « slice » sur un texte ou une transition tranchante.",
                 eviter="Contenus sensibles.", placement="Pic ({pic_ms} ms) sur le coup ou la coupe.",
                 calage="pic", volume=0.4),
    "musical": dict(quand="Ponctuation musicale : sting, note, cloche, instrument isolé.",
                    eviter="Conflit de tonalité avec la musique de fond.", placement="Sur le moment ponctué.",
                    calage="debut", volume=0.35),
    "animal": dict(quand="Présence d'un animal à l'image ou gag animalier.", eviter="Animal absent de l'image (sauf gag).",
                   placement="Synchronisé avec l'animal.", calage="debut", volume=0.35),
    "vehicule": dict(quand="Véhicule à l'image, vitesse, passage, décollage.", eviter="—",
                     placement="Synchronisé avec le mouvement du véhicule.", calage="debut", volume=0.35),
    "voix": dict(quand="Respiration, soupir, réaction vocale non verbale.", eviter="Remplacer une vraie parole.",
                 placement="Dans un blanc de la voix principale.", calage="debut", volume=0.35),
    "bruitage": dict(quand="Bruit réaliste d'un objet ou d'une action visible (porte, verre, papier, eau…).",
                     eviter="Objet absent de l'image.", placement="Synchronisé sur l'action à l'image (pic {pic_ms} ms).",
                     calage="pic", volume=0.35),
}
analyse.USAGE.update(USAGE_EXTRA)


def norm(s):
    return " " + C.slug(s).replace("-", " ") + " "


def find_role(text):
    """Mot-clé en mot entier ; les mots-clés de 5 lettres et plus valent aussi en sous-chaîne (whooshes, swishes)."""
    t = norm(text)
    for role, keys in RULES:
        for k in keys:
            ks = C.slug(k).replace("-", " ")
            if f" {ks} " in t or (len(ks) >= 5 and ks in t):
                return role
    return None


def clean_name(stem):
    s = re.sub(r"[_]+", " ", stem)
    s = re.sub(r"(?i)\b(sound effects?|sfx|free( to use)?|hd|no copyright|effet sonore|bruitages?|#\S+|original|"
               r"version|audio extraction terminée|normal)\b", " ", s)
    s = re.sub(r"\s*-\s*$|^\s*-\s*", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" -_.")
    return s[:80] or stem


# --------------------------------------------------------------- inventaire
def extract_nested_zips(root):
    """Extrait les zip imbriqués qui contiennent des sons absents du dossier (le gros zip miroir est ignoré)."""
    extra = []
    existing = {p.name.lower() for p in root.rglob("*") if p.is_file()}
    for z in root.rglob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            names = [n for n in zf.namelist() if Path(n).suffix.lower() in AUDIO | VIDEO]
            missing = [n for n in names if Path(n).name.lower() not in existing]
            if not missing or len(missing) > 0.5 * len(names) and len(names) > 500:
                continue  # rien de neuf, ou archive miroir d'un dossier déjà présent
            dest = EXTRACT / C.slug(z.stem)
            for n in missing:
                target = dest / n
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(n) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
                extra.append((target, z.parent))
    return extra


def folder_parts(path, root):
    try:
        rel = path.parent.relative_to(root).parts
    except ValueError:
        rel = path.parent.parts[-3:]
    return [p for p in rel if p.lower() not in ("(preview)", "preview", "3000+ premium sfx pack", "+3000 sfx")]


def scan(root):
    root = Path(root)
    files = [(p, p.parent) for p in root.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO | VIDEO]
    files += extract_nested_zips(root)
    report = {"trouves": len(files)}
    # 1) copies exactes
    by_hash = collections.defaultdict(list)
    for p, ctx in files:
        by_hash[C.sha256(p)].append((p, ctx))
    report["copies_exactes"] = sum(len(v) - 1 for v in by_hash.values())
    cands = []
    for digest, group in by_hash.items():
        group.sort(key=lambda g: (-len(folder_parts(g[1] / g[0].name, root)), FORMAT_PRIO.get(g[0].suffix.lower(), 9)))
        p, ctx = group[0]
        aliases = sorted({g[0].stem for g in group})
        folders = sorted({"/".join(folder_parts(g[1] / g[0].name, root)) for g in group})
        cands.append({"src": p, "ctx": ctx, "sha256": digest, "alias": aliases, "dossiers": folders})
    # 2) même son dans plusieurs formats (x.wav / x.mp3, aperçu .mp4 d'un .wav)
    by_key = collections.defaultdict(list)
    for c in cands:
        stem = c["src"].stem.strip()
        if re.search(r"\[.+\]$", stem):  # Motion SFX « Thème [Courbe] » : même son quel que soit le dossier
            key = ("motion", C.slug(stem))
        else:
            key = ("/".join(folder_parts(c["ctx"] / c["src"].name, root)).lower(), C.slug(stem))
        by_key[key].append(c)
    kept = []
    for group in by_key.values():
        group.sort(key=lambda c: FORMAT_PRIO.get(c["src"].suffix.lower(), 9))
        best = group[0]
        for other in group[1:]:
            best["alias"] = sorted(set(best["alias"]) | set(other["alias"]))
        kept.append(best)
    report["memes_sons_autre_format"] = len(cands) - len(kept)
    report["uniques"] = len(kept)
    return kept, report


# --------------------------------------------------------------- classement
def classify(c, root):
    parts = folder_parts(c["ctx"] / c["src"].name, root)
    slugs = [C.slug(p) for p in parts]
    stem = c["src"].stem
    famille = next((FAMILLES[s] for s in reversed(slugs) if s in FAMILLES), None)
    theme = courbe = None
    m = re.match(r"^(.*?)\s*\[(.+?)\]\s*$", stem)
    if m and ("1300-sfx" in slugs or any(e in m.group(2).lower() for e in EASINGS)):
        theme = m.group(1).strip()
        cb = m.group(2).lower()
        courbe = next((e for e in EASINGS if cb.startswith(e)), cb)
        famille = f"Motion SFX : {theme}"
        role = "motion"
    else:
        role = find_role(stem) or find_role(" ".join(c["alias"]))
        if not role:
            for s in reversed(slugs):
                if FOLDER_HINTS.get(s):
                    role = FOLDER_HINTS[s]
                    break
        if not role:
            role = find_role(" ".join(parts))
    if not famille:
        famille = parts[-1] if parts else "Banque (racine)"
    tags = [C.slug(p) for p in parts if len(C.slug(p)) > 1]
    tags += analyse.words_of(stem)[:6]
    if theme:
        tags += ["motion", C.slug(theme), "courbe-" + C.slug(courbe)]
    if re.search(r"(?i)f[u*\s]?ck|\b(fdp|bitch|couilles?|merde|putain|salope|niquer?|ntm|pute|connard|encul\w*)\b|suce ma bite|ta m[eè]re", (stem + " " + " ".join(c["alias"])).replace("_", " ")):
        tags.append("vulgaire")
    if re.search(r"(?i)favorite|favori|strong", stem):
        tags.append("favori")
    if role == "meme" or re.search(r"(?i)fortnite|mario|among ?us|minecraft|discord|smash|roblox", stem):
        tags.append("droits-a-verifier")
    return {"role": role, "famille": famille, "theme": theme, "courbe": courbe,
            "tags": list(dict.fromkeys(t for t in tags if t))}


# --------------------------------------------------------------- traitement (processus parallèles)
def _audio_codec(path):
    info = ffprobe(str(path))
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return a["codec_name"] if a else None


def process(job):
    src, dest = Path(job["src"]), Path(job["dest"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in VIDEO:  # aperçu vidéo : on ne garde que le son
        codec = _audio_codec(src)
        if not codec:
            raise RuntimeError("vidéo sans son")
        args = ["-c:a", "copy"] if dest.suffix == ".m4a" else ["-c:a", "pcm_s16le"]
        r = run([ffmpeg_path(), "-nostdin", "-y", "-v", "error", "-i", src, "-vn", *args, dest])
        if r.returncode:
            raise RuntimeError(r.stderr[:200])
    else:
        shutil.copy2(src, dest)
    hint = job["cls"]["role"]
    typ, role, auto_tags, tech = analyse.analyse_audio(dest, "sfx")
    dur = tech["duree_ms"]
    if dur > 25000 and hint in (None, "ambiance"):
        typ = "ambiance"
    final_role = hint or role
    if typ == "ambiance" and final_role not in ("ambiance", "suspense", "horreur"):
        final_role = "ambiance"
    shape_ok = {"whoosh": ("en-cloche", "tenue"), "impact": ("percussive",), "riser": ("montante",),
                "pop": ("percussive",), "clic": ("percussive",), "explosion": ("percussive", "tenue")}
    confiance = "haute" if hint and (hint not in shape_ok or tech["forme"] in shape_ok[hint]) else \
        "moyenne" if hint else "basse"
    usage = analyse.usage_for(final_role, tech)
    cls = job["cls"]
    if final_role == "motion":
        usage["quand"] = usage["quand"].format(theme=cls["theme"], courbe=EASING_FR.get(cls["courbe"], cls["courbe"]))
    tags = list(dict.fromkeys(cls["tags"] + [t for t in auto_tags if t in ("court", "moyen", "long", "grave", "aigu", "medium")]))
    entry = {
        "id": job["id"], "type": typ, "nom": job["nom"], "fichier": dest.relative_to(BIB).as_posix(),
        "original": str(src), "alias": job["alias"][:6], "sha256": job["sha256"], "ajoute_le": C.now(),
        "famille": cls["famille"], "tags": tags, "tech": tech, "usage": usage,
        "statut": "valide" if confiance == "haute" else "auto", "confiance": confiance, "licence": job["licence"],
    }
    if cls["courbe"]:
        entry["courbe"] = cls["courbe"]
    entry["apercus"] = analyse.make_previews(entry, dest, APERCUS)
    return entry


def import_bank(root, licence, workers=None, dry=False, limit=None):
    root = Path(root)
    say(f"Inventaire de {root}…")
    cands, report = scan(root)
    say(json.dumps(report, ensure_ascii=False))
    cat = C.load()
    known = {e.get("sha256") for e in cat["elements"]}
    jobs, ids = [], {e["id"] for e in cat["elements"]}
    for c in cands:
        if c["sha256"] in known:
            continue
        cls = classify(c, root)
        stem = c["src"].stem
        base = C.slug(clean_name(stem))
        generic = not re.search(r"[a-z]{3,}", base) or re.fullmatch(r"(impact|pop|riser|woosh|whoosh|glitch|sfx|son)(-\d+)*", base)
        if generic:
            base = C.slug(f"{cls['famille']} {stem}")
        base = base[:60].strip("-")
        eid, n = base, 2
        while eid in ids:
            eid, n = f"{base}-{n}", n + 1
        ids.add(eid)
        ext = c["src"].suffix.lower()
        if ext in VIDEO:
            ext = ".m4a" if _audio_codec(c["src"]) == "aac" else ".wav"
        typ_dir = "sfx"
        jobs.append({"src": str(c["src"]), "dest": str(BIB / typ_dir / f"{eid}{ext}"), "id": eid,
                     "nom": clean_name(f"{cls['theme']} {cls['courbe']}" if cls["theme"] else stem),
                     "alias": c["alias"], "sha256": c["sha256"], "cls": cls, "licence": licence})
    if limit:
        jobs = jobs[:limit]
    roles = collections.Counter(j["cls"]["role"] or "(acoustique)" for j in jobs)
    say(f"{len(jobs)} nouveaux sons à installer. Rôles pressentis : {dict(roles.most_common())}")
    if dry:
        return jobs, report
    done, errors = [], []
    with ProcessPoolExecutor(max_workers=workers or max(2, (os.cpu_count() or 4) - 2)) as ex:
        futs = {ex.submit(process, j): j for j in jobs}
        for i, f in enumerate(as_completed(futs), 1):
            j = futs[f]
            try:
                done.append(f.result())
            except Exception as e:
                errors.append({"src": j["src"], "erreur": str(e)[:200]})
            if i % 100 == 0 or i == len(jobs):
                say(f"  {i}/{len(jobs)}")
                for e in done[-100:]:
                    C.upsert(cat, e)
                C.save(cat)  # sauvegarde régulière : une interruption ne perd pas le travail fait
    for e in done:
        C.upsert(cat, e)
    C.save(cat)
    report.update({"installes": len(done), "erreurs": errors})
    (ROOT / ".studio-work" / "banque-rapport.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str),
                                                             encoding="utf-8")
    return done, report
