import cv2, numpy as np, json, wave, subprocess
R = r"C:\Users\mtzti\Downloads\transfer-01a0e3e7\référence edit\01_tyyvixedit_7667810913499548935.mp4"
cap = cv2.VideoCapture(R); rows = []; prev = None; i = 0
while True:
    ok, f = cap.read()
    if not ok: break
    s = cv2.resize(f, (270, 270)); g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(s, cv2.COLOR_BGR2HSV)
    sharp = cv2.Laplacian(g, cv2.CV_64F).var()
    diff = float(np.abs(g.astype(int) - prev.astype(int)).mean()) if prev is not None else 0
    rows.append((i / 60, float(g.mean()), float(hsv[..., 1].mean()), sharp, diff)); prev = g; i += 1
json.dump(rows, open(".analyse/frames.json", "w"))
# onsets audio
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", R, "-vn", "-ac", "1", "-ar", "22050", ".analyse/ref.wav"])
with wave.open(".analyse/ref.wav") as w:
    sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
h = 256; n = len(x) // h; fr = x[:n*h].reshape(n, h)
spec = np.abs(np.fft.rfft(fr * np.hanning(h), axis=1)); flux = np.maximum(0, np.diff(np.log1p(spec), axis=0)).sum(1)
flux = (flux - flux.mean()) / flux.std(); t = np.arange(1, n) * h / sr
peaks = [round(float(t[k]), 3) for k in range(2, len(flux) - 2) if flux[k] > 1.8 and flux[k] == flux[k-3:k+4].max()]
low = np.abs(np.fft.rfft(fr, axis=1))[:, 1:6].sum(1); low = (low - low.mean()) / low.std()
kicks = [round(float(k * h / sr), 3) for k in range(3, n - 3) if low[k] > 1.5 and low[k] == low[k-4:k+5].max()]
print("onsets:", peaks); print("kicks :", kicks)
f = np.array(rows)
print("\n t     lum   sat   net    diff")
for r in rows:
    tag = ""
    if r[4] > 25: tag += " COUPE"
    if r[3] < 60: tag += " FLOU"
    if r[2] < 25: tag += " N&B"
    if r[1] > 150: tag += " FLASH"
    if tag: print(f"{r[0]:5.2f} {r[1]:5.0f} {r[2]:5.0f} {r[3]:6.0f} {r[4]:5.1f}{tag}")
