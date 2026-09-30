"""Analyse automatique des médias : mesures techniques, rôle, tags et règles d'usage."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .catalogue import slug
from .config import AUDIO_EXT, VIDEO_EXT, ffmpeg_path, ffprobe, run, tsrct

SR = 22050

# ---------------------------------------------------------------- mots-clés
SFX_ROLES = [
    ("whoosh", ["whoosh", "woosh", "swoosh", "swish", "swipe", "swoop", "souffle", "passage", "fly", "pass"]),
    ("riser", ["riser", "rise", "uplift", "build", "montee", "tension", "sweep-up", "suspense"]),
    ("downlifter", ["downlift", "downer", "fall", "descente", "sweep-down", "drop-down"]),
    ("impact", ["impact", "hit", "boom", "punch", "thud", "slam", "kick", "coup", "frappe", "bam", "stomp", "braam"]),
    ("pop", ["pop", "bubble", "bulle", "blop", "plop"]),
    ("clic", ["click", "clic", "tap", "tick", "ui", "button", "bouton", "mouse", "souris", "keyboard", "clavier", "typing"]),
    ("notification", ["notif", "ding", "bell", "cloche", "chime", "ping", "success", "succes", "alert", "message", "sms"]),
    ("glitch", ["glitch", "digital", "error", "erreur", "static", "bug", "noise", "data", "zap"]),
    ("cash", ["cash", "coin", "money", "argent", "caisse", "register", "cha-ching"]),
    ("rire", ["laugh", "rire", "haha", "sitcom"]),
    ("scratch", ["scratch", "rewind", "vinyl", "rembobine"]),
    ("camera", ["camera", "shutter", "photo", "flash", "declencheur"]),
    ("transition", ["transition", "trans", "sweep"]),
]
AMBIANCE_WORDS = ["ambiance", "ambience", "ambient", "room", "roomtone", "crowd", "foule", "rain", "pluie", "wind",
                  "vent", "city", "ville", "nature", "forest", "foret", "cafe", "office", "bureau", "street", "rue",
                  "ocean", "mer", "birds", "oiseaux", "traffic", "night", "nuit"]
MUSIC_WORDS = ["music", "musique", "beat", "track", "song", "instrumental", "loop", "bgm", "lofi", "trap", "piano",
               "epic", "cinematic", "hiphop", "house", "edm", "pop-music", "phonk", "drill", "chill", "background"]
VFX_ROLES = [
    ("overlay-lumiere", ["leak", "flare", "light", "lumiere", "bokeh", "sun", "glow", "burn"]),
    ("texture", ["grain", "dust", "poussiere", "film", "scratch", "vhs", "noise", "paper", "texture", "overlay"]),
    ("transition", ["transition", "wipe", "glitch", "zoom", "swipe", "flash", "ink", "encre"]),
    ("particules", ["particle", "particule", "spark", "etincelle", "confetti", "smoke", "fumee", "fire", "feu", "snow", "neige"]),
    ("fond-anime", ["background", "fond", "bg", "loop", "gradient"]),
]
STOP = {"the", "and", "le", "la", "les", "de", "des", "du", "un", "une", "sfx", "fx", "sound", "son", "effect",
        "wav", "mp3", "final", "v1", "v2", "v3", "copy", "copie", "master", "edit", "mix"}

# ------------------------------------------------------- règles d'usage par rôle
USAGE = {
    "whoosh": dict(
        quand="Transitions entre deux plans, entrée ou sortie rapide d'un texte ou d'une image, mouvement de caméra (zoom, glissé).",
        eviter="Chaque coupe : garder 1 transition sonore sur 2 ou 3. Jamais sur une phrase importante.",
        placement="Le pic du souffle tombe pile sur la coupe : démarrer le son {pic_ms} ms avant.",
        calage="pic", volume=0.35),
    "impact": dict(
        quand="Arrivée d'un titre, révélation, chiffre clé, drop musical, coupe dramatique.",
        eviter="Plus de 2 ou 3 par minute ; sous la voix sans baisser la musique.",
        placement="Le pic ({pic_ms} ms) sur l'image clé (apparition du titre, coupe).",
        calage="pic", volume=0.5),
    "riser": dict(
        quand="Faire monter la tension juste avant une révélation, un drop ou un changement de scène.",
        eviter="Au milieu d'une phrase importante ; deux risers d'affilée.",
        placement="Le sommet du riser ({pic_ms} ms) tombe sur le moment clé : il démarre avant, pendant la montée.",
        calage="pic", volume=0.4),
    "downlifter": dict(
        quand="Après un impact ou un drop, retour au calme, fin de séquence.",
        eviter="Enchaîner avec un autre effet long.",
        placement="Démarre sur le moment clé et redescend après.",
        calage="debut", volume=0.35),
    "pop": dict(
        quand="Apparition d'un texte, d'un sticker, d'un emoji, d'un élément d'interface.",
        eviter="Sur chaque mot des sous-titres : réserver aux mots-clés et aux éléments qui apparaissent.",
        placement="Pic sur la première image où l'élément apparaît (démarrer {pic_ms} ms avant).",
        calage="pic", volume=0.3),
    "clic": dict(
        quand="Interaction à l'écran (bouton, souris, clavier), apparition discrète, rythme d'une liste.",
        eviter="Répétitions rapides qui deviennent agaçantes.",
        placement="Sur l'image exacte de l'interaction.",
        calage="pic", volume=0.3),
    "notification": dict(
        quand="Message, succès, validation, notification téléphone, chiffre positif.",
        eviter="Contexte négatif ou sérieux.",
        placement="Sur l'apparition de l'élément à l'écran.",
        calage="pic", volume=0.35),
    "glitch": dict(
        quand="Transition nerveuse ou tech, erreur, effet « bug », coupe brutale.",
        eviter="Vidéos calmes ou premium ; plus de 2 par vidéo courte.",
        placement="Centré sur la coupe ou sur l'effet visuel de glitch.",
        calage="pic", volume=0.35),
    "cash": dict(
        quand="Mention d'argent, prix, gains, vente, promo.",
        eviter="Sujets sérieux.",
        placement="Sur l'apparition du prix ou du chiffre.",
        calage="pic", volume=0.35),
    "rire": dict(quand="Réaction humoristique, chute d'une blague.", eviter="Contenus sérieux.",
                 placement="Juste après la chute.", calage="debut", volume=0.35),
    "scratch": dict(quand="Rupture comique, « retour en arrière », « attendez… ».", eviter="Usage répété.",
                    placement="Sur la coupe qui casse le rythme ; couper la musique au même moment.",
                    calage="debut", volume=0.4),
    "camera": dict(quand="Capture d'écran, photo, freeze frame, flash blanc.", eviter="Sans visuel associé.",
                   placement="Sur l'image du flash ou du gel.", calage="pic", volume=0.35),
    "transition": dict(quand="Changement de plan ou de partie.", eviter="Sur chaque coupe.",
                       placement="Centré sur la coupe (pic à {pic_ms} ms).", calage="pic", volume=0.35),
    "accent": dict(quand="Ponctuer un moment précis (apparition, geste, mot-clé).", eviter="Abus : un accent par idée.",
                   placement="Pic ({pic_ms} ms) sur le moment ponctué.", calage="pic", volume=0.35),
    "musique-fond": dict(
        quand="Fond musical sous la voix ou moteur du rythme d'un montage sans voix.",
        eviter="Couvrir la voix : baisser la musique pendant la parole (ducking automatique du studio).",
        placement="Caler les coupes sur les temps (≈{bpm} BPM, un temps = {beat_ms} ms) et les révélations sur les moments forts.",
        calage="debut", volume=0.25),
    "ambiance": dict(
        quand="Fond sonore réaliste sous des plans sans musique ou pour donner de l'espace à une scène.",
        eviter="Ambiance qui contredit l'image ; trop forte sous la voix.",
        placement="Sur toute la scène, fondu d'entrée et de sortie de 300 ms.",
        calage="debut", volume=0.15),
    "overlay-lumiere": dict(
        quand="Transition chaleureuse, ouverture, souvenir, look « film » ; par-dessus la coupe.",
        eviter="Vidéos corporate très sobres ; plus de 30 % de la durée.",
        placement="Calque au-dessus de la vidéo en mode de fusion « écran » (screen), centré sur la coupe.",
        calage="debut", volume=0.0),
    "texture": dict(
        quand="Donner un grain ou un look vintage à tout le montage.",
        eviter="Sur des textes fins (baisse la lisibilité).",
        placement="Sur toute la durée, mode « overlay » ou « screen », opacité 30 à 60 %.",
        calage="debut", volume=0.0),
    "particules": dict(quand="Ambiance festive, magique, énergie ; habillage d'un titre.", eviter="Masquer le sujet.",
                       placement="Au-dessus de la vidéo, fusion « écran » si fond noir.", calage="debut", volume=0.0),
    "fond-anime": dict(quand="Fond derrière un titre, une citation, une intro ou une outro.", eviter="Sous des rushes.",
                       placement="Calque le plus bas, sur la durée de la scène graphique.", calage="debut", volume=0.0),
    "b-roll": dict(quand="Plan de coupe pour illustrer ce qui est dit ou masquer une coupe de la voix.",
                   eviter="Plans sans rapport avec le propos.",
                   placement="Au-dessus du plan principal, la voix continue dessous.", calage="debut", volume=0.0),
    "logo": dict(quand="Signature de marque : intro, outro, coin de l'écran.", eviter="En plein milieu du sujet.",
                 placement="Coin haut ou fin de vidéo, 10 à 20 % de la largeur.", calage="debut", volume=0.0),
    "sticker": dict(quand="Réaction, emoji, illustration ponctuelle d'un mot.", eviter="Couvrir le visage.",
                    placement="À côté du sujet, apparition « pop » + son pop.", calage="debut", volume=0.0),
    "fond": dict(quand="Arrière-plan d'une scène graphique.", eviter="Sous des rushes.",
                 placement="Calque le plus bas.", calage="debut", volume=0.0),
    "titres": dict(quand="Titres, accroches, mots-clés en gros.", eviter="Longs paragraphes.",
                   placement="Importer dans le projet puis l'utiliser dans les styles de texte.", calage="debut", volume=0.0),
    "texte": dict(quand="Sous-titres, textes courants, légendes.", eviter="—",
                  placement="Importer dans le projet puis l'utiliser dans les styles de texte.", calage="debut", volume=0.0),
}


def usage_for(role, tech):
    tpl = dict(USAGE.get(role, USAGE["accent"]))
    fmt = {"pic_ms": tech.get("pic_ms", 0), "bpm": tech.get("bpm", "?"),
           "beat_ms": round(60000 / tech["bpm"]) if tech.get("bpm") else "?"}
    class Keep(dict):  # garde tels quels les champs inconnus ({theme}, {courbe}…) pour l'appelant
        def __missing__(self, k):
            return "{" + k + "}"
    for k in ("quand", "eviter", "placement"):
        tpl[k] = tpl[k].format_map(Keep(fmt))
    tpl["role"] = role
    return tpl


def words_of(name):
    s = slug(Path(name).stem)
    return [w for w in s.split("-") if w and not w.isdigit() and w not in STOP and len(w) > 1]


def match_role(words, table):
    joined = "-".join(words)
    for role, keys in table:
        for k in keys:
            if k in words or (len(k) > 3 and k in joined):
                return role
    return None


# ------------------------------------------------------------------- audio
def decode_mono(path, sr=SR, start=0.0, dur=None):
    cmd = [ffmpeg_path(), "-v", "error", "-nostdin"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", str(path)]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"décodage audio impossible : {r.stderr.decode(errors='replace')[:300]}")
    return np.frombuffer(r.stdout, dtype=np.float32)


def envelope(x, sr=SR, hop_ms=10):
    hop = int(sr * hop_ms / 1000)
    n = len(x) // hop
    if n == 0:
        return np.zeros(1)
    frames = x[: n * hop].reshape(n, hop)
    return np.sqrt((frames ** 2).mean(axis=1) + 1e-12)


def db(v):
    return float(20 * np.log10(max(float(v), 1e-9)))


def shape_features(x, sr=SR):
    env = envelope(x, sr)
    mx = env.max()
    loud = np.where(env > mx * 0.03)[0]
    start, end = (int(loud[0]), int(loud[-1])) if len(loud) else (0, len(env) - 1)
    pic = int(env.argmax())
    a = pic
    while a > 0 and env[a] > mx * 0.1:
        a -= 1
    t = pic
    while t < len(env) - 1 and env[t] > mx * 0.03:
        t += 1
    span = max(end - start, 1)
    rel = (pic - start) / span
    attaque = (pic - a) * 10
    if attaque <= 40 and rel < 0.25:
        forme = "percussive"
    elif rel > 0.7:
        forme = "montante"
    elif attaque > 40 and rel >= 0.2:
        forme = "en-cloche"
    else:
        forme = "tenue"
    seg = x[max(0, pic * 220 - sr // 4): pic * 220 + sr // 4]
    centroid = 0.0
    if len(seg) > 256:
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / sr)
        centroid = float((spec * freqs).sum() / (spec.sum() + 1e-9))
    return {
        "pic_ms": pic * 10, "attaque_ms": attaque, "queue_ms": (t - pic) * 10,
        "son_debut_ms": start * 10, "son_fin_ms": end * 10, "forme": forme,
        "brillance_hz": round(centroid), "crete_db": round(db(np.abs(x).max()), 1),
        "rms_db": round(db(np.sqrt((x ** 2).mean() + 1e-12)), 1),
    }


def onset_strength(x, sr=SR, n_fft=1024, hop=512):
    n = 1 + (len(x) - n_fft) // hop
    if n < 8:
        return np.zeros(1), hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n)[:, None]
    frames = x[idx] * np.hanning(n_fft)
    mag = np.log1p(10 * np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    flux = flux - np.convolve(flux, np.ones(16) / 16, mode="same")
    return np.maximum(flux, 0), hop


def tempo(x, sr=SR):
    oenv, hop = onset_strength(x, sr, hop=256)
    if len(oenv) < 64:
        return None, 0.0, 0
    fps = sr / hop
    oenv = np.convolve(oenv, np.hanning(5) / np.hanning(5).sum(), mode="same")
    o = oenv - oenv.mean()
    ac = np.correlate(o, o, mode="full")[len(o) - 1:]
    lags = np.arange(len(ac))
    with np.errstate(divide="ignore"):
        bpms = 60 * fps / lags
    ok = (bpms >= 60) & (bpms <= 190)
    weight = np.exp(-0.5 * (np.log2(np.where(ok, bpms, 120) / 115) / 0.9) ** 2)
    double = np.concatenate([ac[::2], np.zeros(len(ac) - len(ac[::2]))])  # ac[2*lag] : soutien des mesures
    score = np.where(ok, (ac + 0.5 * double) * weight, -np.inf)
    lag = int(np.argmax(score))
    bpm = float(60 * fps / lag)
    conf = float(max(0.0, ac[lag] / (ac[0] + 1e-9)))
    fold = np.array([oenv[i::lag].sum() for i in range(lag)])
    phase_ms = int(round(int(fold.argmax()) / fps * 1000))
    return round(bpm, 1), round(conf, 2), phase_ms


def music_moments(x, sr=SR, max_n=8):
    """Moments forts d'une musique : montées d'énergie (drops) et cassures (breaks)."""
    env = envelope(x, sr, hop_ms=250)
    if len(env) < 16:
        return []
    e = 20 * np.log10(np.convolve(env, np.ones(4) / 4, mode="same") + 1e-9)
    out = []
    for i in range(8, len(e) - 4):
        before, after = e[i - 8:i - 1].mean(), e[i:i + 4].mean()
        if after - before >= 5:
            out.append((i, after - before, "montée / drop"))
        elif before - after >= 8:
            out.append((i, before - after, "break (retombée)"))
    out.sort(key=lambda m: -m[1])
    picked = []
    for i, strength, label in out:
        if all(abs(i - p[0]) >= 16 for p in picked):
            picked.append((i, strength, label))
        if len(picked) >= max_n:
            break
    return [{"ms": i * 250, "type": label, "force_db": round(s, 1)} for i, s, label in sorted(picked)]


def loudness(path):
    r = run([ffmpeg_path(), "-nostdin", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    return (float(i[-1]) if i else None, float(p[-1]) if p else None)


def analyse_audio(path, type_hint=None):
    info = ffprobe(path)
    st = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not st:
        raise RuntimeError("aucune piste audio")
    duree = float(info["format"].get("duration", st.get("duration", 0)))
    tech = {"duree_ms": int(duree * 1000), "format": st.get("codec_name"),
            "frequence": int(st.get("sample_rate", 0)), "canaux": st.get("channels")}
    x = decode_mono(path, dur=min(duree, 240))
    tech.update(shape_features(x))
    words = words_of(path)
    typ = type_hint
    if not typ:
        if any(w in AMBIANCE_WORDS for w in words):
            typ = "ambiance"
        elif any(w in MUSIC_WORDS for w in words) or duree > 25:
            typ = "musique"
        else:
            typ = "sfx"
    if duree >= 3:
        tech["lufs"], tech["crete_vraie_db"] = loudness(path)
    tags = list(dict.fromkeys(words))
    if typ == "musique":
        start = min(10.0, duree * 0.1)
        bpm, conf, phase = tempo(decode_mono(path, start=start, dur=min(90, duree - start)))
        if bpm:
            tech.update(bpm=bpm, bpm_confiance=conf, premier_temps_ms=int(start * 1000 + phase) % int(60000 / bpm))
            tags.append("lent" if bpm < 90 else "rapide" if bpm > 125 else "tempo-moyen")
        tech["moments"] = music_moments(x)
        role = "musique-fond"
    elif typ == "ambiance":
        role = "ambiance"
    else:
        role = match_role(words, SFX_ROLES)
        if not role:
            f, d = tech["forme"], duree
            if f == "montante" and d > 0.8:
                role = "riser"
            elif f == "en-cloche" and d < 3:
                role = "whoosh"
            elif f == "percussive" and d < 0.35:
                role = "clic" if tech["brillance_hz"] > 2500 else "pop"
            elif f == "percussive":
                role = "impact"
            elif f == "tenue" and tech["queue_ms"] > 800:
                role = "downlifter"
            else:
                role = "accent"
        tags.append("court" if duree < 0.8 else "long" if duree > 3 else "moyen")
    if tech.get("brillance_hz"):
        tags.append("grave" if tech["brillance_hz"] < 1200 else "aigu" if tech["brillance_hz"] > 4000 else "medium")
    return typ, role, list(dict.fromkeys(tags)), tech


# ------------------------------------------------------------------- vidéo
def analyse_video(path):
    info = ffprobe(path)
    st = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not st:
        raise RuntimeError("aucune piste vidéo")
    num, den = (st.get("avg_frame_rate") or "0/1").split("/")
    fps = round(float(num) / float(den), 2) if float(den) else None
    pix = st.get("pix_fmt", "")
    alpha = any(k in pix for k in ("yuva", "rgba", "argb", "bgra", "gbrap", "ya"))
    duree = float(info["format"].get("duration", 0))
    tech = {"duree_ms": int(duree * 1000), "largeur": st.get("width"), "hauteur": st.get("height"), "fps": fps,
            "codec": st.get("codec_name"), "alpha": alpha,
            "son": any(s["codec_type"] == "audio" for s in info["streams"])}
    r = run([ffmpeg_path(), "-nostdin", "-hide_banner", "-i", path, "-vf", "fps=2,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
             "-t", "20", "-f", "null", "-"])
    ys = [float(v) for v in re.findall(r"YAVG=([\d.]+)", r.stderr)]
    tech["luminance_moy"] = round(sum(ys) / len(ys), 1) if ys else None
    words = words_of(path)
    role = match_role(words, VFX_ROLES)
    if not role:
        role = "b-roll" if (tech["luminance_moy"] or 100) > 45 and not alpha else "overlay-lumiere"
    if alpha:
        fusion = "normal"
    elif role in ("overlay-lumiere", "particules") or (tech["luminance_moy"] or 100) < 45:
        fusion = "screen"
    elif role == "texture":
        fusion = "overlay"
    else:
        fusion = "normal"
    tech["fusion_conseillee"] = fusion
    tags = list(dict.fromkeys(words + (["alpha"] if alpha else []) +
                              (["vertical"] if (st.get("height") or 0) > (st.get("width") or 0) else ["horizontal"])))
    return "vfx", role, tags, tech


# ------------------------------------------------------------------- images, polices
def analyse_image(path):
    info = ffprobe(path)
    st = info["streams"][0]
    pix = st.get("pix_fmt", "")
    alpha = any(k in pix for k in ("rgba", "ya", "pal8", "argb", "bgra"))
    words = words_of(path)
    role = "logo" if "logo" in words else "sticker" if alpha else "fond"
    tech = {"largeur": st.get("width"), "hauteur": st.get("height"), "alpha": alpha, "format": st.get("codec_name")}
    return "image", role, list(dict.fromkeys(words)), tech


def analyse_font(path):
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "f.tsrct"
        tsrct("project", "create", "--project", proj)
        res = tsrct("project", "import-font", "--project", proj, "--file", str(Path(path).resolve()))
    face = (res.get("faces") or [{}])[0]
    tech = {"fontFamily": res.get("fontFamily"), "fontStyle": res.get("fontStyle"),
            "famille": face.get("typographicFamilyName") or face.get("familyName"),
            "graisse": face.get("weight"), "italique": face.get("italic"),
            "style": face.get("typographicStyleName") or face.get("styleName")}
    words = words_of(path)
    joined = "-".join(words)
    display = any(k in joined for k in ("anton", "bebas", "impact", "display", "oswald", "bangers", "archivo"))
    role = "titres" if display or (face.get("weight") or 400) >= 700 else "texte"
    return "police", role, list(dict.fromkeys(words)), tech


# ------------------------------------------------------------------- aperçus
def make_previews(entry, src, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    ff = ffmpeg_path()
    eid, typ, ap = entry["id"], entry["type"], {}
    if typ in ("sfx", "musique", "ambiance"):
        png = out_dir / f"{eid}.onde.png"
        run([ff, "-nostdin", "-y", "-v", "error", "-i", src, "-filter_complex",
             "aformat=channel_layouts=mono,compand=gain=4,showwavespic=s=1200x180:colors=#8a8f98", "-frames:v", "1", png])
        mp3 = out_dir / f"{eid}.mp3"
        run([ff, "-nostdin", "-y", "-v", "error", "-i", src, "-vn", "-c:a", "libmp3lame", "-b:a", "128k", mp3])
        ap = {"onde": png.name, "audio": mp3.name}
    elif typ == "vfx":
        dur = entry["tech"]["duree_ms"] / 1000
        jpg = out_dir / f"{eid}.jpg"
        run([ff, "-nostdin", "-y", "-v", "error", "-ss", f"{dur / 3:.2f}", "-i", src, "-frames:v", "1",
             "-vf", "scale=480:-2", jpg])
        mp4 = out_dir / f"{eid}.mp4"
        run([ff, "-nostdin", "-y", "-v", "error", "-i", src, "-t", "8", "-an", "-vf", "scale=480:-2,fps=24",
             "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4])
        ap = {"image": jpg.name, "video": mp4.name}
    elif typ == "image":
        out = out_dir / f"{eid}.png"
        run([ff, "-nostdin", "-y", "-v", "error", "-i", src, "-vf", "scale='min(480,iw)':-2", out])
        ap = {"image": out.name}
    return ap
