---
name: style-habillage
description: "Préférences de l'utilisateur pour l'habillage motion design (objets/images qui apparaissent quand on en parle)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-26T14:02:13.181Z
---

Habillage : faire apparaître ce dont la personne parle, accordé au mot près. Objets **centrés** (paires symétriques autour du centre), **jamais déformés**, pop 3 clés 0 → 150 → 100 %, sans rebond, aucune image fantôme, mouvement fluide et vivant. **Toujours une ombre portée.**

Mise à jour 2026-09-25 (IMG_2950) :
- **Lueur libre** : la lueur jaune était liée au sujet de la vidéo mode (vêtements jaunes). Désormais je choisis la couleur, ou pas de lueur du tout (ombre seule), selon ce qui rend le mieux.
- **Images d'Internet autorisées et encouragées** : elles doivent avoir un contexte, être liées au propos, de bonne qualité et **sans watermark**. Le droit d'auteur ne le préoccupe pas, mais les téléchargements restent soumis à confirmation, fichier par fichier.
- **Images rectangulaires : coins légèrement arrondis** (pas exagérés), jamais de bords bruts, plus une ombre portée.
- Il m'encourage à essayer d'autres habillages : il corrigera.

Mise à jour 2026-09-26 :
- **Pas que des emojis**, et **jamais les emojis Windows/Segoe** : il les trouve moches (« style Android »). À la limite, des emojis Apple.
- Il préfère de vrais visuels : photos réelles contextuelles, cartes dessinées, maquettes d'interface, tampons, laser de scan…
- Je peux chercher les images sur Internet moi-même ; il me corrige si je me trompe. Wikimedia : télécharger via l'URL `thumb/…/1280px-…` avec un User-Agent descriptif, sinon erreur 429.
- Les grandes photos ont un pop réduit (pic 120 %) et ne doivent pas cacher le visage.

Mise à jour 2026-09-26 (IMG_2893, il adore les essais) :
- Un élément collé à une personne (plaque PNJ) doit être **motion-tracké**. Utiliser `deplacements` tous les 100 ms depuis le suivi du visage, avec `suivi_ms` de 220. La pointe se pose juste au-dessus de la casquette (haut de la tête ≈ centre du visage − 0,83 × hauteur du visage).
- **Un badge (médaille) passe toujours DEVANT l'image** qu'il décore : il vient après elle dans la liste des stickers.
- **Médailles** : petit glow de LEUR couleur, animé au pop (`lueur_anim`, `lueur_rayon` 0.6, `lueur_opacite` 95, `lueur_intensite` 1.6), plus un **light sweep** (`reflet`), découpé à la forme de l'objet.

**Why:** retours du 2026-09-23 (fashion-tips) et du 2026-09-25 (IMG_2950).
**How to apply:** `add_stickers` + `outils/icones.py` (emoji, cartes, photos arrondies) du [[studio-tesseract-projet]] ; voir aussi [[no-sfx-sans-demande]] et [[style-zooms]].
