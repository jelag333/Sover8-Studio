"""Edit n°1 — v3 : copie à l'identique des effets de la référence (analyse profonde, image par image).

- Mouvement : chaque plan reçoit la courbe MESURÉE sur la référence (zoom, décalage, rotation à 60 i/s, suivi de
  points ORB) -> zoom puis dézoom du 1er plan, shakes, coups de zoom + rotation de la marche, etc.
- Flou : proportionnel à la VITESSE du zoom et de la rotation (comme le flou de mouvement de la réf.), + flou de
  mouvement natif, + fouet directionnel sur la coupe gros plan -> rire.
- Miroirs, images de bascule et reverse : cuits dans les plans par prep2.py.
- N&B : profil (pendant les miroirs) et gros plan (s'assombrit, puis couleur au reverse)."""
import json
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI.parent.parent / "outils"))
sys.path.insert(0, str(ICI))
from lib.config import tsrct  # noqa: E402
from edit import DEMI, REF, TOTAL  # noqa: E402
from edit2 import ZOOM_BLUR  # noqa: E402

W, H, FPS = 1080, 1920, 60
PLANS = json.loads((ICI / "plans3" / "plans.json").read_text(encoding="utf-8"))
COURBES = json.loads((ICI / "courbes_ref.json").read_text(encoding="utf-8"))
MARGE = 1.06                                 # sur-échelle minimale (rotation sans bord visible)


def _gros_plan():
    """Gros plan : sur la réf., le suivi mesurait surtout l'acteur qui baisse la tête (pas un effet de montage).
    Geste de montage réel : poussée lente, N&B stable qui continue de pousser, léger recul au reverse, re-poussée."""
    import math
    z, r = [], []
    for f in range(79):
        t = 1430 + f * 1000 / 60
        s = lambda a, b: max(0.0, min(1.0, (t - a) / (b - a)))
        e = lambda x: x * x * (3 - 2 * x)
        if t < 1800:
            v = 1 + 0.12 * e(s(1430, 1800))
        elif t < 2067:
            v = 1.12 + 0.04 * e(s(1800, 2067))
        elif t < 2133:
            v = 1.16 - 0.11 * e(s(2067, 2133))
        elif t < 2420:
            v = 1.05 + 0.12 * e(s(2133, 2420))
        else:
            v = 1.17 + 0.03 * e(s(2420, 2730))
        z.append(round(v, 4))
        r.append(round(-2.0 * e(s(1430, 1800)) if t < 2067 else -2.0 + 2.0 * e(s(2067, 2133)), 2))
    return {"zoom": z, "dx": [0.0] * 79, "dy": [0.0] * 79, "rot": r}


COURBES["gros-plan"] = _gros_plan()


def rep(xs):
    return [x + k * DEMI for k in range(2) for x in xs]


COUPES = [round(x) for x in rep([0, 720, 1420, 2730, 3430, 4080])]
FOUETS = [round(x) for x in rep([2730])]
NB_VIFS = [[a + k * DEMI, b + k * DEMI] for k in range(2) for a, b in ((1033, 1133), (1233, 1317))]
NB_SOMBRES = [[a + k * DEMI, b + k * DEMI] for k in range(2) for a, b in ((1800, 2067), (2420, 2730))]

LIB = (
    "var C=%s,F=%s,NV=%s,NS=%s;" % (json.dumps(COUPES), json.dumps(FOUETS), json.dumps(NB_VIFS), json.dumps(NB_SOMBRES)) +
    "function cl(x){return Math.max(0,Math.min(1,x));}"
    "function sm(x){x=cl(x);return x*x*(3-2*x);}"
    "function isF(c){for(var i=0;i<F.length;i++){if(Math.abs(F[i]-c)<2)return true;}return false;}"
    "function fen(L,t){for(var i=0;i<L.length;i++){if(t>=L[i][0]&&t<L[i][1])return (t-L[i][0])/(L[i][1]-L[i][0]);}return -1;}"
    # flou d'entrée/sortie de coupe (léger : le gros du flou vient du mouvement lui-même)
    "function coupeT(t){var s=0,e=0;for(var i=0;i<C.length;i++){var c=C[i];if(isF(c))continue;"
    "if(t>=c-70&&t<c&&c>0){s=Math.max(s,Math.pow(cl((t-(c-70))/70),2));}"
    "if(t>=c&&t<c+110){e=Math.max(e,Math.pow(1-cl((t-c)/110),2));}}return Math.max(s,e);}"
    "function fouetT(t){var v=0,d=0;for(var i=0;i<F.length;i++){var c=F[i];"
    "if(t>=c-80&&t<c){v=Math.pow(cl((t-(c-80))/80),2);d=-1;}"
    "if(t>=c&&t<c+200){v=Math.pow(1-cl((t-c)/200),2.2);d=1;}}return [v,d];}"
)


def js(start, courbe, corps):
    """`g` = temps global ; `f` = image (60 i/s) depuis le début du plan ; Z/X/Y/R = courbes mesurées du rôle."""
    return (LIB + "var Z=%s,X=%s,Y=%s,R=%s;" % (json.dumps(courbe["zoom"]), json.dumps(courbe["dx"]),
                                                json.dumps(courbe["dy"]), json.dumps(courbe["rot"])) +
            "var lt=input.time.milliseconds;var g=lt+%d;" % start +
            "var fi=lt*60/1000;var f0=Math.max(0,Math.min(Z.length-1,Math.floor(fi)));var f1=Math.min(Z.length-1,f0+1);var a=fi-Math.floor(fi);"
            "function L(A){return A[f0]+(A[f1]-A[f0])*a;}"
            "function V(A){return Math.abs(A[f1]-A[f0]);}" + corps)


def main():
    proj = ICI / "edit-01-v3.tsrct"
    work = ICI / ".tesseract-work"
    if proj.exists():
        proj.unlink()
    tsrct("project", "create", "--project", proj)
    son = work / "musique-ref.wav"
    if not son.exists():
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", REF, "-vn", "-ac", "2", "-ar", "48000", str(son)])
    audio = tsrct("project", "import-asset", "--project", proj, "--file", son, "--asset-id", "musique", "--kind", "audio")
    layers, actions, eid = [], [], 100
    for p in PLANS:
        lid = p["n"] + 1
        m = tsrct("project", "import-video", "--project", proj, "--file", ICI / "plans3" / f"plan{p['n']:02d}.mp4",
                  "--asset-id", f"p3-{p['n']:02d}")
        debut, d = p["debut"], p["fin"] - p["debut"]
        cb = COURBES[p["role"]]
        w, h = m["width"], m["height"]
        s0 = max(W / w, H / h) * 100 * MARGE
        layers.insert(0, {"type": "Video", "id": lid, "name": f"{p['role']} ({p['clip']})", "blendMode": "normal",
                          "activeRange": {"start": debut, "duration": d}, "sourceRange": {"start": 0, "duration": d},
                          "sourceIntrinsicDuration": m["durationMs"], "volume": 0.0,
                          "transform": {"anchorPoint": [w / 2, h / 2], "position": [W / 2, H / 2], "scale": [s0, s0],
                                        "rotation": 0, "opacity": 100},
                          "source": {"assetId": m["assetId"], "fit": "contain"}})
        # échelle : courbe mesurée (minimum = 1) ; position : courbe mesurée, bornée à la marge disponible (aucun bord)
        ech = "var f=fouetT(g);return %f*L(Z)*(1+0.05*f[0]);" % s0
        marge = "var S=%f*L(Z)/100;var mx=(S*%d-%d)/2*0.92,my=(S*%d-%d)/2*0.92;" % (s0, w, W, h, H)
        posx = marge + "var f=fouetT(g);var v=L(X)*%d+(f[1]<0?-260:420)*f[0];return %f+Math.max(-mx,Math.min(mx,v));" % (W, W / 2)
        posy = marge + "var v=L(Y)*%d;return %f+Math.max(-my,Math.min(my,v));" % (W, H / 2)
        rot = "return Math.max(-8,Math.min(8,L(R)));"
        for prop, code in (("scaleX", ech), ("scaleY", ech), ("positionX", posx), ("positionY", posy), ("rotation", rot)):
            actions.append({"type": "setFxPropertyAnimator", "compositionId": "main",
                            "property": {"layerId": lid, "propertyType": prop},
                            "animator": {"type": "jsScript", "layerTimeJsCode": js(debut, cb, code)}, "dependencies": []})
        effets = [
            ({"type": "customShader", "name": "zoomBlurCentreNet", "description": "Flou radial de zoom à centre net, "
              "piloté par la vitesse du zoom/rotation mesurée sur la référence et par les coupes.", "wgsl": ZOOM_BLUR,
              "params": [{"name": "amount", "description": "Force du flou (0..1).", "min": 0, "max": 1, "default": 0},
                         {"name": "centerX", "description": "Centre X (UV).", "min": 0, "max": 1, "default": 0.5},
                         {"name": "centerY", "description": "Centre Y (UV).", "min": 0, "max": 1, "default": 0.42},
                         {"name": "clearRadius", "description": "Rayon net autour du centre (UV).", "min": 0, "max": 1, "default": 0.14}]},
             {"amount": "return Math.min(1,V(Z)*16+V(R)*0.10+0.55*coupeT(g));"}),
            ({"type": "directionalBlur", "direction": 90.0, "blurLength": 0.0},
             {"blurLength": "var f=fouetT(g);return 340*f[0]+Math.min(120,(V(X)+V(Y))*%d*1.4);" % W}),
            ({"type": "hueSaturation", "hue": 0.0, "saturation": 10.0, "lightness": 0.0},
             {"saturation": "return (fen(NV,g)>=0||fen(NS,g)>=0)?-100:10;",
              "lightness": "var ns=fen(NS,g);return ns>=0?-6-30*sm(ns):(fen(NV,g)>=0?4:0);"}),
            ({"type": "brightnessContrast", "brightness": 0.0, "contrast": 24.0},
             {"contrast": "return fen(NV,g)>=0?58:(fen(NS,g)>=0?34:24);",
              "brightness": "var f=fouetT(g);var ns=fen(NS,g);return (fen(NV,g)>=0?8:0)+(ns>=0?-14*sm(ns):0)+50*f[0];"}),
            ({"type": "temperatureTint", "temperature": -14.0, "tint": 0.0}, {}),
            ({"type": "levels", "inputBlack": 14.0, "inputWhite": 246.0, "gamma": 0.9, "outputBlack": 0.0, "outputWhite": 255.0}, {}),
            ({"type": "sharpen", "amount": 32.0}, {"amount": "return fen(NV,g)>=0?120:32;"}),
            ({"type": "vignette", "amount": 0.35, "radius": 0.85, "feather": 0.6}, {}),
        ]
        for effet, anims in effets:
            eid += 1
            actions.append({"type": "addFxLayerEffect", "compositionId": "main", "layerId": lid, "effectId": eid,
                            "effect": dict({"enabled": True}, **effet)})
            for param, corps in anims.items():
                actions.append({"type": "setFxLayerEffectParamAnimator", "compositionId": "main", "layerId": lid,
                                "effectId": eid, "paramName": param,
                                "animator": {"type": "jsScript", "layerTimeJsCode": js(debut, cb, corps)}, "dependencies": []})
        actions.append({"type": "setFxLayerMotionBlur", "compositionId": "main", "layerId": lid, "enabled": True})
    layers.append({"type": "Audio", "id": 900, "name": "Musique (référence)", "windowMs": TOTAL,
                   "activeRange": {"start": 0, "duration": TOTAL}, "sourceRange": {"start": 0, "duration": TOTAL},
                   "sourceIntrinsicDuration": audio.get("durationMs") or TOTAL, "volume": 1.0, "captionsEnabled": False,
                   "source": {"assetId": audio["assetId"]}})
    actions.insert(0, {"type": "setFxCompositionMotionBlur", "compositionId": "main",
                       "settings": {"enabled": True, "shutterAngle": 220, "shutterPhase": -110, "samplesPerFrame": 16,
                                    "adaptiveSampleLimit": 64}})
    ed = work / "editable-v3.json"
    tsrct("project", "checkout", "--project", proj, "--output", ed)
    doc = json.loads(ed.read_text(encoding="utf-8"))
    doc["dimensions"] = {"width": W, "height": H}
    doc["duration"] = TOTAL / 1000
    doc["composition"]["layers"] = layers
    ed.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    tsrct("project", "commit", "--project", proj, "--file", ed)
    ap = work / "actions-v3.json"
    ap.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")
    tsrct("project", "apply", "--project", proj, "--actions", ap)
    tsrct("export", "--project", proj, "--output", ICI / "edit-01-v3.mp4", "--resolution", "1080p", "--fps", str(FPS))
    print("ok")


if __name__ == "__main__":
    main()
