"""Zones de parole (énergie) + transcription Whisper zone par zone -> .zones.json"""
import json, sys, wave
from pathlib import Path
import numpy as np

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI.parent.parent / "outils"))
HOP = 0.01

with wave.open(str(ICI / "rushes" / "voix-16k.wav")) as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
h = int(sr * HOP)
n = len(x) // h
e = 20 * np.log10(np.sqrt(np.mean(x[:n * h].reshape(n, h) ** 2, axis=1)) + 1e-9)
e = np.convolve(e, np.ones(5) / 5, mode="same")
fond = np.percentile(e, 10)
parle = e > fond + 14
zones, i = [], 0
while i < n:
    if parle[i]:
        j = i
        while j < n and (parle[j] or (j + 35 < n and parle[j:j + 35].any())):  # trous < 350 ms fusionnés
            j += 1
        if (j - i) * HOP > 0.35:
            zones.append([max(0, i * HOP - 0.15), min(n * HOP, j * HOP + 0.15)])
        i = j
    else:
        i += 1

from lib import transcription as T
if hasattr(T, "_cuda_dll_dirs"):
    T._cuda_dll_dirs()
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
out = []
for a, b in zones:
    seg = x[int(a * sr):int(b * sr)]
    segs, _ = m.transcribe(seg, language="fr", vad_filter=False, condition_on_previous_text=False, beam_size=5)
    txt = " ".join(s.text.strip() for s in segs).strip()
    crete = float(e[int(a / HOP):int(b / HOP)].max())
    out.append({"debut": round(a, 2), "fin": round(b, 2), "texte": txt, "crete_db": round(crete, 1)})
    print(f"{a:7.2f}-{b:7.2f} ({crete:5.1f} dB) {txt}")
(ICI / ".zones.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"fond {fond:.1f} dB, {len(out)} zones, durée {n * HOP:.1f} s")
