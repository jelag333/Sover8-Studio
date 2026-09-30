---
name: style-etalonnage-transitions
description: Colorimétrie douce à chaque montage + petites transitions flash (déclencheur photo) entre certaines coupes ; rendu en 40 min max
metadata:
  node_type: memory
  type: feedback
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-26T13:44:08.087Z
---

À chaque montage (demandé le 2026-09-26) :
- **Colorimétrie douce**, même minime : couleurs plus vives, meilleure qualité perçue. Réglage validé (IMG_2856), appliqué à l'encodage des prises : `curves` en S légère, `vibrance` 0.22, saturation +6 %, pointe de chaleur, micro-netteté (variable ETALO de Projets/img2856/dynamique.py).
- **Transitions** : de temps en temps, un petit flash blanc sur une coupe entre deux idées, avec un SFX de déclencheur photo (`clic-de-photo-09`). Pas partout.
- **Délai** : 40 minutes maximum par vidéo, rendu compris. Méthode rapide : analyser le son, choisir les prises, puis encoder seulement les prises retenues depuis le 4K.
- Il m'envoie plusieurs musiques : je choisis la meilleure et je dis pourquoi. Une musique chantée se met plus bas.

- Il m'encourage à **tester de nouveaux styles** (animations, SFX). Essayé sur IMG_2893 :
  - plaque de PNJ façon jeu vidéo au-dessus de la tête, placée par le suivi du visage ;
  - médailles #3 / #2 / #1 et vraies photos produits ;
  - roulement de tambour avant une révélation, confettis + corne de fête, level-up.
- Méthode (IMG_2893) : premier mot de chaque prise repéré par la prise, jamais par le texte ; niveau de chaque prise égalisé dans la piste voix ; début « strict » pour couper une reprise collée.

**Why:** retours du 2026-09-26 (« ça rend 25 fois mieux que les vieux emojis », motion design jugé impeccable).
**How to apply:** pipeline Projets/img2856 (zones.py → dynamique.py → habillage.py), `plan["flashs"]`. Voir [[style-habillage]], [[style-musique]], [[methode-derushage]].
