import subprocess, numpy as np
def diffs(f, a, b):
    raw = subprocess.run(["ffmpeg","-v","quiet","-ss",str(a),"-t",str(b-a),"-i",f,"-vf","scale=135:240","-f","rawvideo","-pix_fmt","gray","-"],capture_output=True).stdout
    x = np.frombuffer(raw, np.uint8).reshape(-1, 240, 135).astype(int)
    d = np.abs(np.diff(x, axis=0)).mean(axis=(1, 2))
    return (d < 0.3).mean()
for f in ("edit-01.mp4", "edit-01-v2.mp4"):
    print(f, "images répétées (rire, marche) :", round(diffs(f, 3.0, 3.35), 2), round(diffs(f, 4.3, 4.8), 2))
