"""Edit n°1 — reproduction du modèle « tyyvixedit » sur les clips de l'utilisateur.

Structure relevée image par image sur la référence (60 i/s) : 2 × la même séquence de 5,417 s, 6 plans, tempo
0,337 s. Effets calés au milliseconde sur la référence :
  - transition « zoom » à chaque coupe : flou radial + zoom qui monte (sortie) puis retombe (entrée) ;
  - coupe fouettée (2,73 s) : flou directionnel géant + glissé latéral ;
  - flashs N&B ultra-contrastés (1,03 s / 1,23 s) et passages N&B sombres (1,80–2,07 / 2,42–2,73) ;
  - lent zoom avant sur le plan « rire » ; secousses + flou de mouvement sur les temps du plan « marche » ;
  - étalonnage contrasté + netteté sur tout.
Tous les effets sont des animateurs JS pilotés par le temps GLOBAL du montage (une seule table d'événements)."""
import json
import sys
from pathlib import Path

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI.parent.parent / "outils"))
from lib.config import tsrct  # noqa: E402

B = r"C:\Users\mtzti\Downloads\OUTPUT-20260928T172523Z-1-001\OUTPUT"
CLIPS = {
    "canal": B + r"\02_chemise_ouverte_et_pantalon_large_au_bord_du_canal_amai_nie_DKuvZsCNK5u.mp4",
    "sweat": B + r"\02_portrait_en_sweat_clair_sous_les_spots_kadenhammond_Czy_bkBut7R.mp4",
    "biceps": B + r"\07_poses_biceps_en_tee_shirt_ajuste_shredsonluc_DYC5CvENtCG.mp4",
    "tirage": B + r"\01_MUSCULATION\06_tirage_assis_sans_son_partenaire_apollosimeran_DR8xbbIEUcE.mp4",
    "nuit": B + r"\03_IA_SIMPLE\01_portrait_de_nuit_sous_les_guirlandes_kadenhammond_Cz4A1mgu20d.mp4",
}
REF = r"C:\Users\mtzti\Downloads\transfer-01a0e3e7\référence edit\01_tyyvixedit_7667810913499548935.mp4"
W, H, FPS = 1080, 1920, 60
DEMI = 5416.667                       # durée d'une séquence (la référence la joue 2 fois)
TOTAL = 10817

# plans d'une séquence : (début ms, rôle) — coupes relevées sur la référence
ROLES = [(0, "lunettes"), (720, "profil"), (1420, "gros-plan"), (2730, "rire"), (3430, "bras"), (4080, "marche")]
# (clip, début source en s) pour chaque rôle, 1re puis 2e séquence
CHOIX = [
    {"lunettes": ("canal", 0.30), "profil": ("tirage", 4.00), "gros-plan": ("nuit", 2.40),
     "rire": ("canal", 2.55), "bras": ("biceps", 1.75), "marche": ("canal", 4.55)},
    {"lunettes": ("canal", 9.00), "profil": ("canal", 1.50), "gros-plan": ("nuit", 3.70),
     "rire": ("tirage", 1.00), "bras": ("biceps", 0.00), "marche": ("canal", 5.62)},
]
FOUET = 2730                          # la coupe fouettée (flou directionnel au lieu du zoom)

# --------------------------------------------------------------------- table d'événements (JS commun)
coupes = []
for k in range(2):
    for t, _ in ROLES:
        coupes.append(round(k * DEMI + t))
coupes_js = json.dumps(coupes)
fouets = json.dumps([round(FOUET), round(DEMI + FOUET)])
flashs = json.dumps([[k * DEMI + a, k * DEMI + b] for k in range(2) for a, b in ((1030, 1130), (1230, 1320))])
sombres = json.dumps([[k * DEMI + a, k * DEMI + b] for k in range(2) for a, b in ((1800, 2070), (2420, 2730))])
secousses = json.dumps([k * DEMI + t for k in range(2) for t in (4170, 4500, 4850, 5080)])
rires = json.dumps([[k * DEMI + 2930, k * DEMI + 3430] for k in range(2)])

LIB = (
    "var C=%s,F=%s,FL=%s,SO=%s,SE=%s,RI=%s;" % (coupes_js, fouets, flashs, sombres, secousses, rires) +
    "function cl(x){return Math.max(0,Math.min(1,x));}"
    "function isF(c){for(var i=0;i<F.length;i++){if(Math.abs(F[i]-c)<2)return true;}return false;}"
    "function dans(L,t){for(var i=0;i<L.length;i++){if(t>=L[i][0]&&t<L[i][1])return true;}return false;}"
    # transition zoom : (sortie) 90 ms avant la coupe, montée en ease-in ; (entrée) 130 ms après, retombée ease-out
    "function zoomT(t){var s=0,e=0;for(var i=0;i<C.length;i++){var c=C[i];if(isF(c))continue;"
    "if(t>=c-140&&t<c&&c>0){s=Math.max(s,Math.pow(cl((t-(c-140))/140),1.6));}"
    "if(t>=c&&t<c+160){e=Math.max(e,Math.pow(1-cl((t-c)/160),1.6));}}return Math.max(s,e);}"
    # coupe fouettée : sortie 70 ms, entrée 200 ms
    "function fouetT(t){var v=0,d=0;for(var i=0;i<F.length;i++){var c=F[i];"
    "if(t>=c-70&&t<c){v=Math.pow(cl((t-(c-70))/70),2);d=-1;}"
    "if(t>=c&&t<c+200){v=Math.pow(1-cl((t-c)/200),2);d=1;}}return [v,d];}"
    # secousse : impulsion de 150 ms sur le temps
    "function secT(t){var v=0;for(var i=0;i<SE.length;i++){var u=t-SE[i];if(u>=0&&u<200){v=Math.max(v,Math.exp(-u/75));}}return v;}"
    "function secP(t){var x=0;for(var i=0;i<SE.length;i++){var u=t-SE[i];if(u>=0&&u<150){x+=Math.sin(u/150*Math.PI*3)*Math.exp(-u/60);}}return x;}"
    "function rire(t){for(var i=0;i<RI.length;i++){if(t>=RI[i][0]&&t<RI[i][1]+140)return cl((t-RI[i][0])/(RI[i][1]-RI[i][0]));}return 0;}"
)


def js(start, corps):
    """Animateur JS : `g` = temps global du montage (ms), à partir du temps du calque."""
    return LIB + "var g=input.time.milliseconds+%d;" % start + corps


def main():
    proj = ICI / "edit-01.tsrct"
    work = ICI / ".tesseract-work"
    work.mkdir(exist_ok=True)
    if proj.exists():
        proj.unlink()
    tsrct("project", "create", "--project", proj)
    metas = {k: tsrct("project", "import-video", "--project", proj, "--file", v, "--asset-id", "clip-" + k)
             for k, v in CLIPS.items()}
    # musique : la piste de la référence (le calage de tous les effets en dépend)
    son = work / "musique-ref.wav"
    import subprocess
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", REF, "-vn", "-ac", "2", "-ar", "48000", str(son)])
    audio = tsrct("project", "import-asset", "--project", proj, "--file", son, "--asset-id", "musique", "--kind", "audio")

    layers, actions, lid, eid = [], [], 1, 100
    plans = []
    for k in range(2):
        for i, (t, role) in enumerate(ROLES):
            debut = round(k * DEMI + t)
            fin = round(k * DEMI + ROLES[i + 1][0]) if i + 1 < len(ROLES) else round((k + 1) * DEMI)
            fin = min(fin, TOTAL)
            clip, src = CHOIX[k][role]
            plans.append((debut, fin, clip, src, role))
    for debut, fin, clip, src, role in plans:
        m = metas[clip]
        w, h = m["width"], m["height"]
        s0 = max(W / w, H / h) * 100
        d = fin - debut
        layers.insert(0, {"type": "Video", "id": lid, "name": f"{role} ({clip})", "blendMode": "normal",
                          "activeRange": {"start": debut, "duration": d},
                          "sourceRange": {"start": round(src * 1000), "duration": d},
                          "sourceIntrinsicDuration": m["durationMs"], "volume": 0.0,
                          "transform": {"anchorPoint": [w / 2, h / 2], "position": [W / 2, H / 2], "scale": [s0, s0],
                                        "rotation": 0, "opacity": 100},
                          "source": {"assetId": m["assetId"], "fit": "contain"}})
        # --- transform : zoom de transition + zoom lent (rire) + secousses (marche) + glissé du fouet
        ech = js(debut, "var z=zoomT(g);var f=fouetT(g);var r=rire(g);"
                        "return %f*(1+0.20*z+0.08*r+0.035*secT(g)+0.06*f[0]);" % s0)
        # fouet : le plan sortant file à gauche, l'entrant arrive de la droite ; + secousses de la marche
        posx = js(debut, "var f=fouetT(g);return %f+(f[1]<0?-260:420)*f[0]+26*secP(g);" % (W / 2))
        posy = js(debut, "return %f+10*secP(g+37);" % (H / 2))
        for prop, code in (("scaleX", ech), ("scaleY", ech), ("positionX", posx), ("positionY", posy)):
            actions.append({"type": "setFxPropertyAnimator", "compositionId": "main",
                            "property": {"layerId": lid, "propertyType": prop},
                            "animator": {"type": "jsScript", "layerTimeJsCode": code}, "dependencies": []})
        # --- effets (ordre = ordre de traitement)
        effets = [
            ("radialBlur", {"centerX": 0.5, "centerY": 0.42, "amount": 0.0}, {"amount": "return 60*zoomT(g)+14*secT(g);"}),
            ("directionalBlur", {"direction": 90.0, "blurLength": 0.0},
             {"blurLength": "var f=fouetT(g);return 320*f[0]+105*secT(g);"}),
            ("hueSaturation", {"hue": 0.0, "saturation": 10.0, "lightness": 0.0},
             {"saturation": "return (dans(FL,g)||dans(SO,g))?-100:10;",
              "lightness": "return dans(SO,g)?-14:(dans(FL,g)?6:0);"}),
            ("brightnessContrast", {"brightness": 0.0, "contrast": 24.0},
             {"contrast": "return dans(FL,g)?72:(dans(SO,g)?30:24);",
              "brightness": "var f=fouetT(g);return (dans(FL,g)?14:(dans(SO,g)?-22:0))+45*f[0];"}),
            # étalonnage « ciné » de la référence : ombres froides, noirs denses, milieux un peu plus sombres
            ("temperatureTint", {"temperature": -14.0, "tint": 0.0}, {}),
            ("levels", {"inputBlack": 14.0, "inputWhite": 246.0, "gamma": 0.9, "outputBlack": 0.0, "outputWhite": 255.0}, {}),
            ("sharpen", {"amount": 30.0}, {"amount": "return dans(FL,g)?160:30;"}),
            ("vignette", {"amount": 0.35, "radius": 0.85, "feather": 0.6}, {}),
        ]
        for typ, valeurs, anims in effets:
            eid += 1
            actions.append({"type": "addFxLayerEffect", "compositionId": "main", "layerId": lid, "effectId": eid,
                            "effect": dict({"type": typ, "enabled": True}, **valeurs)})
            for param, corps in anims.items():
                actions.append({"type": "setFxLayerEffectParamAnimator", "compositionId": "main", "layerId": lid,
                                "effectId": eid, "paramName": param,
                                "animator": {"type": "jsScript", "layerTimeJsCode": js(debut, corps)}, "dependencies": []})
        actions.append({"type": "setFxLayerMotionBlur", "compositionId": "main", "layerId": lid, "enabled": True})
        lid += 1
    layers.append({"type": "Audio", "id": 900, "name": "Musique (référence)", "windowMs": TOTAL,
                   "activeRange": {"start": 0, "duration": TOTAL}, "sourceRange": {"start": 0, "duration": TOTAL},
                   "sourceIntrinsicDuration": audio.get("durationMs") or TOTAL, "volume": 1.0, "captionsEnabled": False,
                   "source": {"assetId": audio["assetId"]}})
    actions.insert(0, {"type": "setFxCompositionMotionBlur", "compositionId": "main",
                       "settings": {"enabled": True, "shutterAngle": 180, "shutterPhase": -90,
                                    "samplesPerFrame": 16, "adaptiveSampleLimit": 64}})

    ed = work / "editable.json"
    tsrct("project", "checkout", "--project", proj, "--output", ed)
    doc = json.loads(ed.read_text(encoding="utf-8"))
    doc["dimensions"] = {"width": W, "height": H}
    doc["duration"] = TOTAL / 1000
    doc["composition"]["layers"] = layers
    ed.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    tsrct("project", "commit", "--project", proj, "--file", ed)
    ap = work / "actions.json"
    ap.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")
    tsrct("project", "apply", "--project", proj, "--actions", ap)
    print(f"{len(plans)} plans, {len(actions)} actions")
    if "--apercu" in sys.argv:
        stamps = ",".join(str(t) for t in (60, 400, 700, 760, 1080, 1270, 1600, 1900, 2600, 2760, 2850, 3200, 3450,
                                           3800, 4180, 4520, 4700, 5000, 5450, 8200))
        tsrct("filmstrip", "--project", proj, "--timestamps-ms", stamps, "--output", work / "planche.png",
              "--tile-width", 216, "--tile-height", 384, "--items-per-row", 10)
    else:
        tsrct("export", "--project", proj, "--output", ICI / "edit-01.mp4", "--resolution", "1080p", "--fps", str(FPS))
        print("export ok")


if __name__ == "__main__":
    main()
