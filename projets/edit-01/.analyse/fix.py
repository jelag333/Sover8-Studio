p = "prep2.py"
s = open(p, encoding="utf-8").read()
a = s.index('    if p["role"] == "gros-plan":'); b = s.index("    return tau", a)
s = s[:a] + '''    if p["role"] == "gros-plan":             # N&B : l'image avance ; puis REVERSE (retour à l'état d'avant le N&B)
        base, cur, avant, apres = p["k"] * DEMI, 0.0, None, None
        tau = np.zeros(n)
        for i in range(n):
            g = p["debut"] + i * IMG - base
            a, b, c = NB_REVERSE[0]
            if a <= g < b:
                if avant is None:
                    avant = cur
                tau[i] = apres = cur
                cur += vmin / FPS
            elif b <= g < c and avant is not None:
                x = (g - b) / (c - b)
                tau[i] = apres + (avant - apres) * x * x * (3 - 2 * x)
                cur = avant
            else:
                tau[i] = cur
                cur += vmin / FPS
''' + s[b:]
open(p, "w", encoding="utf-8").write(s)
