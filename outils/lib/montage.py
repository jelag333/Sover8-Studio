"""Plan de montage (plan.json) -> projet Tesseract éditable + MP4 + planche de contrôle."""
import json
import shutil
from pathlib import Path

from . import analyse, catalogue as C, presets as PR
from .config import BIB, PROJETS, say, tsrct

FORMATS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}
IDENT = {"anchorPoint": [0, 0], "position": [0, 0], "scale": [100, 100], "rotation": 0, "opacity": 100}


class Builder:
    def __init__(self, plan, plan_path=None):
        self.plan = plan
        self.cat = C.load()
        self.W, self.H = FORMATS[plan.get("format", "9:16")]
        self.nom = C.slug(plan.get("nom", "montage"))
        self.dir = Path(plan.get("dossier") or PROJETS / self.nom)
        self.work = self.dir / ".tesseract-work"
        self.proj = self.dir / f"{self.nom}.tsrct"
        self.assets, self.fonts, self.layers, self.actions = {}, {}, [], []
        self.warnings = []
        self.plan_path = plan_path

    # ------------------------------------------------------------ ressources
    def entry(self, eid, types=None):
        return C.require(self.cat, eid, types)

    def import_rush(self, fichier):
        key = str(Path(fichier).resolve())
        if key not in self.assets:
            aid = f"rush-{sum(1 for k in self.assets if k.startswith('rush:')) + 1}"
            r = tsrct("project", "import-video", "--project", self.proj, "--file", key, "--asset-id", aid)
            self.assets[key] = r
            self.assets["rush:" + aid] = True
        return self.assets[key]

    def import_entry(self, e):
        key = "cat:" + e["id"]
        if key not in self.assets:
            src = str((BIB / e["fichier"]).resolve())
            aid = "c-" + e["id"]
            if e["type"] == "vfx":
                r = tsrct("project", "import-video", "--project", self.proj, "--file", src, "--asset-id", aid)
            else:
                kind = "image" if e["type"] == "image" else "audio"
                r = tsrct("project", "import-asset", "--project", self.proj, "--file", src, "--asset-id", aid,
                          "--kind", kind)
                r.setdefault("durationMs", e.get("tech", {}).get("duree_ms"))
            self.assets[key] = r
        return self.assets[key]

    def font(self, preset):
        fid = preset.get("police")
        if not fid:
            raise ValueError(f"le style « {preset.get('id')} » n'a pas de police")
        if fid not in self.fonts:
            # l'import réel se fait après le commit (un commit retire les polices encore inutilisées)
            # le moteur de rendu résout les noms typographiques (ex. « Poppins » / « Black »)
            t = self.entry(fid, ["police"])["tech"]
            self.fonts[fid] = PR.Font(t.get("famille") or t["fontFamily"], t.get("style") or t["fontStyle"])
        return self.fonts[fid]

    def import_fonts(self):
        for fid in self.fonts:
            e = self.entry(fid, ["police"])
            tsrct("project", "import-font", "--project", self.proj, "--file", str((BIB / e["fichier"]).resolve()))

    def preset(self, pid, typ):
        e = self.entry(pid, [typ])
        return json.loads((BIB / e["fichier"]).read_text(encoding="utf-8"))

    # ------------------------------------------------------------ calques
    def cover(self, w, h, zoom=1.0, offset=(0, 0)):
        s = max(self.W / w, self.H / h) * 100 * zoom
        return {"anchorPoint": [w / 2, h / 2], "position": [self.W / 2 + offset[0], self.H / 2 + offset[1]],
                "scale": [s, s], "rotation": 0, "opacity": 100}

    def add_clips(self):
        t, cuts, lid = 0, [], 1
        for c in self.plan.get("clips", []):
            meta = self.import_rush(c["fichier"])
            d = int(c["fin_ms"]) - int(c["debut_ms"])
            if d <= 0:
                continue
            tr = self.cover(meta["width"], meta["height"], float(c.get("zoom", 1.0)), c.get("decalage", (0, 0)))
            self.layers.append({
                "type": "Video", "id": lid, "name": c.get("nom", f"Plan {lid}"), "blendMode": "normal",
                "activeRange": {"start": t, "duration": d},
                "sourceRange": {"start": int(c["debut_ms"]), "duration": d},
                "sourceIntrinsicDuration": meta["durationMs"], "volume": float(c.get("volume", 1.0)),
                "transform": tr, "source": {"assetId": meta["assetId"], "fit": "contain"}})
            if c.get("zooms"):
                self.add_zooms(lid, c, meta, tr, d)
            elif c.get("entree") == "punch":
                s = tr["scale"][0]
                for ax in ("scaleX", "scaleY"):
                    self.actions.append(PR.prop(lid, ax, [PR.kf(f"L{lid}", ax + "0", 0, s * 1.12),
                                                          PR.kf(f"L{lid}", ax + "1", min(220, d - 1), s, PR.EASE)]))
            if t > 0:
                cuts.append(t)
            t += d
            lid += 1
        return t, cuts

    # cibles de zoom : décalage vertical en hauteurs de visage, et où la cible se place à l'écran (fraction H)
    CIBLES = {"visage": (0.0, 0.40), "buste": (1.6, 0.45), "top": (2.4, 0.48), "taille": (3.6, 0.50),
              "jean": (5.4, 0.52), "jambes": (6.5, 0.55), "pieds": (8.2, 0.70)}

    # courbe des zooms : ease-out type After Effects (pic de vitesse à ~20 % puis longue décélération)
    COURBE_ZOOM = (0.30, 0.0, 0.06, 1.0)
    DUREE_ZOOM = 800

    def add_zooms(self, lid, clip, meta, base_tr, dur):
        """Zooms en cadres fixes, 2 clés par mouvement (comme dans After Effects).

        clip["zooms"] = [{t_ms, zoom, cible, duree_ms, courbe: [x1,y1,x2,y2], decalage_h, ecran_y, pourquoi}]
        Temps relatifs au début du plan. Le cadre ne bouge qu'entre t_ms et t_ms + duree_ms, puis reste
        immobile : la cible est placée sur la position MOYENNE du visage pendant le maintien (pas de suivi,
        donc pas d'effet shake). Un avertissement signale un visage qui sortirait du cadre pendant le maintien.
        """
        from . import suivi
        w, h = meta["width"], meta["height"]
        s0 = base_tr["scale"][0] / 100
        ax, ay = base_tr["anchorPoint"]
        try:
            track = suivi.track_face(clip["fichier"])
        except Exception as e:
            self.warnings.append(f"suivi du visage impossible ({e}) : zooms centrés")
            track = None
        src0 = int(clip["debut_ms"])
        zs = sorted(clip["zooms"], key=lambda z: z["t_ms"])

        def face_window(t_a, t_b):
            pts = [p for p in track if src0 + t_a <= p["t_ms"] <= src0 + max(t_b, t_a + 1)] if track else []
            return pts or ([suivi.at(track, src0 + t_a)] if track else [])

        def framing(z, t_a, t_b):
            """Position (px, py) et échelle k du cadre fixe tenu entre t_a et t_b."""
            zoom = float(z.get("zoom", 1.0))
            k = s0 * zoom
            cible = z.get("cible", "visage")
            if cible in (None, "plan") or zoom <= 1.0001 or (track is None and not isinstance(cible, (list, tuple))):
                tx, ty, sy = ax, ay, 0.5
            elif isinstance(cible, (list, tuple)):
                tx, ty, sy = float(cible[0]), float(cible[1]), float(z.get("ecran_y", 0.5))
            else:
                pts = face_window(t_a, t_b)
                off, sy = self.CIBLES.get(cible, (0.0, 0.45))
                off, sy = float(z.get("decalage_h", off)), float(z.get("ecran_y", sy))
                tx = sum(p["cx"] for p in pts) / len(pts)
                ty = min(h, sum(p["cy"] + off * p["h"] for p in pts) / len(pts))
            px = self.W / 2 - (tx - ax) * k
            py = self.H * sy - (ty - ay) * k
            px = min(ax * k, max(self.W - (w - ax) * k, px))  # jamais de bord visible
            py = min(ay * k, max(self.H - (h - ay) * k, py))
            if track and cible == "visage":  # le visage reste-t-il dans le cadre pendant le maintien ?
                for p in face_window(t_a, t_b):
                    sx_, sy_ = px + (p["cx"] - ax) * k, py + (p["cy"] - ay) * k
                    half = p["h"] * k / 2
                    if sx_ - half < 0 or sx_ + half > self.W or sy_ - half < 0 or sy_ + half > self.H * 0.9:
                        self.warnings.append(f"zoom à {z['t_ms']} ms : le visage sort du cadre vers {p['t_ms'] - src0} ms")
                        break
            return round(px, 1), round(py, 1), k * 100

        keys = {"scaleX": [], "scaleY": [], "positionX": [], "positionY": []}

        def add(t, fr, easing, tag):
            for prop, v in (("scaleX", fr[2]), ("scaleY", fr[2]), ("positionX", fr[0]), ("positionY", fr[1])):
                keys[prop].append(PR.kf(f"L{lid}z", f"{prop}-{tag}", int(t), round(v, 2), easing))

        first_t = zs[0]["t_ms"] if zs else dur
        cur = framing({"zoom": 1.0, "cible": "plan"}, 0, first_t)
        add(0, cur, PR.LIN, "init")
        for i, z in enumerate(zs):
            t0 = int(z["t_ms"])
            nxt = int(zs[i + 1]["t_ms"]) if i + 1 < len(zs) else dur
            d = min(int(z.get("duree_ms", self.DUREE_ZOOM)), max(1, nxt - t0 - 1), dur - 1 - t0)
            x1, y1, x2, y2 = z.get("courbe", self.COURBE_ZOOM)
            new = framing(z, t0 + d, nxt)
            add(t0, cur, PR.LIN, f"{i}a")  # clé de départ : cadre précédent, immobile jusqu'ici
            add(t0 + d, new, {"type": "cubicBezier", "x1": x1, "y1": y1, "x2": x2, "y2": y2}, f"{i}b")
            cur = new
        for prop, lst in keys.items():
            lst.sort(key=lambda k: k["layerTime"])
            self.actions.append(PR.prop(lid, prop, lst))

    def add_video_overlays(self, total):
        lid = 200
        for o in self.plan.get("calques_video", []):
            e = self.entry(o["id"], ["vfx"])
            meta = self.import_entry(e)
            start = int(o.get("debut_ms", 0))
            src0 = int(o.get("source_debut_ms", 0))
            d = min(int(o.get("duree_ms", meta["durationMs"] - src0)), meta["durationMs"] - src0, total - start)
            if d <= 0:
                continue
            tr = self.cover(meta["width"], meta["height"], float(o.get("zoom", 1.0)))
            tr["opacity"] = float(o.get("opacite", 100))
            self.layers.insert(0, {
                "type": "Video", "id": lid, "name": e["nom"],
                "blendMode": o.get("fusion") or e["tech"].get("fusion_conseillee", "normal"),
                "activeRange": {"start": start, "duration": d}, "sourceRange": {"start": src0, "duration": d},
                "sourceIntrinsicDuration": meta["durationMs"], "volume": float(o.get("volume", 0.0)),
                "transform": tr, "source": {"assetId": meta["assetId"], "fit": "contain"}})
            lid += 1

    def add_images(self, total):
        lid = 300
        for im in self.plan.get("images", []):
            e = self.entry(im["id"], ["image"])
            meta = self.import_entry(e)
            w, h = e["tech"]["largeur"], e["tech"]["hauteur"]
            s = self.W * float(im.get("largeur", 0.25)) / w * 100
            y = PR.zone_y(im.get("zone", "haut"), self.W, self.H)
            x = self.W / 2 if "x" not in im else float(im["x"]) * self.W
            start = int(im.get("debut_ms", 0))
            d = min(int(im.get("duree_ms", total - start)), total - start)
            self.layers.insert(0, {
                "type": "Image", "id": lid, "name": e["nom"], "blendMode": "normal",
                "activeRange": {"start": start, "duration": d},
                "transform": {"anchorPoint": [w / 2, h / 2], "position": [x, y], "scale": [s, s], "rotation": 0,
                              "opacity": float(im.get("opacite", 100))},
                "source": {"assetId": meta["assetId"], "fit": "contain"}})
            anim = im.get("entree", "pop")
            if anim != "aucune":
                p = f"L{lid}"
                keys = {"scaleX": [PR.kf(p, "sx0", 0, s * 0.5), PR.kf(p, "sx1", 240, s, PR.BACK)],
                        "scaleY": [PR.kf(p, "sy0", 0, s * 0.5), PR.kf(p, "sy1", 240, s, PR.BACK)],
                        "opacity": [PR.kf(p, "o0", 0, 0), PR.kf(p, "o1", 120, 100, PR.EASE)]}
                if anim == "fondu":
                    keys = {"opacity": keys["opacity"]}
                self.actions += [PR.prop(lid, k, v) for k, v in keys.items()]
            lid += 1

    STICKER_POP = {"type": "cubicBezier", "x1": 0.22, "y1": 1.18, "x2": 0.36, "y2": 1.0}   # pop doux, léger rebond
    STICKER_COURBE = {"type": "cubicBezier", "x1": 0.30, "y1": 0.0, "x2": 0.06, "y2": 1.0}  # ease-out type AE
    STICKER_SORTIE = {"type": "cubicBezier", "x1": 0.55, "y1": 0.0, "x2": 0.9, "y2": 0.45}
    STICKER_BALANCE = {"type": "cubicBezier", "x1": 0.45, "y1": 0.0, "x2": 0.55, "y2": 1.0}

    def glow_for(self, e):
        """Lueur qui contraste avec l'objet : ambre derrière un objet jaune, jaune sinon (le blanc disparaît sur fond clair)."""
        try:
            import cv2
            import numpy as np
            im = cv2.imread(str(BIB / e["fichier"]), cv2.IMREAD_UNCHANGED)
            hsv = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2HSV)
            m = im[:, :, 3] > 128
            h, sat = hsv[:, :, 0][m], hsv[:, :, 1][m]
            yellow = float(((h >= 18) & (h <= 38) & (sat > 90)).mean())
            return "#FFC21A"  # jaune-orangé tirant vers le jaune, pour tous (retour utilisateur)
        except Exception:
            return "#FFD21F"

    # pop relevé sur le graphe de vitesse After Effects de l'utilisateur (compo 60 i/s) : 3 clés,
    # 0 % -> ~160 % en 233 ms -> 100 % à 700 ms, même easing sur les deux segments (pic de vitesse à 20 %)
    POP_EASE = {"type": "cubicBezier", "x1": 0.30, "y1": 0.0, "x2": 0.06, "y2": 1.0}
    POP_T1, POP_T2 = 233, 700
    POP_SORTIE = {"type": "cubicBezier", "x1": 0.60, "y1": 0.0, "x2": 0.90, "y2": 0.35}

    def add_stickers(self, total):
        """Objets animés : groupe [objet + lueur Deep Glow], pop calqué sur l'exemple, ombre nette, flottement.

        plan["stickers"] = [{id, x, y (fractions de l'écran), largeur, rotation, apparait_ms, disparait_ms,
                             effets: [{t_ms, type: grossit|pulse, valeur}]  (échelle toujours proportionnelle),
                             deplacements: [{t_ms, x, y}], trajet: {a: [x, y], debut_ms, fin_ms, arc},
                             lueur (couleur, auto par défaut), lueur_intensite, pop (pic, 1.35), son (null), pourquoi}]
        """
        from . import glow as G
        lid = 3000
        if self.plan.get("stickers"):  # flou de mouvement façon After Effects, obturateur 90° : discret, pas d'étoile floue au départ du pop
            self.actions.append({"type": "setFxCompositionMotionBlur", "compositionId": "main",
                                 "settings": {"enabled": True, "shutterAngle": 90, "shutterPhase": -45,
                                              "samplesPerFrame": 16, "adaptiveSampleLimit": 128}})
        for n, st in enumerate(self.plan.get("stickers", [])):
            e = self.entry(st["id"], ["image"])
            meta = self.import_entry(e)
            w, h = e["tech"]["largeur"], e["tech"]["hauteur"]
            frame = 1000 / float(self.plan.get("export", {}).get("fps", 30))
            # apparition calée sur la grille d'images : chaque image du pop tombe au bon endroit de la courbe
            t_in = int(round(round(int(st["apparait_ms"]) / frame) * frame))
            t_out = int(round(round(int(st["disparait_ms"]) / frame) * frame))
            end = min(total, max(t_out, t_in + 760) + 280)
            life = end - t_in
            to = t_out - t_in
            s = self.W * float(st.get("largeur", 0.38)) / w * 100
            x, y = float(st["x"]) * self.W, float(st["y"]) * self.H
            rot = float(st.get("rotation", 0))
            gid, oid, glid = lid, lid + 1, lid + 2
            # lueur Deep Glow pré-calculée : une couleur au choix, "ombre" (halo noir doux décalé vers le bas =
            # ombre portée diffuse, sans couleur) ou "aucune". Par défaut : plan["lueur_defaut"], sinon jaune.
            mode = st.get("lueur", self.plan.get("lueur_defaut"))
            child_tr = lambda cw, ch, dx=0, dy=0: {"anchorPoint": [cw / 2, ch / 2], "position": [x + dx, y + dy],
                                                   "scale": [s, s], "rotation": rot, "opacity": 100}
            children = [{"type": "Image", "id": oid, "name": e["nom"], "blendMode": "normal",
                         "activeRange": {"start": 0, "duration": life}, "transform": child_tr(w, h),
                         "source": {"assetId": meta["assetId"], "fit": "contain"}}]
            glow_op = float(st.get("lueur_opacite", 78))
            if mode != "aucune":
                ombre = mode == "ombre"
                gcol = "#000000" if ombre else (mode or self.glow_for(e))
                if ombre:
                    glow_op = float(st.get("lueur_opacite", 45))
                    gpath, pad = G.soft_shadow(BIB / e["fichier"])
                else:
                    gpath, pad = G.deep_glow(BIB / e["fichier"], gcol, float(st.get("lueur_intensite", 1.0)),
                                             float(st.get("lueur_rayon", 1.0)))
                gkey = "glow:" + gpath.stem
                if gkey not in self.assets:
                    self.assets[gkey] = tsrct("project", "import-asset", "--project", self.proj, "--file", str(gpath),
                                              "--asset-id", "g-" + gpath.stem[-40:].strip("-"), "--kind", "image")
                gw, gh = w + 2 * pad, h + 2 * pad
                dx, dy = (6, 18) if ombre else (0, 0)  # décalage en pixels d'écran (le groupe est à l'échelle 100)
                children.append({"type": "Image", "id": glid, "name": f"Lueur {e['nom']}", "blendMode": "normal",
                                 "activeRange": {"start": 0, "duration": life}, "transform": child_tr(gw, gh, dx, dy),
                                 "source": {"assetId": self.assets[gkey]["assetId"], "fit": "contain"}})
            ref = st.get("reflet")  # light sweep : reflet découpé à la forme de l'objet, une image par frame
            if ref:
                n_img = int(ref.get("images", 15))
                t_ref = int(ref.get("t_ms", t_in + 750)) - t_in
                for k_, fpath in enumerate(G.reflet_images(BIB / e["fichier"], n_img, float(ref.get("largeur", 0.16)),
                                                          float(ref.get("intensite", 0.8)))):
                    rkey = "reflet:" + fpath.stem
                    if rkey not in self.assets:
                        self.assets[rkey] = tsrct("project", "import-asset", "--project", self.proj, "--file", str(fpath),
                                                  "--asset-id", "r-" + fpath.stem[-44:].strip("-"), "--kind", "image")
                    a0 = t_ref + round(k_ * frame)
                    a1 = t_ref + round((k_ + 1) * frame)
                    if 0 <= a0 and a1 < life:
                        self._rid = getattr(self, "_rid", 9000) + 1
                        children.insert(0, {"type": "Image", "id": self._rid, "name": f"Reflet {e['nom']} {k_}",
                                            "blendMode": "normal", "activeRange": {"start": a0, "duration": a1 - a0},
                                            "transform": child_tr(w, h), "source": {"assetId": self.assets[rkey]["assetId"], "fit": "contain"}})
            self.layers.insert(0, {
                "type": "Group", "id": gid, "name": f"Sticker {e['nom']}", "blendMode": "normal",
                "activeRange": {"start": t_in, "duration": life},
                "transform": {"anchorPoint": [x, y], "position": [x, y], "scale": [100, 100], "rotation": 0, "opacity": 100},
                "layers": children})
            k = {"scale": [], "opacity": [], "glow": []}

            def key(prop, t, v, easing=PR.LIN):
                t = int(max(0, min(t, life - 1)))
                k[prop] = [q for q in k[prop] if q[0] != t] + [(t, v, easing)]

            # pop en 3 clés : 0 % -> 150 % de la taille finale -> taille finale (même easing sur les deux segments)
            # objet très court : le pop est raccourci pour se terminer avant la sortie (toujours 3 étapes)
            k_t = max(0.45, min(1.0, (to - 150) / self.POP_T2))
            T1, T2 = int(self.POP_T1 * k_t), int(self.POP_T2 * k_t)
            final = 100.0
            for ef in st.get("effets", []):  # « grossit » : la taille finale du pop change (jamais de 4e étape)
                if ef["type"] == "grossit":
                    final *= float(ef.get("valeur", 1.15))
            key("scale", 0, 0.0)
            key("scale", T1, final * float(st.get("pop", 1.5)), self.POP_EASE)
            key("scale", T2, final, self.POP_EASE)
            key("opacity", 0, 100.0)     # opaque dès la 1re image : pas d'image fantôme translucide
            if st.get("lueur_anim"):     # glow qui s'allume avec le pop (pic sur le 150 %) puis se pose
                key("glow", 0, 0.0)
                key("glow", T1, min(100.0, glow_op * 1.7), self.POP_EASE)
                key("glow", T2, glow_op, self.POP_EASE)
            else:
                key("glow", 0, glow_op)  # lueur à intensité constante (pas de flash)
            # sortie : simple rétrécissement en douceur (pas d'anticipation, donc pas de rebond)
            exit_t = max(to, T2 + 60)
            key("scale", exit_t, final)
            key("scale", exit_t + 250, 0.0, self.POP_SORTIE)
            key("opacity", exit_t + 200, 100.0)
            key("opacity", exit_t + 250, 0.0)
            for prop, target, ids in (("scale", gid, ("scaleX", "scaleY")), ("opacity", gid, ("opacity",)),
                                      ("glow", glid, ("opacity",))):
                if target == glid and len(children) == 1:  # pas de lueur
                    continue
                lst = sorted(k[prop])
                for pt in ids:
                    self.actions.append(PR.prop(target, pt, [PR.kf(f"S{target}", f"{pt}{i}", t, round(v, 2), ez)
                                                             for i, (t, v, ez) in enumerate(lst)]))
            tr = st.get("trajet")
            if tr:  # objet qui voyage (ex. goutte de couleur)
                t0, t1 = int(tr["debut_ms"]) - t_in, int(tr["fin_ms"]) - t_in
                x1, y1 = float(tr["a"][0]) * self.W, float(tr["a"][1]) * self.H
                arc = float(tr.get("arc", -0.1)) * self.H
                for prop, v0, vm, v1 in (("positionX", x, (x + x1) / 2, x1), ("positionY", y, (y + y1) / 2 + arc, y1)):
                    self.actions.append(PR.prop(gid, prop, [
                        PR.kf(f"S{gid}", f"{prop}0", t0, round(v0, 1)),
                        PR.kf(f"S{gid}", f"{prop}1", (t0 + t1) // 2, round(vm, 1), self.STICKER_BALANCE),
                        PR.kf(f"S{gid}", f"{prop}2", t1, round(v1, 1), self.STICKER_BALANCE)]))
            else:  # flottement organique continu + glissés doux vers une nouvelle place
                moves = [[0, x, y]] + [[int(m["t_ms"]) - t_in, float(m["x"]) * self.W, float(m["y"]) * self.H]
                                       for m in st.get("deplacements", [])]
                ph = round(n * 1.7, 2)
                common = ("var t=input.time.milliseconds;var M=" + json.dumps(moves) + ";"
                          "function io(p){p=Math.max(0,Math.min(1,p));return p<0.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;}"
                          "function eo(p){p=Math.max(0,Math.min(1,p));return 1-Math.pow(1-p,3);}"
                          "var x=M[0][1],y=M[0][2];for(var i=1;i<M.length;i++){var a=io((t-M[i][0])/%d);" % int(st.get("suivi_ms", 550)) +
                          "x+=(M[i][1]-x)*a;y+=(M[i][2]-y)*a;}var on=eo((t-700)/900);")
                jx = common + "return x+3*Math.sin(t/1000*2*Math.PI/3.6+%s)*on;" % ph
                jy = common + "return y+5*Math.sin(t/1000*2*Math.PI/2.8+%s)*on;" % ph
                jr = ("var t=input.time.milliseconds;function eo(p){p=Math.max(0,Math.min(1,p));return 1-Math.pow(1-p,3);}"
                      "var on=eo((t-700)/900);return -5*(1-eo(t/700))+1.2*Math.sin(t/1000*2*Math.PI/3.2+%s)*on;" % ph)
                for prop, code in (("positionX", jx), ("positionY", jy), ("rotation", jr)):
                    self.actions.append({"type": "setFxPropertyAnimator", "compositionId": "main",
                                         "property": {"layerId": gid, "propertyType": prop},
                                         "animator": {"type": "jsScript", "layerTimeJsCode": code}, "dependencies": []})
            self.actions.append({"type": "setFxLayerMotionBlur", "compositionId": "main", "layerId": gid, "enabled": True})
            # ombre portée nette, décalée en bas à droite (comme l'exemple) : effet sur l'objet seul
            self.actions.append({"type": "addFxLayerEffect", "compositionId": "main", "layerId": oid, "effectId": oid * 10 + 1,
                                 "effect": {"type": "dropShadow", "enabled": True, "color": [0, 0, 0, 0.42],
                                            "offset": [9, 11], "blurRadius": 4, "spreadRadius": 0, "blendMode": "normal"}})
            son = st.get("son")  # pas de son par défaut : l'utilisateur les demande explicitement
            if son:
                from .plan import sfx_pool
                pool = [son] if C.get(self.cat, son) else sfx_pool(self.cat, son, max_ms=1500)
                if pool:
                    self.plan.setdefault("sfx", []).append({"id": pool[n % len(pool)], "t_ms": t_in + 60,
                                                            "volume": st.get("son_volume", 0.28)})
            lid += 3

    def audio_layer(self, lid, e, start, total, volume, src0=0):
        meta = self.import_entry(e)
        full = int(meta.get("durationMs") or e["tech"]["duree_ms"])
        if start < 0:
            src0, start = src0 - start, 0
        d = min(full - src0, total - start)
        if d <= 20:
            return None
        self.layers.append({"type": "Audio", "id": lid, "name": e["nom"], "windowMs": d,
                            "activeRange": {"start": int(start), "duration": int(d)},
                            "sourceRange": {"start": int(src0), "duration": int(d)},
                            "sourceIntrinsicDuration": full, "volume": float(volume), "captionsEnabled": False,
                            "source": {"assetId": meta["assetId"]}})
        return d

    def add_voice(self, total):
        """Piste voix pré-mixée (dérush avec J-cuts : les phrases se chevauchent en fondu croisé).
        plan["voix"] = {"fichier": wav, "volume": 1.0} ; les clips vidéo sont alors muets (volume 0)."""
        v = self.plan.get("voix")
        if not v:
            return
        src = str(Path(v["fichier"]).resolve())
        meta = tsrct("project", "import-asset", "--project", self.proj, "--file", src, "--asset-id", "voix",
                     "--kind", "audio")
        if not meta.get("durationMs"):
            import wave
            with wave.open(src) as w:
                meta["durationMs"] = w.getnframes() * 1000 // w.getframerate()
        full = int(meta["durationMs"])
        d = min(full, total)
        self.layers.append({"type": "Audio", "id": 499, "name": "Voix", "windowMs": d,
                            "activeRange": {"start": 0, "duration": d}, "sourceRange": {"start": 0, "duration": d},
                            "sourceIntrinsicDuration": full, "volume": float(v.get("volume", 1.0)),
                            "captionsEnabled": False, "source": {"assetId": meta["assetId"]}})

    def add_flashes(self, total):
        """Flashs de couleur plein écran, au-dessus de la vidéo et sous les objets et les textes.
        plan["flashs"] = [{t_ms, couleur, pic (opacité %), montee_ms, descente_ms, pourquoi}]"""
        fl = self.plan.get("flashs") or []
        if not fl:
            return
        idx = next((i for i, l in enumerate(self.layers) if l["type"] == "Video"), 0)
        for n, f in enumerate(fl):
            lid = 180 + n
            up, down = int(f.get("montee_ms", 70)), int(f.get("descente_ms", 450))
            start = max(0, int(f["t_ms"]) - up)
            d = min(up + down, total - start)
            self.actions.append({"type": "createFxRectLayer", "compositionId": "main", "layerId": lid,
                                 "name": f"Flash {n + 1}", "insertIndex": idx,
                                 "activeRange": {"start": start, "duration": d}, "transform": dict(IDENT),
                                 "rect": {"size": [self.W, self.H], "fillColor": PR.rgba(f.get("couleur", "#FFFFFF"))}})
            p = f"F{lid}"
            self.actions.append(PR.prop(lid, "opacity", [
                PR.kf(p, "o0", 0, 0.0), PR.kf(p, "o1", up, float(f.get("pic", 30)), PR.EASE),
                PR.kf(p, "o2", d - 1, 0.0, {"type": "cubicBezier", "x1": 0.2, "y1": 0.0, "x2": 0.1, "y2": 1.0})]))

    def add_music(self, total, speech):
        for n, extra in enumerate(self.plan.get("ambiances", [])):
            ea = self.entry(extra["id"], ["ambiance", "musique"])
            start = int(extra.get("debut_ms", 0))
            self.audio_layer(520 + n, ea, start, min(total, start + int(extra.get("duree_ms", total))),
                             float(extra.get("volume", ea["usage"].get("volume", 0.15))))
        m = self.plan.get("musique")
        if not m:
            return
        e = self.entry(m["id"], ["musique", "ambiance"])
        lvl = float(m.get("volume", e["usage"].get("volume", 0.25)))
        low = float(m.get("volume_sous_voix", round(lvl * 0.3, 3)))
        d = self.audio_layer(500, e, 0, total, lvl, int(m.get("source_debut_ms", 0)))
        if not d:
            return
        if d < total:
            self.warnings.append(f"la musique ({d} ms) est plus courte que le montage ({total} ms)")
        fi, fo = int(m.get("fondu_entree_ms", 250)), int(m.get("fondu_sortie_ms", 1200))
        pts = [(0, 0.0)]
        level = lambda t: low if any(a - 150 <= t <= b + 250 for a, b in speech) else lvl
        pts.append((fi, level(fi)))
        for a, b in speech:
            if a - 150 > fi:
                pts += [(a - 400, level(a - 400)), (a - 150, low)]
            pts += [(b + 250, low), (b + 600, level(b + 600))]
        pts += [(d - fo, level(d - fo)), (d - 1, 0.0)]
        keys, last = [], -1
        for t, v in sorted(p for p in pts if 0 <= p[0] < d):
            if t > last:
                keys.append(PR.kf("mus", f"v{len(keys)}", t, v, PR.EASE))
                last = t
        self.actions.append(PR.prop(500, "volume", keys))

    def add_sfx(self, total):
        lid = 600
        for s in sorted(self.plan.get("sfx", []), key=lambda s: s["t_ms"]):
            e = self.entry(s["id"], ["sfx", "ambiance"])
            cal = s.get("calage") or e["usage"].get("calage", "pic")
            t = int(s["t_ms"])
            start = t - e["tech"].get("pic_ms", 0) if cal == "pic" else t - e["tech"]["duree_ms"] if cal == "fin" else t
            if s.get("volume") is not None:
                vol = s["volume"]
            elif self.plan.get("clips"):  # niveau calé sous la voix (règle : un SFX reste en fond)
                from . import mix
                if not hasattr(self, "_voice_db"):
                    ref = (self.plan.get("voix") or {}).get("fichier") or self.plan["clips"][0]["fichier"]
                    self._voice_db = mix.voice_level(ref)
                vol = mix.gain(e, self._voice_db, s.get("sous_voix_db"))
            else:
                vol = e["usage"].get("volume", 0.35) * 0.5
            s["_volume_calcule"] = vol
            # source_debut_ms : on démarre le son en cours de fichier (ex. roulement de tambour qui doit finir pile sur
            # une révélation) ; duree_ms : on le coupe avant sa fin
            src0 = int(s.get("source_debut_ms", 0))
            fin_son = start + int(s["duree_ms"]) if s.get("duree_ms") else total
            if self.audio_layer(lid, e, start, min(total, fin_son), vol, src0):
                lid += 1

    def add_texts(self, total):
        lid = 1000
        for t in self.plan.get("textes", []):
            pr = self.preset(t["preset"], "texte-fx")
            if t.get("zone"):
                pr["zone"] = t["zone"]
            if t.get("taille"):
                pr["taille"] = t["taille"]
            start = int(t.get("debut_ms", 0))
            d = min(int(t.get("duree_ms", 2000)), total - start)
            self.actions += PR.build_text_fx(pr, t["texte"], start, d, lid, self.font(pr), self.W, self.H, t.get("position"))
            sfx = pr.get("sfx_entree")
            if sfx and t.get("son", True):
                from .plan import sfx_pool
                pool = [sfx["id"]] if sfx.get("id") else sfx_pool(self.cat, sfx.get("role"), sfx.get("tags"), 2500)
                pick = pool[(lid - 1000) % len(pool)] if pool else None
                if pick:
                    self.plan.setdefault("sfx", []).append({"id": pick, "t_ms": start + int(sfx.get("decalage_ms", 0)),
                                                            "volume": sfx.get("volume")})
            lid += 1

    def add_subtitles(self, total):
        st = self.plan.get("sous_titres")
        if not st or not st.get("mots"):
            return
        pr = self.preset(st["preset"], "sous-titres")
        for k in ("zone", "taille", "mode", "mots_max"):
            if st.get(k):
                pr[k] = st[k]
        if pr.get("mode") == "pop-mots":
            font_file = BIB / self.entry(pr["police"], ["police"])["fichier"]
            y0 = float(st.get("y", pr.get("y", 0.80)))
            acts, _ = PR.build_subtitles_pop(pr, st["mots"], 2000, self.font(pr), font_file, self.W, self.H, total,
                                             y_for=lambda a, b: self.subtitle_y(a, b, y0, pr), cles=st.get("cles", ()),
                                             lignes=st.get("lignes"))
            if not self.plan.get("stickers"):
                self.actions.append({"type": "setFxCompositionMotionBlur", "compositionId": "main",
                                     "settings": {"enabled": True, "shutterAngle": 90, "shutterPhase": -45,
                                                  "samplesPerFrame": 16, "adaptiveSampleLimit": 128}})
        else:
            acts, _ = PR.build_subtitles(pr, st["mots"], 2000, self.font(pr), self.W, self.H, total)
        self.actions += acts

    def subtitle_y(self, t_a, t_b, y0, pr):
        """Hauteur de la ligne de sous-titres : y0 par défaut ; si un objet (sticker) est à l'écran au même
        moment et chevauche la ligne, on passe juste au-dessus de lui (ou juste en dessous s'il est trop haut)."""
        half = float(pr.get("taille", 60)) * 0.75 / self.H
        for st in self.plan.get("stickers", []):
            if st.get("trajet") or st["apparait_ms"] >= t_b or st["disparait_ms"] + 250 <= t_a:
                continue
            e = self.entry(st["id"], ["image"])
            w, h = e["tech"]["largeur"], e["tech"]["hauteur"]
            sh = float(st.get("largeur", 0.38)) * self.W * h / w / self.H
            ys = [float(st["y"])] + [float(m["y"]) for m in st.get("deplacements", [])]
            top, bot = min(ys) - sh / 2, max(ys) + sh / 2
            if y0 + half > top - 0.02 and y0 - half < bot + 0.02:
                return round(top - 0.03 - half, 3) if top - 0.03 - half > 0.42 else round(min(0.9, bot + 0.03 + half), 3)
        return y0

    # ------------------------------------------------------------ pipeline
    def speech(self):
        if self.plan.get("parole"):
            return [tuple(x) for x in self.plan["parole"]]
        mots = (self.plan.get("sous_titres") or {}).get("mots") or []
        out = []
        for w in mots:
            if out and w["debut_ms"] - out[-1][1] < 700:
                out[-1][1] = w["fin_ms"]
            else:
                out.append([w["debut_ms"], w["fin_ms"]])
        return [tuple(x) for x in out]

    def prepare_dir(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        self.work.mkdir(exist_ok=True)
        (self.dir / "Previews").mkdir(exist_ok=True)
        if self.proj.exists():
            vdir = self.dir / "Versions"
            vdir.mkdir(exist_ok=True)
            n = len(list(vdir.glob(f"{self.nom}-v*.tsrct"))) + 1
            shutil.move(str(self.proj), str(vdir / f"{self.nom}-v{n}.tsrct"))
            mp4 = self.dir / f"{self.nom}.mp4"
            if mp4.exists():
                shutil.move(str(mp4), str(vdir / f"{self.nom}-v{n}.mp4"))
        (self.dir / "plan.json").write_text(json.dumps(self.plan, ensure_ascii=False, indent=2), encoding="utf-8")

    def build(self, export=True):
        self.prepare_dir()
        say(f"Projet : {self.proj}")
        tsrct("project", "create", "--project", self.proj)
        total, cuts = self.add_clips()
        total = int(self.plan.get("duree_ms") or total)
        if total <= 0:
            raise ValueError("montage vide : ajoute des clips ou une durée (duree_ms)")
        self.add_video_overlays(total)
        self.add_images(total)
        self.add_stickers(total)
        self.add_flashes(total)  # avant les textes : ses calques s'insèrent juste au-dessus de la vidéo
        self.add_texts(total)  # avant les SFX : un style de texte peut ajouter son son d'entrée
        self.add_voice(total)
        self.add_music(total, self.speech())
        self.add_sfx(total)
        self.add_subtitles(total)
        ed = self.work / "editable.json"
        tsrct("project", "checkout", "--project", self.proj, "--output", ed)
        doc = json.loads(ed.read_text(encoding="utf-8"))
        doc["dimensions"] = {"width": self.W, "height": self.H}
        doc["duration"] = round(total / 1000, 3)
        doc["composition"]["layers"] = self.layers
        ed.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        tsrct("project", "commit", "--project", self.proj, "--file", ed)
        self.import_fonts()
        if self.plan.get("fond"):  # fond uni sous tout le reste (scènes graphiques, aperçus)
            self.actions.insert(0, {
                "type": "createFxRectLayer", "compositionId": "main", "layerId": 190, "name": "Fond",
                "activeRange": {"start": 0, "duration": total}, "transform": dict(IDENT),
                "rect": {"size": [self.W, self.H], "fillColor": PR.rgba(self.plan["fond"])}})
        if self.actions:
            ap = self.work / "actions.json"
            ap.write_text(json.dumps(self.actions, ensure_ascii=False), encoding="utf-8")
            tsrct("project", "apply", "--project", self.proj, "--actions", ap)
        report = {"projet": str(self.proj), "duree_ms": total, "coupes_ms": cuts, "alertes": self.warnings}
        strip = self.dir / "Previews" / "Filmstrip.png"
        n = 15
        tw, th = (180, 320) if self.H > self.W else (320, 180) if self.W > self.H else (240, 240)
        stamps = ",".join(str(int(total * (i + 0.5) / n)) for i in range(n))
        tsrct("filmstrip", "--project", self.proj, "--timestamps-ms", stamps, "--output", strip,
              "--tile-width", tw, "--tile-height", th, "--items-per-row", 5)
        report["planche"] = str(strip)
        if export:
            ex = self.plan.get("export", {})
            mp4 = self.dir / f"{self.nom}.mp4"
            say("Export du MP4…")
            tsrct("export", "--project", self.proj, "--output", mp4, "--resolution", ex.get("resolution", "1080p"),
                  "--fps", str(ex.get("fps", 30)))
            report["video"] = str(mp4)
            report["lufs"], report["crete_db"] = analyse.loudness(str(mp4))
        (self.work / "rapport.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report


def build(plan_path, export=True):
    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    return Builder(plan, plan_path).build(export)


def _simplify(ts, vs, eps, forced):
    """Ramer-Douglas-Peucker : garde les clés utiles (écart > eps) et les coupes sèches."""
    keep = {0, len(ts) - 1} | set(forced) | {j - 1 for j in forced if j > 0}

    def rdp(a, b):
        if b - a < 2:
            return
        ta, tb, va, vb = ts[a], ts[b], vs[a], vs[b]
        best, idx = 0.0, None
        for j in range(a + 1, b):
            v = va + (vb - va) * (ts[j] - ta) / (tb - ta)
            d = abs(vs[j] - v)
            if d > best:
                best, idx = d, j
        if idx is not None and best > eps:
            keep.add(idx)
            rdp(a, idx)
            rdp(idx, b)
    pts = sorted(keep)
    for a, b in zip(pts[:-1], pts[1:]):
        rdp(a, b)
    return sorted(keep)
