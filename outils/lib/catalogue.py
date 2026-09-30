"""Lecture/écriture de bibliotheque/catalogue.json : une fiche par élément."""
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import unicodedata

from .config import CATALOGUE


def now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "element"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load():
    if not CATALOGUE.exists():
        return {"version": 1, "maj": now(), "elements": []}
    with open(CATALOGUE, encoding="utf-8") as f:
        return json.load(f)


def save(cat):
    cat["maj"] = now()
    cat["elements"].sort(key=lambda e: (e["type"], e["id"]))
    CATALOGUE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=CATALOGUE.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CATALOGUE)


def get(cat, element_id):
    for e in cat["elements"]:
        if e["id"] == element_id:
            return e
    return None


def require(cat, element_id, types=None):
    e = get(cat, element_id)
    if not e:
        raise KeyError(f"élément « {element_id} » absent du catalogue")
    if types and e["type"] not in types:
        raise KeyError(f"« {element_id} » est de type {e['type']}, attendu : {', '.join(types)}")
    return e


def by_hash(cat, digest):
    return next((e for e in cat["elements"] if e.get("sha256") == digest), None)


def unique_id(cat, base):
    ids = {e["id"] for e in cat["elements"]}
    cand, n = base, 2
    while cand in ids:
        cand, n = f"{base}-{n}", n + 1
    return cand


def upsert(cat, entry):
    cat["elements"] = [e for e in cat["elements"] if e["id"] != entry["id"]] + [entry]


def find(cat, type_=None, role=None, tags=None, statut=None):
    out = []
    for e in cat["elements"]:
        if type_ and e["type"] != type_:
            continue
        if role and e.get("usage", {}).get("role") != role:
            continue
        if tags and not set(tags) & set(e.get("tags", [])):
            continue
        if statut and e.get("statut") != statut:
            continue
        out.append(e)
    return out
