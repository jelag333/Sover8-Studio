"""Carte lisible de la bibliothèque (GUIDE-BIBLIOTHEQUE.md), relue par Claude avant chaque montage."""
import collections

from . import banque  # noqa: F401  (enregistre les règles d'usage des rôles de banque)
from . import catalogue as C
from .analyse import USAGE
from .config import BIB
from .plan import sfx_pool

OUT = BIB / "GUIDE-BIBLIOTHEQUE.md"
TYPE_FR = {"sfx": "SFX", "musique": "Musiques", "ambiance": "Ambiances", "vfx": "VFX", "image": "Images",
           "police": "Polices", "texte-fx": "Textes animés", "sous-titres": "Sous-titres"}


def generate():
    cat = C.load()
    els = cat["elements"]
    by_type = collections.Counter(e["type"] for e in els)
    lines = [f"# Guide de la bibliothèque — {len(els)} éléments", "",
             f"_Généré automatiquement le {C.now()} par `studio guide`. Ne pas éditer : corriger les fiches (`studio modifier`)._", "",
             "| Type | Nombre |", "|---|---|"]
    lines += [f"| {TYPE_FR.get(t, t)} | {n} |" for t, n in by_type.most_common()]
    audio = [e for e in els if e["type"] in ("sfx", "ambiance", "musique")]
    roles = collections.defaultdict(list)
    for e in audio:
        roles[e.get("usage", {}).get("role", "autre")].append(e)
    lines += ["", "## Sons par rôle", "",
              "Pour chaque rôle : quand l'utiliser, et les meilleurs choix (validés, favoris, courts, sans droits à vérifier).", ""]
    for role, items in sorted(roles.items(), key=lambda kv: -len(kv[1])):
        if role == "motion":
            continue
        u = USAGE.get(role, {})
        fams = collections.Counter(e.get("famille", "—") for e in items).most_common(4)
        picks = sfx_pool(cat, role, max_ms=10 ** 7, size=8)
        auto = sum(1 for e in items if e.get("statut") == "auto")
        lines += [f"### {role} — {len(items)} sons" + (f" ({auto} à vérifier)" if auto else ""),
                  f"- Quand : {u.get('quand', '—').split('{')[0].strip()}",
                  f"- Éviter : {u.get('eviter', '—')}",
                  f"- Familles : {', '.join(f'{f} ({n})' for f, n in fams)}",
                  f"- Meilleurs choix : {', '.join(f'`{p}`' for p in picks) or '—'}", ""]
    motion = roles.get("motion", [])
    if motion:
        themes = collections.defaultdict(list)
        for e in motion:
            themes[e.get("famille", "").replace("Motion SFX : ", "")].append(e.get("courbe", "?"))
        lines += ["## Motion SFX (sons synchronisés sur une courbe d'animation)", "",
                  f"{len(motion)} sons, {len(themes)} thèmes. Chaque thème existe pour plusieurs courbes : choisir la courbe "
                  "identique à celle de l'animation (ease in = accélère, ease out = ralentit, easy ease = les deux, "
                  "bounce = rebond, hit = arrivée frappée, shake = secousse, swinging = balancier, wheel = rotation). "
                  "Id = `<thème>-<courbe>` (ex. `blade-ease-in`). Garder un seul thème par séquence.", "",
                  "| Thème | Courbes disponibles |", "|---|---|"]
        for t, cs in sorted(themes.items()):
            lines.append(f"| {t} | {', '.join(sorted(set(cs)))} |")
        lines.append("")
    risky = [e for e in els if {"droits-a-verifier", "vulgaire"} & set(e.get("tags", []))]
    if risky:
        lines += ["## À manier avec précaution", "",
                  f"{len(risky)} sons marqués `droits-a-verifier` (mèmes, jeux vidéo) ou `vulgaire` : jamais en montage automatique, "
                  "seulement sur demande explicite, et pas pour un usage commercial sans vérifier les droits.", ""]
    long_ = [e for e in audio if e["tech"].get("duree_ms", 0) > 20000]
    if long_:
        lines += ["## Sons longs (> 20 s)", "", ", ".join(f"`{e['id']}` ({e['tech']['duree_ms'] // 1000} s)" for e in long_[:40]), ""]
    others = [e for e in els if e["type"] not in ("sfx", "ambiance", "musique")]
    if others:
        lines += ["## Styles, polices et visuels", ""]
        for t in ("texte-fx", "sous-titres", "police", "vfx", "image"):
            xs = [e for e in others if e["type"] == t]
            if xs:
                lines.append(f"- {TYPE_FR[t]} : " + ", ".join(f"`{e['id']}`" for e in xs))
        lines.append("")
    musiques = by_type.get("musique", 0)
    if not musiques:
        lines += ["## Manques", "", "- Aucune musique : les montages se font sans musique tant que l'utilisateur n'en ajoute pas.", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    return OUT
