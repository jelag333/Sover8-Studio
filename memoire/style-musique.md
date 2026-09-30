---
name: style-musique
description: "Règles musique de fond de l'utilisateur — douce, qui accompagne, style trend TikTok / rap / trap / instrus"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-26T09:56:57.443Z
---

Musique de fond : **douce, jamais forte**, elle accompagne la voix. Style **jeune et trend** : sons TikTok du moment, rap US (Travis Scott, Drake…), rap FR, instrumentales rap/trap. Le droit d'auteur ne le préoccupe pas. Moi, je ne récupère pas des morceaux commerciaux sur des sites non officiels : j'utilise la bibliothèque, et il peut déposer ses sons dans A-AJOUTER/musiques.

Méthode validée en interne (IMG_2950, 2026-09-26) :
- musique environ 20 dB sous la voix (repères : −18 à −25 dB) ;
- EQ creusée de 3 à 4 dB autour de 1,2 kHz (zone de la voix) ;
- calage sur la structure du beat (retombée sur le problème, drop sur le retournement) ;
- fondu d'entrée court, fondu de sortie de 0,7 s.

Il m'a aussi demandé d'aller plus vite (la v3 a pris 1 h 20) tout en restant appliqué.

**Why:** consignes du 2026-09-26.
**How to apply:** `plan["musique"]` avec `volume_sous_voix`, puis mesure par soustraction de la voix. Mesure l'écart. Voir [[no-sfx-sans-demande]], [[contexte-reps-boonbuy]].
