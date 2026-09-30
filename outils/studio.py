"""Studio Tesseract : bibliothèque de sons, musiques, VFX et styles + montage automatique.

Usage (depuis le dossier du studio) :  studio <commande> [options]   —   studio aide
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import catalogue as C  # noqa: E402
from lib import ingest, montage, page  # noqa: E402
from lib.config import APERCUS, BIB, ROOT, TSRCT_VERSION, fail, ffmpeg_path, say, tsrct, tsrct_path  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def refresh_page():
    from lib import guide
    out = page.generate()
    guide.generate()
    say(f"Catalogue HTML et guide mis à jour : {out}")


def cmd_guide(a):
    from lib import guide
    say(f"Guide : {guide.generate()}")


# ------------------------------------------------------------------ commandes
def cmd_ajouter(a):
    tags = [t.strip() for t in (a.tags or "").split(",") if t.strip()]
    ok, errors = ingest.add_many(a.chemins, a.type, tags, licence=a.licence or "", move=a.deplacer)
    say(f"{len(ok)} élément(s) installé(s), {len(errors)} erreur(s).")
    if ok:
        say("Statut « auto » : relis/valide les fiches (studio fiche <id>, studio modifier <id> --valider).")
    refresh_page()


def cmd_banque(a):
    from lib import banque
    jobs_or_done, rep = banque.import_bank(a.dossier, a.licence or "", workers=a.processus, dry=a.simulation,
                                           limit=a.limite)
    if a.simulation:
        out = ROOT / ".studio-work" / "banque-simulation.json"
        out.write_text(json.dumps([{k: (str(v) if k == "src" else v) for k, v in j.items() if k != "dest"}
                                   for j in jobs_or_done], ensure_ascii=False, indent=1), encoding="utf-8")
        say(f"Simulation écrite : {out}")
        return
    say(f"{rep['installes']} sons installés, {len(rep['erreurs'])} erreur(s) (détail : .studio-work/banque-rapport.json).")
    refresh_page()


def cmd_liste(a):
    cat = C.load()
    rows = C.find(cat, a.type, a.role, [a.tag] if a.tag else None)
    if a.famille:
        rows = [e for e in rows if a.famille.lower() in (e.get("famille") or "").lower()]
    if a.cherche:
        q = a.cherche.lower()
        rows = [e for e in rows if q in " ".join([e["id"], e.get("nom", ""), " ".join(e.get("tags", [])),
                                                   " ".join(e.get("alias", []))]).lower()]
    for e in rows:
        u = e.get("usage", {})
        d = e.get("tech", {}).get("duree_ms")
        say(f"{e['id']:<34} {e['type']:<11} {u.get('role', ''):<16} {e.get('statut', ''):<6} "
            f"{(str(d) + ' ms') if d else '':>9}  {', '.join(e.get('tags', [])[:6])}")
    say(f"— {len(rows)} élément(s)")


def cmd_fiche(a):
    e = C.get(C.load(), a.id)
    if not e:
        fail(f"« {a.id} » introuvable")
    say(json.dumps(e, ensure_ascii=False, indent=2))


def cmd_modifier(a):
    cat = C.load()
    e = C.get(cat, a.id)
    if not e:
        fail(f"« {a.id} » introuvable")
    u = e.setdefault("usage", {})
    for k in ("role", "quand", "eviter", "placement", "calage"):
        v = getattr(a, k)
        if v is not None:
            u[k] = v
    if a.volume is not None:
        u["volume"] = a.volume
    if a.nom:
        e["nom"] = a.nom
    if a.tags is not None:
        e["tags"] = [t.strip() for t in a.tags.split(",") if t.strip()]
    if a.ajouter_tags:
        e["tags"] = list(dict.fromkeys(e.get("tags", []) + [t.strip() for t in a.ajouter_tags.split(",") if t.strip()]))
    if a.licence is not None:
        e["licence"] = a.licence
    if a.notes is not None:
        u["notes"] = a.notes
    if a.valider:
        e["statut"] = "valide"
    C.upsert(cat, e)
    C.save(cat)
    say(f"Fiche {a.id} mise à jour.")
    refresh_page()


def cmd_supprimer(a):
    cat = C.load()
    e = C.get(cat, a.id)
    if not e:
        fail(f"« {a.id} » introuvable")
    bin_ = ROOT / ".corbeille"
    bin_.mkdir(exist_ok=True)
    src = BIB / e["fichier"]
    if src.exists():
        shutil.move(str(src), str(bin_ / src.name))
    for f in (e.get("apercus") or {}).values():
        p = APERCUS / f
        if p.exists():
            p.unlink()
    cat["elements"] = [x for x in cat["elements"] if x["id"] != a.id]
    C.save(cat)
    say(f"{a.id} retiré du catalogue (fichier déplacé dans .corbeille, récupérable).")
    refresh_page()


def cmd_transcrire(a):
    from lib.transcription import to_srt, transcribe
    res = transcribe(a.video, a.langue, a.modele, force=a.force)
    say(f"{len(res['mots'])} mots ({res['appareil']}).")
    say(" ".join(w["mot"] for w in res["mots"])[:2000])
    if a.srt:
        out = Path(a.video).with_suffix(".srt")
        to_srt(res["mots"], out)
        say(f"SRT : {out}")


def cmd_auto(a):
    from lib import plan as P
    path, pl = P.auto(a.rushes, a.recette, a.nom, a.accroche, a.musique, a.langue)
    say(f"Plan : {path}  ({len(pl['clips'])} plans, {pl['_info']['duree_ms'] / 1000:.1f} s)")
    if a.plan_seul:
        return
    rep = montage.build(path, export=not a.sans_export)
    say(json.dumps(rep, ensure_ascii=False, indent=2))


def cmd_monter(a):
    rep = montage.build(a.plan, export=not a.sans_export)
    say(json.dumps(rep, ensure_ascii=False, indent=2))


def preview_preset(e):
    typ = e["type"]
    work = ROOT / ".studio-work" / "apercus" / e["id"]
    if work.exists():
        shutil.rmtree(work)
    plan = {"nom": e["id"], "format": "9:16", "fond": "#2B2F3A", "dossier": str(work), "duree_ms": 2600,
            "export": {"resolution": "720p", "fps": 30}}
    if typ == "texte-fx":
        plan["textes"] = [{"preset": e["id"], "texte": "Ton *titre* ici", "debut_ms": 100, "duree_ms": 2400, "son": False}]
        t = 1200
    else:
        demo = "Voici un exemple de sous-titres animés pour tes vidéos".split()
        plan["sous_titres"] = {"preset": e["id"], "mots": [
            {"mot": w, "debut_ms": 150 + i * 260, "fin_ms": 150 + i * 260 + 220} for i, w in enumerate(demo)]}
        plan["duree_ms"] = 150 + len(demo) * 260 + 300
        t = 150 + 2 * 260 + 100
    b = montage.Builder(plan)
    b.build(export=True)
    APERCUS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / f"{e['id']}.mp4", APERCUS / f"{e['id']}.mp4")
    tsrct("preview", "--project", b.proj, "--time", str(t / 1000), "--output", APERCUS / f"{e['id']}.png")
    return {"video": f"{e['id']}.mp4", "image": f"{e['id']}.png"}


def cmd_apercus(a):
    cat = C.load()
    targets = [e for e in cat["elements"] if e["type"] in ("texte-fx", "sous-titres") and (not a.ids or e["id"] in a.ids)]
    for e in targets:
        say(f"  aperçu {e['id']}…")
        try:
            e["apercus"] = preview_preset(e)
        except Exception as ex:
            say(f"  ! {e['id']} : {ex}")
    C.save(cat)
    refresh_page()


def cmd_page(a):
    refresh_page()
    if a.en_ligne:
        out = page.generate(online=True)
        say(f"Version en ligne prête : {out} (+ fichiers.json)")


def cmd_verifier(a):
    problems = 0
    try:
        v = tsrct("--version")
        say(f"tsrct : {v} ({tsrct_path()})")
        if TSRCT_VERSION not in str(v):
            say(f"  ! version attendue {TSRCT_VERSION}")
            problems += 1
    except Exception as ex:
        say(f"  ! tsrct : {ex}")
        problems += 1
    for tool in ("ffmpeg", "ffprobe"):
        try:
            say(f"{tool} : {ffmpeg_path(tool)}")
        except Exception as ex:
            say(f"  ! {ex}")
            problems += 1
    try:
        import faster_whisper
        say(f"faster-whisper : {faster_whisper.__version__}")
    except Exception:
        say("  ! faster-whisper absent (sous-titres automatiques indisponibles)")
        problems += 1
    cat = C.load()
    for e in cat["elements"]:
        if not (BIB / e["fichier"]).exists():
            say(f"  ! fichier manquant : {e['id']} -> {e['fichier']}")
            problems += 1
        for pid in [e.get("police")] if e["type"] in ("texte-fx", "sous-titres") else []:
            if pid and not C.get(cat, pid):
                say(f"  ! {e['id']} utilise la police absente « {pid} »")
                problems += 1
    auto_ = sum(1 for e in cat["elements"] if e.get("statut") == "auto")
    say(f"{len(cat['elements'])} éléments au catalogue, {auto_} à valider. Problèmes : {problems}")
    sys.exit(1 if problems else 0)


# ------------------------------------------------------------------ CLI
def main():
    p = argparse.ArgumentParser(prog="studio", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ajouter", help="installer des fichiers (sans chemin : vide A-AJOUTER)")
    s.add_argument("chemins", nargs="*")
    s.add_argument("--type", choices=["sfx", "musique", "ambiance", "vfx", "image", "police", "texte-fx", "sous-titres"])
    s.add_argument("--tags")
    s.add_argument("--licence")
    s.add_argument("--deplacer", action="store_true", help="déplacer au lieu de copier")
    s.set_defaults(f=cmd_ajouter)

    s = sub.add_parser("banque", help="importer une banque de sons entière (dédoublonnée, classée, en parallèle)")
    s.add_argument("dossier")
    s.add_argument("--licence")
    s.add_argument("--processus", type=int)
    s.add_argument("--limite", type=int)
    s.add_argument("--simulation", action="store_true", help="classer sans rien copier")
    s.set_defaults(f=cmd_banque)

    s = sub.add_parser("liste", help="lister le catalogue")
    s.add_argument("--type")
    s.add_argument("--role")
    s.add_argument("--tag")
    s.add_argument("--famille")
    s.add_argument("--cherche", help="texte à chercher dans l'id, le nom, les tags")
    s.set_defaults(f=cmd_liste)

    s = sub.add_parser("fiche", help="afficher la fiche complète d'un élément")
    s.add_argument("id")
    s.set_defaults(f=cmd_fiche)

    s = sub.add_parser("modifier", help="corriger/valider la fiche d'un élément")
    s.add_argument("id")
    for k in ("role", "quand", "eviter", "placement", "nom", "tags", "ajouter_tags", "licence", "notes"):
        s.add_argument("--" + k.replace("_", "-"), dest=k)
    s.add_argument("--calage", choices=["pic", "debut", "fin"])
    s.add_argument("--volume", type=float)
    s.add_argument("--valider", action="store_true")
    s.set_defaults(f=cmd_modifier)

    s = sub.add_parser("supprimer", help="retirer un élément (fichier mis à la corbeille du studio)")
    s.add_argument("id")
    s.set_defaults(f=cmd_supprimer)

    s = sub.add_parser("transcrire", help="transcrire une vidéo mot à mot")
    s.add_argument("video")
    s.add_argument("--langue", default="fr")
    s.add_argument("--modele")
    s.add_argument("--srt", action="store_true")
    s.add_argument("--force", action="store_true")
    s.set_defaults(f=cmd_transcrire)

    s = sub.add_parser("auto", help="montage automatique : rushes + recette")
    s.add_argument("rushes", nargs="+")
    s.add_argument("--recette", default="short-vertical")
    s.add_argument("--nom")
    s.add_argument("--accroche", help="texte du titre d'accroche (*mot* = mis en avant)")
    s.add_argument("--musique", help="id de musique à imposer")
    s.add_argument("--langue")
    s.add_argument("--plan-seul", action="store_true", help="écrire plan.json sans monter")
    s.add_argument("--sans-export", action="store_true")
    s.set_defaults(f=cmd_auto)

    s = sub.add_parser("monter", help="construire un projet depuis un plan.json")
    s.add_argument("plan")
    s.add_argument("--sans-export", action="store_true")
    s.set_defaults(f=cmd_monter)

    s = sub.add_parser("apercus", help="rendre les aperçus vidéo des styles de texte/sous-titres")
    s.add_argument("ids", nargs="*")
    s.set_defaults(f=cmd_apercus)

    s = sub.add_parser("page", help="régénérer catalogue.html")
    s.add_argument("--en-ligne", action="store_true", help="préparer aussi la version à publier")
    s.set_defaults(f=cmd_page)
    sub.add_parser("verifier", help="vérifier outils et bibliothèque").set_defaults(f=cmd_verifier)
    sub.add_parser("guide", help="régénérer bibliotheque/GUIDE-BIBLIOTHEQUE.md").set_defaults(f=cmd_guide)

    a = p.parse_args()
    try:
        a.f(a)
    except (KeyError, ValueError, FileNotFoundError, RuntimeError) as ex:
        fail(str(ex).strip("'\""))


if __name__ == "__main__":
    main()
