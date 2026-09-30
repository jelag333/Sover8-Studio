import json, numpy as np
rows = json.load(open("mesures.json"))
plans = {"lunettes": (0, 43), "profil": (43, 85), "gros-plan": (85, 163), "rire": (163, 205), "bras": (205, 244), "marche": (244, 325)}
out = {}
for nom, (a, b) in plans.items():
    z, x, y, r = [1.0], [0.0], [0.0], [0.0]
    for i in range(a + 1, b + 1):
        m = rows[i]; ok = m.get("ok", 0) > 12 and m.get("sim_miroir", 0) <= m.get("sim", 1) and abs(m["zoom"] - 1) < 0.2
        dz, dx, dy, dr = (m["zoom"], m["dx"] / 360, m["dy"] / 360, m["rot"]) if ok else (1, 0, 0, 0)
        z.append(z[-1] * dz); x.append(x[-1] + dx); y.append(y[-1] + dy); r.append(r[-1] + dr)
    z, x, y, r = map(np.array, (z, x, y, r))
    k = np.ones(3) / 3
    lis = lambda v: np.convolve(np.pad(v, 1, mode="edge"), k, mode="valid")
    z = lis(z); x = lis(x); y = lis(y); r = lis(r)
    out[nom] = {"zoom": (z / z.min()).round(4).tolist(), "dx": x.round(4).tolist(), "dy": y.round(4).tolist(), "rot": r.round(2).tolist()}
    print(nom, len(z), "zoom max/min", round(z.max() / z.min(), 3))
json.dump(out, open("../courbes_ref.json", "w"))
