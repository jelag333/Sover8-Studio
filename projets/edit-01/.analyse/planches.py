import json, cv2
from PIL import Image, ImageDraw, ImageFont
rows = json.load(open("mesures.json"))
R = r"C:\Users\mtzti\Downloads\transfer-01a0e3e7\référence edit\01_tyyvixedit_7667810913499548935.mp4"
cap = cv2.VideoCapture(R); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 20)
def planche(a, b, nom, pas=1):
    idx = list(range(a, b, pas)); cols = 8; sz = 250
    im = Image.new("RGB", (cols * sz, ((len(idx) + cols - 1) // cols) * sz), "black"); d = ImageDraw.Draw(im)
    for k, i in enumerate(idx):
        x = Image.fromarray(cv2.cvtColor(cv2.resize(fr[i], (sz, sz)), cv2.COLOR_BGR2RGB))
        im.paste(x, ((k % cols) * sz, (k // cols) * sz))
        r = rows[i]; m = r.get("sim_miroir", 0) > r.get("sim", 1)
        d.text(((k % cols) * sz + 4, (k // cols) * sz + 4), f"{i} {r['t']:.3f}{' MIROIR' if m else ''}", font=f, fill=(255, 60, 60) if m else (255, 255, 0))
    im.save(nom)
planche(55, 87, "p_profil_a.png")
planche(87, 119, "p_profil_b.png")
planche(104, 136, "p_gros_a.png", 1)
