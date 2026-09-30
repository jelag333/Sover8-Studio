"""Montage automatique : rushes + recette -> plan.json (modifiable) prêt pour montage.build."""
import json
from pathlib import Path

from . import catalogue as C
from .config import PROJETS, RECETTES, ffprobe, say
from .transcription import transcribe


def load_recette(rid):
    p = RECETTES / f"{rid}.json"
    if not p.exists():
        dispo = ", ".join(sorted(x.stem for x in RECETTES.glob("*.json")))
        raise FileNotFoundError(f"recette « {rid} » introuvable (disponibles : {dispo})")
    return json.loads(p.read_text(encoding="utf-8"))


def speech_segments(words, dur_ms, r):
    """Blocs de parole séparés par des silences > pause_min_ms, avec marges."""
    cs = r.get("coupe_silences", {})
    pause = int(cs.get("pause_min_ms", 400))
    before, after = int(cs.get("marge_avant_ms", 80)), int(cs.get("marge_apres_ms", 140))
    blocks = []
    for w in words:
        if blocks and w["debut_ms"] - blocks[-1][-1]["fin_ms"] <= pause:
            blocks[-1].append(w)
        else:
            blocks.append([w])
    segs = []
    for b in blocks:
        a = max(0, b[0]["debut_ms"] - before)
        z = min(dur_ms, b[-1]["fin_ms"] + after)
        if segs and a <= segs[-1]["fin"]:
            segs[-1]["fin"], segs[-1]["mots"] = z, segs[-1]["mots"] + b
        else:
            segs.append({"debut": a, "fin": z, "mots": b})
    return segs


def split_long(seg, max_ms):
    """Découpe un bloc trop long entre deux mots (jump cut sans perte de parole)."""
    out, cur_start, words = [], seg["debut"], seg["mots"]
    for i, w in enumerate(words[:-1]):
        if w["fin_ms"] - cur_start >= max_ms:
            cut = (w["fin_ms"] + words[i + 1]["debut_ms"]) // 2
            out.append((cur_start, cut))
            cur_start = cut
    out.append((cur_start, seg["fin"]))
    return [(a, b) for a, b in out if b - a > 200]


def sfx_pool(cat, role, tags=None, max_ms=1500, size=10):
    """Meilleurs SFX d'un rôle : validés, favoris, courts, sans droits à vérifier ; tags de la recette en bonus."""
    banned = {"droits-a-verifier", "vulgaire"}
    want = set(tags or [])

    def score(e):
        t = set(e.get("tags", []))
        return (-(2 * (e.get("statut") == "valide") + 2 * ("favori" in t) + len(want & t)
                  + (e.get("confiance") == "haute")), e["tech"].get("duree_ms", 0), e["id"])
    cands = [e for e in C.find(cat, "sfx", role=role)
             if not banned & set(e.get("tags", [])) and e["tech"].get("duree_ms", 0) <= max_ms]
    return [e["id"] for e in sorted(cands, key=score)[:size]]


def pick_music(cat, spec, total):
    cands = C.find(cat, "musique")
    if spec.get("id"):
        return spec["id"]
    want = set(spec.get("tags", []))

    def score(e):
        s = 2 * (e.get("statut") == "valide") + len(want & set(e.get("tags", [])))
        s += 2 if e["tech"]["duree_ms"] >= total else -1
        return (s, e["id"])
    return max(cands, key=score)["id"] if cands else None


def auto(rushes, recette_id, nom=None, accroche=None, musique=None, langue=None):
    r = load_recette(recette_id)
    cat = C.load()
    langue = langue or r.get("langue", "fr")
    max_total = int(float(r.get("duree_max_s", 600)) * 1000)
    plan_max = int(float(r.get("plan_max_s", 0)) * 1000)
    zooms = r.get("zoom_alterne", [1.0])
    clips, edit_words, cuts, t = [], [], [], 0
    use_words = r.get("coupe_silences", {}).get("actif", True) or r.get("sous_titres")
    for rush in rushes:
        rush = str(Path(rush).resolve())
        dur = int(float(ffprobe(rush)["format"]["duration"]) * 1000)
        words = transcribe(rush, langue)["mots"] if use_words else []
        if words and r.get("coupe_silences", {}).get("actif", True):
            ranges = []
            for seg in speech_segments(words, dur, r):
                ranges += split_long(seg, plan_max) if plan_max else [(seg["debut"], seg["fin"])]
        else:
            ranges = [(0, dur)]
        prev_end = None
        for a, b in ranges:
            if t + (b - a) > max_total:
                say(f"  durée max atteinte ({max_total // 1000} s) : le reste est ignoré")
                break
            real_cut = clips and (prev_end is None or a - prev_end > 1500)
            if clips:
                cuts.append({"t_ms": t, "vraie_coupe": bool(real_cut)})
            clips.append({"fichier": rush, "debut_ms": a, "fin_ms": b, "zoom": zooms[len(clips) % len(zooms)]})
            for w in words:
                if a <= w["debut_ms"] < b:
                    edit_words.append({"mot": w["mot"], "debut_ms": t + w["debut_ms"] - a,
                                       "fin_ms": t + min(w["fin_ms"], b) - a})
            t += b - a
            prev_end = b
    if not clips:
        raise ValueError("aucun plan retenu")
    if r.get("entree_premier_plan") == "punch":
        clips[0]["entree"] = "punch"
    plan = {"nom": nom or C.slug(Path(rushes[0]).stem), "format": r.get("format", "9:16"),
            "recette": recette_id, "export": r.get("export", {}), "clips": clips, "sfx": [], "textes": []}
    if r.get("musique") is not None or musique:
        spec = dict(r.get("musique") or {}, **({"id": musique} if musique else {}))
        mid = pick_music(cat, spec, t)
        if mid:
            plan["musique"] = {"id": mid, "volume": spec.get("volume", 0.22),
                               "volume_sous_voix": spec.get("volume_sous_voix", 0.06), "source_debut_ms": 0}
        else:
            say("  aucune musique dans la bibliothèque : montage sans musique")
    sc = r.get("sfx_coupes")
    if sc:
        pool = sfx_pool(cat, sc.get("role", "whoosh"), sc.get("tags"), sc.get("duree_max_ms", 1500))
        eligible = [c for c in cuts if c["vraie_coupe"]] or cuts
        every = max(1, int(sc.get("toutes_les", 2)))
        for i, c in enumerate(eligible):
            if pool and i % every == 0:
                plan["sfx"].append({"id": pool[(i // every) % len(pool)], "t_ms": c["t_ms"], "volume": sc.get("volume")})
        if not pool:
            say(f"  aucun SFX de rôle « {sc.get('role')} » : coupes sans son")
    ac = r.get("accroche")
    if ac and accroche:
        plan["textes"].append({"preset": ac["preset"], "texte": accroche, "debut_ms": 0,
                               "duree_ms": min(int(ac.get("duree_ms", 2200)), t)})
    if r.get("sous_titres") and edit_words:
        plan["sous_titres"] = {"preset": r["sous_titres"]["preset"], "mots": edit_words}
    plan["_info"] = {"coupes": cuts, "duree_ms": t, "genere_le": C.now()}
    dest = PROJETS / C.slug(plan["nom"])
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "plan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, plan
