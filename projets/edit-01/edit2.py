"""Edit n°1 — v2 « niveau pro » : même partition que la référence, relevée à 60 i/s, image par image.

Ce que la v1 ratait (retour utilisateur « trop débutant, pas assez smooth ») :
  1. Fluidité : plans pré-rendus par prep.py (flux optique 120 i/s + courbe de vitesse type Twixtor), chaque image
     à 60 i/s est unique.
  2. Flou radial : shader sur mesure « zoom blur à centre net » (le flou croît avec la distance au centre, comme
     CC Radial Fast Blur), au lieu d'un flou uniforme.
  3. Profil : alternance rapide relevée sur la réf. -> image glitch (smear) / N&B / glitch / couleur / glitch / N&B /
     glitch / couleur, avec micro-décalage de l'image à chaque glitch.
  4. Gros plan : le N&B arrive, puis l'image s'ASSOMBRIT progressivement (lent zoom avant), et la couleur revient
     d'un coup sur le temps (« un côté noir, puis un côté noir et blanc »)."""
import json
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI.parent.parent / "outils"))
sys.path.insert(0, str(ICI))
from lib.config import tsrct  # noqa: E402
from edit import DEMI, REF, TOTAL  # noqa: E402

W, H, FPS = 1080, 1920, 60
PLANS = json.loads((ICI / "plans" / "plans.json").read_text(encoding="utf-8"))

VERT = """struct VertexInput { @location(0) position: vec2<f32>, @location(1) tex_coords: vec2<f32>, @location(2) color: vec4<f32>, };
struct VertexOutput { @builtin(position) clip_position: vec4<f32>, @location(0) tex_coords: vec2<f32>, };
@vertex fn vs_main(input: VertexInput) -> VertexOutput { var out: VertexOutput; out.clip_position = vec4<f32>(input.position, 0.0, 1.0); out.tex_coords = input.tex_coords; return out; }
"""
FRAG_FIN = """@fragment fn fs_main(input: VertexOutput) -> @location(0) vec4<f32> {
  let raw = author_frag(input.tex_coords);
  return vec4<f32>(clamp(raw.rgb, vec3<f32>(0.0), vec3<f32>(raw.a)), raw.a);
}"""

ZOOM_BLUR = VERT + """
struct Params { amount: f32, centerX: f32, centerY: f32, clearRadius: f32, };
@group(0) @binding(0) var t_texture: texture_2d<f32>;
@group(0) @binding(1) var s_sampler: sampler;
@group(0) @binding(2) var<uniform> params: Params;
fn author_frag(uv: vec2<f32>) -> vec4<f32> {
  let c = vec2<f32>(params.centerX, params.centerY);
  let d = uv - c;
  let dist = length(d * vec2<f32>(1.0, 1.7778));
  let w = smoothstep(params.clearRadius, params.clearRadius + 0.55, dist);
  let k = params.amount * (0.06 + 0.94 * w) * 0.42;
  var acc = vec4<f32>(0.0);
  for (var i = 0; i < 40; i = i + 1) {
    let t = f32(i) / 39.0;
    acc = acc + textureSample(t_texture, s_sampler, c + d * (1.0 - k * t));
  }
  return acc / 40.0;
}
""" + FRAG_FIN

GLITCH = VERT + """
struct Params { amount: f32, seed: f32, desat: f32, _pad0: f32, };
@group(0) @binding(0) var t_texture: texture_2d<f32>;
@group(0) @binding(1) var s_sampler: sampler;
@group(0) @binding(2) var<uniform> params: Params;
fn hash(p: vec2<f32>) -> f32 { return fract(sin(dot(p, vec2<f32>(127.1, 311.7))) * 43758.5453); }
fn vnoise(p: vec2<f32>) -> f32 {
  let i = floor(p); let f = fract(p); let u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2<f32>(1.0, 0.0)), u.x), mix(hash(i + vec2<f32>(0.0, 1.0)), hash(i + vec2<f32>(1.0, 1.0)), u.x), u.y);
}
fn author_frag(uv: vec2<f32>) -> vec4<f32> {
  let a = params.amount;
  let s = params.seed;
  let n1 = vnoise(uv * vec2<f32>(2.5, 4.0) + vec2<f32>(s, 3.1 * s));
  let n2 = vnoise(uv * vec2<f32>(5.0, 1.5) + vec2<f32>(7.3 + s, s));
  let n3 = vnoise(uv * vec2<f32>(1.2, 9.0) + vec2<f32>(s * 0.7, 1.9));
  // smear « flux optique raté » : bandes horizontales étirées + grande déformation basse fréquence
  let off = (vec2<f32>(n1, n2) - 0.5) * vec2<f32>(0.85, 0.45) + vec2<f32>((n3 - 0.5) * 0.6, 0.0);
  let suv = clamp(uv + off * a, vec2<f32>(0.001), vec2<f32>(0.999));
  let col = textureSample(t_texture, s_sampler, suv);
  let g = dot(col.rgb, vec3<f32>(0.299, 0.587, 0.114));
  let rgb = mix(col.rgb, vec3<f32>(g) * vec3<f32>(1.02, 1.0, 0.98), params.desat * a);
  return vec4<f32>(mix(rgb, rgb * 1.08 + 0.03, a), col.a);
}
""" + FRAG_FIN


def ev(liste):
    return json.dumps([round(x) for x in liste])


# --------------------------------------------------------------------- partition (relevée sur la référence)
def rep(xs):
    return [x + k * DEMI for k in range(2) for x in xs]


COUPES = [round(x) for x in rep([0, 720, 1420, 2730, 3430, 4080])]
FOUETS = [round(x) for x in rep([2730])]
GLITCHS = rep([1033, 1133, 1233, 1316])                  # 1 image chacun (17 ms)
GL_DESAT = json.dumps([1, 0.35, 1, 0.35] * 2)             # gris / smear coloré, comme la réf.
NB_VIFS = [[a + k * DEMI, b + k * DEMI] for k in range(2) for a, b in ((1050, 1133), (1250, 1316))]
NB_SOMBRES = [[a + k * DEMI, b + k * DEMI] for k in range(2) for a, b in ((1800, 2070), (2420, 2730))]
SECOUSSES = rep([4170, 4500, 4850, 5080])
RIRES = [[2930 + k * DEMI, 3430 + k * DEMI] for k in range(2)]

LIB = (
    "var C=%s,F=%s,GL=%s,GD=%s,NV=%s,NS=%s,SE=%s,RI=%s;" % (json.dumps(COUPES), json.dumps(FOUETS), ev(GLITCHS), GL_DESAT,
                                                           json.dumps(NB_VIFS), json.dumps(NB_SOMBRES), ev(SECOUSSES), json.dumps(RIRES)) +
    "function cl(x){return Math.max(0,Math.min(1,x));}"
    "function sm(x){x=cl(x);return x*x*(3-2*x);}"
    "function isF(c){for(var i=0;i<F.length;i++){if(Math.abs(F[i]-c)<2)return true;}return false;}"
    "function fen(L,t){for(var i=0;i<L.length;i++){if(t>=L[i][0]&&t<L[i][1])return (t-L[i][0])/(L[i][1]-L[i][0]);}return -1;}"
    # transition zoom : sortie 140 ms (accélère), entrée 180 ms (décélère)
    "function zoomT(t){var s=0,e=0;for(var i=0;i<C.length;i++){var c=C[i];if(isF(c))continue;"
    "if(t>=c-140&&t<c&&c>0){s=Math.max(s,Math.pow(cl((t-(c-140))/140),1.8));}"
    "if(t>=c&&t<c+150){e=Math.max(e,0.75*Math.pow(1-cl((t-c)/150),2.4));}}return Math.max(s,e);}"
    "function fouetT(t){var v=0,d=0;for(var i=0;i<F.length;i++){var c=F[i];"
    "if(t>=c-80&&t<c){v=Math.pow(cl((t-(c-80))/80),2);d=-1;}"
    "if(t>=c&&t<c+220){v=Math.pow(1-cl((t-c)/220),2.2);d=1;}}return [v,d];}"
    "function glitch(t){for(var i=0;i<GL.length;i++){if(t>=GL[i]-1&&t<GL[i]+16)return i;}return -1;}"
    "function secT(t){var v=0;for(var i=0;i<SE.length;i++){var u=t-SE[i];if(u>=0&&u<220){v=Math.max(v,Math.exp(-u/70));}}return v;}"
    "function secP(t){var x=0;for(var i=0;i<SE.length;i++){var u=t-SE[i];if(u>=0&&u<220){x+=Math.sin(u/220*Math.PI*3)*Math.exp(-u/80);}}return x;}"
    "function rire(t){for(var i=0;i<RI.length;i++){if(t>=RI[i][0]&&t<RI[i][1]+180)return sm((t-RI[i][0])/(RI[i][1]-RI[i][0]));}return 0;}"
)


def js(start, corps):
    return LIB + "var g=input.time.milliseconds+%d;" % start + corps


def main():
    proj = ICI / "edit-01-v2.tsrct"
    work = ICI / ".tesseract-work"
    work.mkdir(exist_ok=True)
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
        m = tsrct("project", "import-video", "--project", proj, "--file", ICI / "plans" / f"plan{p['n']:02d}.mp4",
                  "--asset-id", f"plan{p['n']:02d}")
        debut, d = p["debut"], p["fin"] - p["debut"]
        s0 = max(W / m["width"], H / m["height"]) * 100
        layers.insert(0, {"type": "Video", "id": lid, "name": f"{p['role']} ({p['clip']})", "blendMode": "normal",
                          "activeRange": {"start": debut, "duration": d}, "sourceRange": {"start": 0, "duration": d},
                          "sourceIntrinsicDuration": m["durationMs"], "volume": 0.0,
                          "transform": {"anchorPoint": [m["width"] / 2, m["height"] / 2], "position": [W / 2, H / 2],
                                        "scale": [s0, s0], "rotation": 0, "opacity": 100},
                          "source": {"assetId": m["assetId"], "fit": "contain"}})
        # transform : zoom de transition, zoom lent (rire), poussée lente pendant le N&B sombre (+ retour sec),
        # micro-décalages des glitchs, secousses de la marche, glissé du fouet
        ech = js(debut, "var z=zoomT(g);var f=fouetT(g);var ns=fen(NS,g);var gl=glitch(g);"
                        "var push=ns>=0?0.07*sm(ns):0;var nv=fen(NV,g)>=0?0.03:0;"
                        "return %f*(1+0.14*z+0.08*rire(g)+push+nv+0.04*secT(g)+0.07*f[0]+(gl>=0?0.05:0));" % s0)
        posx = js(debut, "var f=fouetT(g);var gl=glitch(g);var nv=fen(NV,g)>=0?-16:0;"
                         "return %f+(f[1]<0?-280:460)*f[0]+30*secP(g)+(gl>=0?(gl%%2?34:-34):0)+nv;" % (W / 2))
        posy = js(debut, "var ns=fen(NS,g);return %f+12*secP(g+40)+(ns>=0?-40*sm(ns):0);" % (H / 2))
        for prop, code in (("scaleX", ech), ("scaleY", ech), ("positionX", posx), ("positionY", posy)):
            actions.append({"type": "setFxPropertyAnimator", "compositionId": "main",
                            "property": {"layerId": lid, "propertyType": prop},
                            "animator": {"type": "jsScript", "layerTimeJsCode": code}, "dependencies": []})
        effets = [
            ({"type": "customShader", "name": "glitchSmear", "description": "Image « flux optique raté » d'une image : "
              "smear basse fréquence + désaturation, comme les glitchs de la référence.", "wgsl": GLITCH,
              "params": [{"name": "amount", "description": "Force du smear (0 = aucun, 1 = image glitch).", "min": 0, "max": 1, "default": 0},
                         {"name": "seed", "description": "Graine du motif.", "min": 0, "max": 100, "default": 0},
                         {"name": "desat", "description": "Désaturation du glitch (1 = gris).", "min": 0, "max": 1, "default": 1},
                         {"name": "_pad0", "description": "Remplissage.", "min": 0, "max": 1, "default": 0}]},
             {"amount": "return glitch(g)>=0?0.8:0;", "seed": "var i=glitch(g);return i>=0?7.3*i+3:0;",
              "desat": "var i=glitch(g);return i>=0?GD[i]:1;"}),
            ({"type": "customShader", "name": "zoomBlurCentreNet", "description": "Flou radial de zoom dont la force croît "
              "avec la distance au centre (centre net), façon CC Radial Fast Blur.", "wgsl": ZOOM_BLUR,
              "params": [{"name": "amount", "description": "Force du flou (0..1).", "min": 0, "max": 1, "default": 0},
                         {"name": "centerX", "description": "Centre X (UV).", "min": 0, "max": 1, "default": 0.5},
                         {"name": "centerY", "description": "Centre Y (UV).", "min": 0, "max": 1, "default": 0.42},
                         {"name": "clearRadius", "description": "Rayon net autour du centre (UV).", "min": 0, "max": 1, "default": 0.12}]},
             {"amount": "return Math.min(1,zoomT(g)+0.25*secT(g));"}),
            ({"type": "directionalBlur", "direction": 90.0, "blurLength": 0.0},
             {"blurLength": "var f=fouetT(g);return 340*f[0]+95*secT(g);"}),
            ({"type": "hueSaturation", "hue": 0.0, "saturation": 10.0, "lightness": 0.0},
             {"saturation": "return (fen(NV,g)>=0||fen(NS,g)>=0)?-100:10;",
              "lightness": "var ns=fen(NS,g);return ns>=0?-6-30*sm(ns):(fen(NV,g)>=0?4:0);"}),
            ({"type": "brightnessContrast", "brightness": 0.0, "contrast": 24.0},
             {"contrast": "return fen(NV,g)>=0?62:(fen(NS,g)>=0?34:24);",
              "brightness": "var f=fouetT(g);var ns=fen(NS,g);return (fen(NV,g)>=0?10:0)+(ns>=0?-14*sm(ns):0)+50*f[0];"}),
            ({"type": "temperatureTint", "temperature": -14.0, "tint": 0.0}, {}),
            ({"type": "levels", "inputBlack": 14.0, "inputWhite": 246.0, "gamma": 0.9, "outputBlack": 0.0, "outputWhite": 255.0}, {}),
            ({"type": "sharpen", "amount": 32.0}, {"amount": "return fen(NV,g)>=0?140:32;"}),
            ({"type": "vignette", "amount": 0.35, "radius": 0.85, "feather": 0.6}, {}),
        ]
        for effet, anims in effets:
            eid += 1
            actions.append({"type": "addFxLayerEffect", "compositionId": "main", "layerId": lid, "effectId": eid,
                            "effect": dict({"enabled": True}, **effet)})
            for param, corps in anims.items():
                actions.append({"type": "setFxLayerEffectParamAnimator", "compositionId": "main", "layerId": lid,
                                "effectId": eid, "paramName": param,
                                "animator": {"type": "jsScript", "layerTimeJsCode": js(debut, corps)}, "dependencies": []})
        actions.append({"type": "setFxLayerMotionBlur", "compositionId": "main", "layerId": lid, "enabled": True})
    layers.append({"type": "Audio", "id": 900, "name": "Musique (référence)", "windowMs": TOTAL,
                   "activeRange": {"start": 0, "duration": TOTAL}, "sourceRange": {"start": 0, "duration": TOTAL},
                   "sourceIntrinsicDuration": audio.get("durationMs") or TOTAL, "volume": 1.0, "captionsEnabled": False,
                   "source": {"assetId": audio["assetId"]}})
    actions.insert(0, {"type": "setFxCompositionMotionBlur", "compositionId": "main",
                       "settings": {"enabled": True, "shutterAngle": 180, "shutterPhase": -90, "samplesPerFrame": 16,
                                    "adaptiveSampleLimit": 64}})
    ed = work / "editable-v2.json"
    tsrct("project", "checkout", "--project", proj, "--output", ed)
    doc = json.loads(ed.read_text(encoding="utf-8"))
    doc["dimensions"] = {"width": W, "height": H}
    doc["duration"] = TOTAL / 1000
    doc["composition"]["layers"] = layers
    ed.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    tsrct("project", "commit", "--project", proj, "--file", ed)
    ap = work / "actions-v2.json"
    ap.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")
    tsrct("project", "apply", "--project", proj, "--actions", ap)
    if "--apercu" in sys.argv:
        stamps = sys.argv[sys.argv.index("--apercu") + 1] if len(sys.argv) > sys.argv.index("--apercu") + 1 else \
            "60,680,760,1040,1090,1140,1270,1330,1900,2050,2600,2760"
        tsrct("filmstrip", "--project", proj, "--timestamps-ms", stamps, "--output", work / "planche-v2.png",
              "--tile-width", 216, "--tile-height", 384, "--items-per-row", 6)
    else:
        tsrct("export", "--project", proj, "--output", ICI / "edit-01-v2.mp4", "--resolution", "1080p", "--fps", str(FPS))
    print("ok")


if __name__ == "__main__":
    main()
