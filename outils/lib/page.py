"""Génère la page catalogue (locale : catalogue.html ; en ligne : .studio-work/publication/)."""
import base64
import collections
import json
from pathlib import Path

from . import catalogue as C
from .config import BIB, PAGE, RECETTES, ROOT

TEMPLATE = Path(__file__).with_name("page_template.html")
MAX_ONLINE = 15 * 1024 * 1024  # limite par fichier publié
MAX_ENTRIES = 250               # limite de fichiers par publication (255) moins une marge
MAX_FONT_INLINE = 450 * 1024
AUDIO_TYPES = ("sfx", "musique", "ambiance")
PRIVATE = ("original", "sha256", "alias")


def _font_faces(cat):
    css = []
    for e in C.find(cat, "police"):
        p = BIB / e["fichier"]
        if p.exists() and p.stat().st_size <= MAX_FONT_INLINE:
            b64 = base64.b64encode(p.read_bytes()).decode()
            fmt = "opentype" if p.suffix.lower() == ".otf" else "truetype"
            css.append(f"@font-face{{font-family:'lib-{e['id']}';src:url(data:font/{p.suffix[1:]};base64,{b64}) format('{fmt}');font-display:swap}}")
    return "\n".join(css)


def _score(e):
    tags = set(e.get("tags", []))
    s = 2 * (e.get("statut") == "valide") + 2 * ("favori" in tags) + (e.get("confiance") == "haute")
    s += 1 if e.get("tech", {}).get("duree_ms", 0) <= 4000 else 0
    return s


def online_selection(cat, budget):
    """Sons écoutables en ligne : les meilleurs de chaque rôle, à tour de rôle (un thème Motion à la fois)."""
    pools = collections.defaultdict(list)
    for e in cat["elements"]:
        tags = set(e.get("tags", []))
        if e["type"] not in AUDIO_TYPES or tags & {"droits-a-verifier", "vulgaire"}:
            continue
        if not (e.get("apercus") or {}).get("audio"):
            continue
        pools[e.get("usage", {}).get("role", "autre")].append(e)
    for role, items in pools.items():
        items.sort(key=lambda e: (-_score(e), e["id"]))
        if role == "motion":  # un son par thème avant d'en prendre un deuxième
            seen, first, rest = set(), [], []
            for e in items:
                (rest if e.get("famille") in seen else first).append(e)
                seen.add(e.get("famille"))
            pools[role] = first + rest
    chosen, i = [], 0
    while len(chosen) < budget and any(i < len(v) for v in pools.values()):
        for role in sorted(pools, key=lambda r: -len(pools[r])):
            if i < len(pools[role]) and len(chosen) < budget:
                chosen.append(pools[role][i]["id"])
        i += 1
    return set(chosen)


def _data(cat, online):
    items, files = [], {}
    fixed = sum(1 for e in cat["elements"] if e["type"] not in AUDIO_TYPES) * 3
    playable = online_selection(cat, (MAX_ENTRIES - fixed) // 2) if online else None
    for e in cat["elements"]:
        e = dict(e)
        src = BIB / e["fichier"]
        rel = "bibliotheque/" + e["fichier"]
        size = src.stat().st_size if src.exists() else 0
        e["taille"] = size
        e["dl"] = rel
        ap = {}
        for k, v in (e.get("apercus") or {}).items():
            if (BIB / "apercus" / v).exists():
                ap[k] = "bibliotheque/apercus/" + v
        if online:
            for k in PRIVATE:
                e.pop(k, None)
            if e["type"] in AUDIO_TYPES:
                if e["id"] in playable:  # aperçu MP3 (écoute + téléchargement) et forme d'onde
                    ap = {k: v for k, v in ap.items() if k in ("audio", "onde")}
                    e["dl"] = ap.get("audio")
                    e["dl_note"] = "aperçu MP3 (l'original est dans le catalogue local)"
                else:
                    ap, e["dl"] = {}, None
            elif size > MAX_ONLINE:
                e["dl"] = None
            else:
                files[rel] = src
            for v in ap.values():
                files[v] = BIB / v.removeprefix("bibliotheque/")
        e["apercus"] = ap
        e.pop("sha256", None)
        items.append(e)
    recettes = []
    for r in sorted(RECETTES.glob("*.json")):
        try:
            recettes.append(json.loads(r.read_text(encoding="utf-8")))
        except ValueError:
            pass
    return {"maj": cat.get("maj"), "elements": items, "recettes": recettes, "enLigne": online}, files


def generate(online=False):
    cat = C.load()
    data, files = _data(cat, online)
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("/*__FONTS__*/", _font_faces(cat))
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    if not online:
        PAGE.write_text("<!doctype html>\n<html lang=\"fr\">\n" + html + "\n</html>\n", encoding="utf-8")
        return PAGE
    out = ROOT / ".studio-work" / "publication"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    manifest = {k: str(v.relative_to(ROOT)).replace("\\", "/") for k, v in files.items()}
    (out / "fichiers.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return out / "index.html"
