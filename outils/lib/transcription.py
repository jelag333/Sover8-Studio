"""Transcription locale mot à mot (faster-whisper), avec cache par fichier."""
import json
import os
import sys
from pathlib import Path

from .catalogue import sha256
from .config import CACHE, say

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")


def _cuda_dll_dirs():
    """Rend visibles les DLL CUDA installées par pip (nvidia-cublas-cu12, nvidia-cudnn-cu12)."""
    if os.name != "nt":
        return
    base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    for b in base.glob("*/bin"):
        os.add_dll_directory(str(b))
        os.environ["PATH"] = str(b) + os.pathsep + os.environ.get("PATH", "")


def _model(taille):
    from faster_whisper import WhisperModel
    _cuda_dll_dirs()
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            m = WhisperModel(taille or "large-v3-turbo", device="cuda", compute_type="float16")
            return m, "cuda"
    except Exception as e:  # CUDA indisponible -> CPU
        say(f"  (GPU indisponible, passage au CPU : {str(e)[:120]})")
    return WhisperModel(taille or "small", device="cpu", compute_type="int8"), "cpu"


def transcribe(path, langue="fr", taille=None, force=False):
    """Renvoie {"langue", "mots": [{mot, debut_ms, fin_ms, proba}], "segments": [...]} en temps source."""
    path = Path(path)
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"{sha256(path)[:16]}-{langue}-{taille or 'auto'}"
    cache = CACHE / f"{key}.mots.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text(encoding="utf-8"))
    say(f"  transcription de {path.name}…")
    model, device = _model(taille)
    try:
        segs, info = model.transcribe(str(path), language=langue, word_timestamps=True, vad_filter=True,
                                      condition_on_previous_text=False)
        segs = list(segs)
    except Exception as e:
        if device != "cuda":
            raise
        say(f"  (échec GPU : {str(e)[:120]} — nouvel essai sur CPU)")
        from faster_whisper import WhisperModel
        model, device = WhisperModel(taille or "small", device="cpu", compute_type="int8"), "cpu"
        segs, info = model.transcribe(str(path), language=langue, word_timestamps=True, vad_filter=True,
                                      condition_on_previous_text=False)
        segs = list(segs)
    mots, segments = [], []
    for s in segs:
        segments.append({"texte": s.text.strip(), "debut_ms": int(s.start * 1000), "fin_ms": int(s.end * 1000)})
        for w in s.words or []:
            t = w.word.strip()
            if not t:
                continue
            # un jeton sans espace initial prolonge le mot précédent (aujourd'hui, sous-titres, c'est)
            glued = mots and not w.word[:1].isspace() and (t[0] in "'’-" or mots[-1]["mot"][-1] in "'’-")
            if glued:
                mots[-1]["mot"] += t
                mots[-1]["fin_ms"] = int(w.end * 1000)
            else:
                mots.append({"mot": t, "debut_ms": int(w.start * 1000), "fin_ms": int(w.end * 1000),
                             "proba": round(w.probability, 2)})
    out = {"fichier": path.name, "langue": info.language, "appareil": device, "mots": mots, "segments": segments}
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def to_srt(mots, path, max_words=7):
    def ts(ms):
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    lines, i = [], 0
    for n in range(0, len(mots), max_words):
        grp = mots[n:n + max_words]
        i += 1
        lines += [str(i), f"{ts(grp[0]['debut_ms'])} --> {ts(grp[-1]['fin_ms'])}", " ".join(w["mot"] for w in grp), ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
