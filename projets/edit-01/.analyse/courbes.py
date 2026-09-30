import json, numpy as np
rows = json.load(open("mesures.json"))
plans = [("A lunettes", 1, 43), ("B profil", 44, 85), ("C gros plan", 86, 163), ("D rire", 164, 205), ("E bras", 206, 244), ("F marche", 245, 324)]
for nom, a, b in plans:
    z, x, y, r = 1.0, 0.0, 0.0, 0.0; out = []
    for i in range(a, b + 1):
        m = rows[i]
        miroir = m.get("sim_miroir", 0) > m.get("sim", 1)
        if m.get("ok", 0) > 12 and not miroir and abs(m["zoom"] - 1) < 0.2:
            z *= m["zoom"]; x += m["dx"] / 360; y += m["dy"] / 360; r += m["rot"]
        out.append((i, z, x, y, r))
    print(f"== {nom} ({a/60:.2f}-{b/60:.2f}s)")
    print("   t     zoom    dx%   dy%   rot")
    for i, z, x, y, r in out[::3]:
        print(f"  {i/60:5.2f}  {z:6.3f} {100*x:6.1f} {100*y:6.1f} {r:5.1f}")
