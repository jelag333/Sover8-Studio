"""« Installer » un élément : copie dans la bibliothèque, analyse, fiche d'usage, aperçus."""
import json
import shutil
from pathlib import Path

from . import analyse, catalogue as C
from .config import APERCUS, BIB, INBOX, TYPES, AUDIO_EXT, VIDEO_EXT, say

IMAGE_EXT = TYPES["image"][1]
FONT_EXT = TYPES["police"][1]
# nom de sous-dossier de A-AJOUTER -> type
HINTS = {"sfx": "sfx", "sons": "sfx", "bruitages": "sfx", "musique": "musique", "musiques": "musique",
         "music": "musique", "ambiance": "ambiance", "ambiances": "ambiance", "vfx": "vfx", "overlays": "vfx",
         "videos": "vfx", "images": "image", "logos": "image", "stickers": "image", "polices": "police",
         "fonts": "police", "textes-fx": "texte-fx", "sous-titres": "sous-titres"}


def hint_from_path(path):
    for part in reversed(Path(path).parent.parts):
        h = HINTS.get(C.slug(part))
        if h:
            return h
    return None


def add_preset(cat, path, type_hint=None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    typ = data.get("type") or type_hint
    if typ not in ("texte-fx", "sous-titres"):
        raise ValueError("un preset JSON doit avoir \"type\": \"texte-fx\" ou \"sous-titres\"")
    eid = data.get("id") or C.slug(Path(path).stem)
    data["id"] = eid
    dest = BIB / TYPES[typ][0] / f"{eid}.json"
    if Path(path).resolve() != dest.resolve():
        dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    entry = C.get(cat, eid) or {}
    entry.update({
        "id": eid, "type": typ, "nom": data.get("nom", eid), "fichier": dest.relative_to(BIB).as_posix(),
        "tags": data.get("tags", []), "usage": data.get("usage", {}), "statut": data.get("statut", "valide"),
        "description": data.get("description", ""), "police": data.get("police"),
        "ajoute_le": entry.get("ajoute_le") or C.now(), "licence": data.get("licence", "création studio"),
        "apercus": entry.get("apercus", {}),
    })
    C.upsert(cat, entry)
    return entry


def add_file(cat, path, type_hint=None, tags=(), nom=None, licence="", move=False):
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".json":
        return add_preset(cat, path, type_hint)
    digest = C.sha256(path)
    dup = C.by_hash(cat, digest)
    if dup:
        say(f"  = déjà installé : {path.name} -> {dup['id']}")
        if move:
            path.unlink()
        return dup
    hint = type_hint or hint_from_path(path)
    if ext in AUDIO_EXT:
        typ, role, auto_tags, tech = analyse.analyse_audio(path, hint if hint in ("sfx", "musique", "ambiance") else None)
    elif ext in VIDEO_EXT:
        typ, role, auto_tags, tech = analyse.analyse_video(path)
    elif ext in IMAGE_EXT:
        typ, role, auto_tags, tech = analyse.analyse_image(path)
    elif ext in FONT_EXT:
        typ, role, auto_tags, tech = analyse.analyse_font(path)
    else:
        raise ValueError(f"format non géré : {ext}")
    eid = C.unique_id(cat, C.slug(nom or path.stem))
    dest = BIB / TYPES[typ][0] / f"{eid}{ext}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    (shutil.move if move else shutil.copy2)(str(path), str(dest))
    entry = {
        "id": eid, "type": typ, "nom": nom or path.stem, "fichier": dest.relative_to(BIB).as_posix(),
        "original": path.name, "sha256": digest, "ajoute_le": C.now(),
        "tags": list(dict.fromkeys(list(tags) + auto_tags)), "tech": tech,
        "usage": analyse.usage_for(role, tech), "statut": "auto", "licence": licence,
    }
    entry["apercus"] = analyse.make_previews(entry, dest, APERCUS)
    C.upsert(cat, entry)
    u = entry["usage"]
    dur = f"  {tech['duree_ms']} ms" if tech.get("duree_ms") else ""
    say(f"  + {eid}  [{typ} / {u['role']}]{dur}")
    return entry


def iter_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and not f.name.startswith(".") and f.suffix.lower() not in (".txt", ".md", ".ini", ".db"):
                    yield f
        elif p.is_file():
            yield p


def add_many(paths, type_hint=None, tags=(), licence="", move=False):
    cat = C.load()
    ok, errors = [], []
    for f in iter_files(paths or [INBOX]):
        try:
            ok.append(add_file(cat, f, type_hint, tags, licence=licence, move=move or not paths))
        except Exception as e:  # un fichier cassé ne bloque pas les autres
            errors.append((f, str(e)))
            say(f"  ! {f.name} : {e}")
    C.save(cat)
    return ok, errors
