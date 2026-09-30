"""Styles de texte (texte-fx) et de sous-titres -> actions Tesseract natives et éditables."""
import re

EASE = {"type": "cubicBezier", "x1": 0.2, "y1": 0, "x2": 0.2, "y2": 1}
BACK = {"type": "cubicBezier", "x1": 0.34, "y1": 1.56, "x2": 0.64, "y2": 1}
IN = {"type": "cubicBezier", "x1": 0.5, "y1": 0, "x2": 0.9, "y2": 0.5}
LIN = {"type": "linear"}
HOLD = {"type": "hold"}

ZONES = {  # centre vertical (fraction de la hauteur) selon l'orientation
    "portrait": {"haut": 0.16, "tiers-haut": 0.30, "centre": 0.50, "bas": 0.70, "tres-bas": 0.82},
    "paysage": {"haut": 0.14, "tiers-haut": 0.28, "centre": 0.50, "bas": 0.80, "tres-bas": 0.88},
}


def rgba(value, default=(1, 1, 1, 1)):
    if value is None:
        return list(default)
    if isinstance(value, (list, tuple)):
        return list(value) + [1] * (4 - len(value))
    h = value.lstrip("#")
    parts = [int(h[i:i + 2], 16) / 255 for i in range(0, len(h), 2)]
    return [round(p, 4) for p in parts] + [1] * (4 - len(parts))


def zone_y(zone, W, H):
    table = ZONES["portrait" if H >= W else "paysage"]
    return round(H * table.get(zone, 0.5))


def kf(prefix, name, t, v, easing=LIN, kind="float"):
    return {"id": f"{prefix}-{name}", "layerTime": int(t), "value": {"type": kind, "value": v}, "easing": easing}


def prop(lid, ptype, keys):
    return {"type": "setFxPropertyKeyframes", "compositionId": "main",
            "property": {"layerId": lid, "propertyType": ptype}, "keyframes": keys}


class Font:
    def __init__(self, family, style):
        self.family, self.style = family, style


def fit_size(text, size, box_w, st):
    """Réduit la taille pour que le mot le plus long tienne dans la boîte (estimation par chasse moyenne)."""
    ratio = float(st.get("chasse", 0.66 if st.get("majuscules") else 0.56))
    longest = max((len(w) for w in text.split()), default=1)
    track = 1 + float(st.get("interlettrage", 0)) / 1000
    need = longest * size * ratio * track
    return round(size * min(1.0, box_w * 0.96 / need), 1) if need else size


def text_layer(lid, name, text, start, dur, st, font, W, H, animators=None, pos=None, insert=0):
    """Crée un calque texte en boîte centré sur `pos` (x, y) + ses styles. Renvoie la liste d'actions."""
    bw = round(W * float(st.get("largeur", 0.86)))
    size = fit_size(text, float(st.get("taille", 80)), bw, st)
    bh = round(size * 1.35 * int(st.get("lignes", 2)) + size * 0.4)
    cx, cy = pos or (W / 2, zone_y(st.get("zone", "centre"), W, H))
    source = {"text": text, "fontFamily": font.family, "fontStyle": font.style, "fontSize": size,
              "fillColor": rgba(st.get("couleur")), "strokeWidth": 0, "justification": st.get("alignement", "center"),
              "boxText": True, "boxPosition": [0, 0], "boxSize": [bw, bh], "verticalAlign": "center",
              "allCaps": bool(st.get("majuscules", False)), "tracking": float(st.get("interlettrage", 0))}
    if st.get("interligne"):
        source["leading"] = float(st["interligne"])
    acts = [{"type": "createFxTextLayer", "compositionId": "main", "layerId": lid, "name": name,
             "insertIndex": insert, "activeRange": {"start": int(start), "duration": int(dur)},
             "transform": {"anchorPoint": [bw / 2, bh / 2], "position": [cx, cy], "scale": [100, 100],
                           "rotation": float(st.get("rotation", 0)), "opacity": 100},
             "sourceText": source, "animators": animators or []}]
    item = lid * 100
    c = st.get("contour")
    if c and float(c.get("epaisseur", 0)) > 0:
        acts.append({"type": "addFxLayerStyle", "compositionId": "main", "layerId": lid, "itemId": item + 1,
                     "style": {"type": "stroke", "enabled": True, "color": rgba(c.get("couleur"), (0, 0, 0, 1)),
                               "width": float(c["epaisseur"]), "position": "outside", "blendMode": "normal"}})
    o = st.get("ombre")
    if o:
        acts.append({"type": "addFxLayerStyle", "compositionId": "main", "layerId": lid, "itemId": item + 2,
                     "style": {"type": "dropShadow", "enabled": True, "color": rgba(o.get("couleur"), (0, 0, 0, 0.6)),
                               "offset": list(o.get("decalage", [0, 6])), "blurRadius": float(o.get("flou", 12)),
                               "spreadRadius": float(o.get("etalement", 0)), "blendMode": "normal"}})
    return acts, (cx, cy)


def entrance(lid, anim, dur_ms, layer_dur, center, text=None):
    """Keyframes d'entrée. anim : pop | fondu | glisse-haut | zoom-doux | machine | mot-a-mot | aucune."""
    p, d = f"L{lid}", max(1, min(int(dur_ms), int(layer_dur) - 1))
    if anim in (None, "aucune"):
        return []
    if anim == "pop":
        return [prop(lid, "scaleX", [kf(p, "sxi0", 0, 55), kf(p, "sxi1", d, 100, BACK)]),
                prop(lid, "scaleY", [kf(p, "syi0", 0, 55), kf(p, "syi1", d, 100, BACK)]),
                prop(lid, "opacity", [kf(p, "opi0", 0, 0), kf(p, "opi1", max(1, d // 2), 100, EASE)])]
    if anim == "zoom-doux":
        return [prop(lid, "scaleX", [kf(p, "sxi0", 0, 118), kf(p, "sxi1", d, 100, EASE)]),
                prop(lid, "scaleY", [kf(p, "syi0", 0, 118), kf(p, "syi1", d, 100, EASE)]),
                prop(lid, "opacity", [kf(p, "opi0", 0, 0), kf(p, "opi1", d, 100, EASE)])]
    if anim == "glisse-haut":
        y = center[1]
        return [prop(lid, "positionY", [kf(p, "pyi0", 0, y + 70), kf(p, "pyi1", d, y, EASE)]),
                prop(lid, "opacity", [kf(p, "opi0", 0, 0), kf(p, "opi1", d, 100, EASE)])]
    if anim == "fondu":
        return [prop(lid, "opacity", [kf(p, "opi0", 0, 0), kf(p, "opi1", d, 100, EASE)])]
    if anim in ("machine", "mot-a-mot") and text:
        if anim == "machine":
            steps = [text[:i] for i in range(1, len(text) + 1)]
        else:
            ws = text.split()
            steps = [" ".join(ws[:i]) for i in range(1, len(ws) + 1)]
        step = d / max(1, len(steps))
        keys = [kf(p, f"tc{i}", round(i * step), s, HOLD, "string") for i, s in enumerate(steps)]
        return [prop(lid, "textContent", keys)]
    raise ValueError(f"animation d'entrée inconnue : {anim}")


def exit_(lid, anim, dur_ms, layer_dur, center):
    p = f"L{lid}"
    d = max(1, min(int(dur_ms), int(layer_dur) // 3))
    a, b = int(layer_dur) - d, int(layer_dur) - 1
    if anim in (None, "aucune"):
        return []
    if anim == "fondu":
        return [prop(lid, "opacity", [kf(p, "opo0", a, 100), kf(p, "opo1", b, 0, IN)])]
    if anim == "pop":
        return [prop(lid, "scaleX", [kf(p, "sxo0", a, 100), kf(p, "sxo1", b, 60, IN)]),
                prop(lid, "scaleY", [kf(p, "syo0", a, 100), kf(p, "syo1", b, 60, IN)]),
                prop(lid, "opacity", [kf(p, "opo0", a, 100), kf(p, "opo1", b, 0, IN)])]
    if anim == "glisse-bas":
        y = center[1]
        return [prop(lid, "positionY", [kf(p, "pyo0", a, y), kf(p, "pyo1", b, y + 70, IN)]),
                prop(lid, "opacity", [kf(p, "opo0", a, 100), kf(p, "opo1", b, 0, IN)])]
    raise ValueError(f"animation de sortie inconnue : {anim}")


def merge_keys(actions):
    """Fusionne les setFxPropertyKeyframes visant la même propriété (entrée + sortie)."""
    out, seen = [], {}
    for a in actions:
        if a["type"] == "setFxPropertyKeyframes":
            k = (a["property"]["layerId"], a["property"]["propertyType"])
            if k in seen:
                seen[k]["keyframes"].extend(a["keyframes"])
                continue
            seen[k] = a
        out.append(a)
    return out


def highlight_animator(aid, word_indices, color, scale=None):
    sels = [{"id": aid + 1 + i, "start": w, "end": w + 1, "units": "index", "basedOn": "words",
             "mode": "add", "amount": 1, "shape": "square"} for i, w in enumerate(word_indices)]
    an = {"id": aid, "name": "mise en avant", "fillColor": rgba(color), "selectors": sels}
    if scale:
        an["scale"] = [scale, scale]
    return an


# ------------------------------------------------------------------ texte-fx
def build_text_fx(preset, text, start, dur, lid, font, W, H, pos=None):
    """Texte animé. Les *mots entre astérisques* prennent la couleur de mise en avant."""
    words = text.split()
    marked = [i for i, w in enumerate(words) if w.startswith("*") and w.rstrip(".,!?:;").endswith("*")]
    clean = " ".join(w.replace("*", "") for w in words)
    anims = []
    if marked and preset.get("mise_en_avant"):
        anims.append(highlight_animator(lid * 100 + 10, marked, preset["mise_en_avant"].get("couleur", "#FFD400")))
    acts, center = text_layer(lid, preset.get("nom", "Texte") + " : " + clean[:30], clean, start, dur, preset, font, W, H,
                              anims, pos)
    e, s = preset.get("entree", {}), preset.get("sortie", {})
    acts += entrance(lid, e.get("anim", "pop"), e.get("duree_ms", 220), dur, center, clean)
    acts += exit_(lid, s.get("anim", "fondu"), s.get("duree_ms", 150), dur, center)
    return merge_keys(acts)


# ------------------------------------------------------------------ sous-titres
PUNCT_END = re.compile(r"[.!?…]$")


def clean_word(w, keep_punct):
    w = w.strip()
    if not keep_punct:
        w = re.sub(r"[.,;:]+$", "", w)
    return w


def phrases(words, preset):
    """Regroupe les mots horodatés en phrases courtes lisibles."""
    max_w = int(preset.get("mots_max", 4))
    max_c = int(preset.get("caracteres_max", 24))
    gap = int(preset.get("pause_coupe_ms", 450))
    out, cur = [], []
    for i, w in enumerate(words):
        if cur:
            text_len = len(" ".join(x["mot"] for x in cur + [w]))
            if (len(cur) >= max_w or text_len > max_c or w["debut_ms"] - cur[-1]["fin_ms"] > gap
                    or PUNCT_END.search(cur[-1]["mot"])):
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


POP_EASE = {"type": "cubicBezier", "x1": 0.30, "y1": 0.0, "x2": 0.06, "y2": 1.0}
# mots qui ouvrent une nouvelle idée (on coupe avant) et petits mots qu'on ne laisse jamais en fin de ligne
OUVRANTS = {"and", "because", "but", "so", "when", "if", "or", "then", "et", "mais", "donc", "quand", "si", "ou", "parce"}
SUSPENDUS = {"my", "a", "an", "the", "to", "of", "on", "in", "your", "is", "are", "i", "you're", "it's", "one", "every",
             "from", "like", "for", "with", "at", "le", "la",
             "les", "un", "une", "de", "des", "du", "mon", "ma", "mes", "ton", "ta", "à", "au", "en", "je", "tu"}


def phrases_sens(words, preset):
    """Découpe au sens : ponctuation, mots ouvrants, jamais de petit mot suspendu en fin de ligne, N mots max."""
    max_w = int(preset.get("mots_max", 3))
    max_c = int(preset.get("caracteres_max", 20))
    gap = int(preset.get("pause_coupe_ms", 400))
    out, cur = [], []
    for w in words:
        low = w["mot"].strip(".,!?;:").lower()
        if cur:
            prev = cur[-1]
            chars = len(" ".join(x["mot"] for x in cur + [w]))
            # jusqu'à max_w + 1 mots s'ils sont très courts (évite un mot orphelin : « like you meant it »)
            full = (len(cur) >= max_w and not (len(cur) == max_w and chars <= int(preset.get("courts_max", 16)))) or chars > max_c
            if (PUNCT_END.search(prev["_orig"]) or prev["_orig"].rstrip().endswith(",")
                    or w["debut_ms"] - prev["fin_ms"] > gap or (low in OUVRANTS and len(cur) >= 2) or full):
                # ne pas finir sur un petit mot suspendu : on le fait passer à la ligne suivante
                carry = []
                while len(cur) > 1 and cur[-1]["mot"].lower() in SUSPENDUS and not PUNCT_END.search(cur[-1]["_orig"]):
                    carry.insert(0, cur.pop())
                out.append(cur)
                cur = carry
                if len(cur) >= max_w:
                    out.append(cur)
                    cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def build_subtitles_pop(preset, words, first_lid, font, font_file, W, H, timeline_end, y_for=None, cles=(), lignes=None):
    """Sous-titres « pop mot à mot » : chaque mot apparaît en pop-in (0 -> pic -> 100 %) quand il est prononcé,
    la phrase se construit mot après mot ; mots importants en couleur ; ombre douce ; flou de mouvement.
    Chaque mot est un calque texte placé à la mesure exacte de la police (Pillow)."""
    from PIL import ImageFont
    size = float(preset.get("taille", 60))
    pil = ImageFont.truetype(str(font_file), int(round(size)))
    keep = bool(preset.get("ponctuation", False))
    words = [dict(w, mot=clean_word(w["mot"], keep), _orig=w["mot"]) for w in words if clean_word(w["mot"], keep)]
    # mots clés : "mot" (toutes les occurrences) ou {"mot": ..., "t_ms": ...} (cette occurrence seulement)
    cles_all = {c.lower() for c in cles if isinstance(c, str)}
    cles_t = [(c["mot"].lower(), int(c["t_ms"])) for c in cles if isinstance(c, dict)]

    def is_key(w):
        bare = w["mot"].strip(".,!?;:'\"").lower()
        return bare in cles_all or any(bare == m and abs(w["debut_ms"] - t) <= 350 for m, t in cles_t)
    white, gold = rgba(preset.get("couleur", "#FFFFFF")), rgba(preset.get("couleur_cle", "#FFC21A"))
    pop = float(preset.get("pop", 1.18)) * 100
    o = preset.get("ombre", {})
    if lignes:  # découpe écrite à la main (travail de monteur) : on suit le nombre de mots de chaque ligne
        groups, k = [], 0
        for ligne in lignes:
            n = len(ligne.split())
            groups.append(words[k:k + n])
            k += n
        if k != len(words):
            raise ValueError(f"sous-titres : les lignes couvrent {k} mots, la transcription en a {len(words)}")
        groups = [g for g in groups if g]
    else:
        groups = (phrases_sens if preset.get("decoupe", "sens") == "sens" else phrases)(words, preset)
    acts, lid = [], first_lid
    space = pil.getlength(" ") * float(preset.get("espace", 1.15))  # un peu plus d'air : le pic du pop ne mord pas sur le voisin
    for gi, grp in enumerate(groups):
        # la ligne suivante commence 60 ms avant son premier mot : l'ancienne doit être partie avant (sinon les
        # deux lignes se superposent quand les phrases s'enchaînent sans pause, ex. dérush serré)
        nxt = groups[gi + 1][0]["debut_ms"] - 60 if gi + 1 < len(groups) else timeline_end
        p_end = min(grp[-1]["fin_ms"] + 450, nxt, timeline_end)
        text = " ".join(w["mot"] for w in grp)
        x0, y0, x1, y1 = pil.getbbox(text, anchor="ls")
        cy_local = (y0 + y1) / 2                        # centre vertical commun : tous les mots sur la même ligne
        widths = [pil.getlength(w["mot"]) for w in grp]
        total = sum(widths) + space * (len(grp) - 1)
        y = (y_for(grp[0]["debut_ms"], p_end) if y_for else float(preset.get("y", 0.80))) * H
        x = W / 2 - total / 2
        for i, w in enumerate(grp):
            start = max(0, w["debut_ms"] - 40) if i else max(0, grp[0]["debut_ms"] - 60)
            dur = p_end - start
            if dur < 60:
                x += widths[i] + space
                continue
            col = gold if is_key(w) else white
            cx = x + widths[i] / 2
            acts.append({"type": "createFxTextLayer", "compositionId": "main", "layerId": lid, "name": f"ST {w['mot']}",
                         "insertIndex": 0, "activeRange": {"start": int(start), "duration": int(dur)},
                         "transform": {"anchorPoint": [0, cy_local], "position": [round(x, 1), round(y, 1)],  # grandit vers la droite (vide)
                                       "scale": [100, 100], "rotation": 0, "opacity": 100},
                         "sourceText": {"text": w["mot"], "fontFamily": font.family, "fontStyle": font.style,
                                        "fontSize": size, "fillColor": col, "strokeWidth": 0, "justification": "left",
                                        "tracking": float(preset.get("interlettrage", 0))}})
            if o:
                acts.append({"type": "addFxLayerStyle", "compositionId": "main", "layerId": lid, "itemId": lid * 100 + 2,
                             "style": {"type": "dropShadow", "enabled": True, "color": rgba(o.get("couleur"), (0, 0, 0, 0.55)),
                                       "offset": list(o.get("decalage", [0, 4])), "blurRadius": float(o.get("flou", 10)),
                                       "spreadRadius": float(o.get("etalement", 0)), "blendMode": "normal"}})
            p = f"W{lid}"
            for prop in ("scaleX", "scaleY"):
                acts.append({"type": "setFxPropertyKeyframes", "compositionId": "main",
                             "property": {"layerId": lid, "propertyType": prop},
                             "keyframes": [kf(p, prop + "0", 0, float(preset.get("depart", 45))),
                                           kf(p, prop + "1", 120, pop, POP_EASE), kf(p, prop + "2", 360, 100.0, POP_EASE)]})
            # pop « mousse » : petite montée qui accompagne le mot + éclosion en 2 images
            for ptype, keys in (("positionY", [kf(p, "py0", 0, round(y + 10, 1)), kf(p, "py1", 360, round(y, 1), POP_EASE)]),
                                ("opacity", [kf(p, "op0", 0, 0.0), kf(p, "op1", 80, 100.0, POP_EASE)])):
                acts.append({"type": "setFxPropertyKeyframes", "compositionId": "main",
                             "property": {"layerId": lid, "propertyType": ptype}, "keyframes": keys})
            acts.append({"type": "setFxLayerMotionBlur", "compositionId": "main", "layerId": lid, "enabled": True})
            x += widths[i] + space
            lid += 1
    return acts, lid


def build_subtitles(preset, words, first_lid, font, W, H, timeline_end):
    keep = bool(preset.get("ponctuation", False))
    words = [dict(w, mot=clean_word(w["mot"], keep)) for w in words if clean_word(w["mot"], keep)]
    mode = preset.get("mode", "karaoke")
    color_on = preset.get("couleur_active", "#FFD400")
    scale_on = preset.get("grossir_mot_actif")
    e = preset.get("entree", {"anim": "pop", "duree_ms": 140})
    acts, lid, groups = [], first_lid, phrases(words, preset)
    for gi, grp in enumerate(groups):
        nxt = groups[gi + 1][0]["debut_ms"] if gi + 1 < len(groups) else timeline_end
        p_start = grp[0]["debut_ms"]
        p_end = min(grp[-1]["fin_ms"] + 250, nxt, timeline_end)
        text = " ".join(w["mot"] for w in grp)
        if mode == "phrase":
            spans = [(p_start, p_end, None, text)]
        elif mode == "mot":
            spans = [(w["debut_ms"], min(grp[i + 1]["debut_ms"] if i + 1 < len(grp) else p_end, timeline_end), None, w["mot"])
                     for i, w in enumerate(grp)]
        else:  # karaoke : la phrase reste, le mot prononcé change de couleur
            spans = []
            for i, w in enumerate(grp):
                s = p_start if i == 0 else w["debut_ms"]
                t = grp[i + 1]["debut_ms"] if i + 1 < len(grp) else p_end
                spans.append((s, t, i, text))
        for si, (s, t, wi, txt) in enumerate(spans):
            if t - s < 30:
                continue
            anims = [highlight_animator(lid * 100 + 10, [wi], color_on, scale_on)] if wi is not None else []
            a, center = text_layer(lid, f"ST {txt[:28]}", txt, s, t - s, preset, font, W, H, anims)
            if si == 0 or mode == "mot":
                a += entrance(lid, e.get("anim", "pop"), e.get("duree_ms", 140), t - s, center, txt)
            acts += merge_keys(a)
            lid += 1
    return acts, lid
