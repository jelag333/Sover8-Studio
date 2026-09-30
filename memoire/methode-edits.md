---
name: methode-edits
description: "Les « edits » (clips + effets calés sur une musique) — méthode apprise le 2026-09-28, gros sujet pour l'utilisateur"
metadata:
  node_type: memory
  type: project
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-30T09:12:46.064Z
---

Un **edit** = plusieurs moments d'un ou plusieurs clips, avec des effets calés sur une musique stylée. L'utilisateur fournit les clips et la musique (et des edits de référence à reproduire). Il veut du très clean : « mets-toi dans la peau du meilleur éditeur du monde ». Premier edit : Projets/edit-01, modèle `tyyvixedit`, clips dans Downloads\OUTPUT…

Méthode qui marche :
1. **Décortiquer la référence image par image** : planches horodatées, puis mesures par image (coupes, flou, N&B, flash) croisées avec les onsets audio. Le fichier CapCut affiche des erreurs H.264 sans conséquence : utiliser `-v quiet`.
2. **Reproduire la même table d'événements** (coupes, transitions zoom/fouet, flashs N&B, secousses) dans un générateur Python (`edit.py`). Les effets tsrct sont animés par JS sur le temps global (`setFxLayerEffectParamAnimator` : radialBlur, directionalBlur, hueSaturation, brightnessContrast, sharpen, temperatureTint, levels, vignette).
3. **Comparer côte à côte référence / version aux mêmes instants**, puis corriger. Première erreur constatée : des flous trop faibles et trop courts. Les bonnes valeurs : radial 60, sortie 140 ms, entrée 160 ms.
4. Export en 60 i/s, en 9:16. Le rendu est très rapide (20 s).

Retour sur la v1 (2026-09-30) : « niveau débutant, pas assez smooth ». Leçons pour la v2 :
- **Fluidité** : ne jamais poser des clips en 24 i/s tels quels dans un edit en 60 i/s. `prep.py` : flux optique 120 i/s (minterpolate mci/aobmc/bidir), puis courbe de vitesse type Twixtor (rapide près des coupes, ralenti au centre). Chaque image doit être unique.
- **Analyser à 60 i/s en pleine résolution**, pas avec des planches à 12 i/s. Les effets courts (1 à 5 images) y étaient invisibles : images glitch (smear datamosh) et alternance glitch / N&B / couleur toutes les ~100 ms.
- Le N&B « sombre » s'assombrit **progressivement**, puis la couleur revient d'un coup sur le temps.
- **Flou radial à centre net** : shader `zoomBlurCentreNet` (le flou croît avec la distance au centre). Le RadialBlur natif est trop uniforme.
- Entrées de transition : se nettoyer en 3 à 4 images, sans trop zoomer sur un gros plan.
- Code : `edit-01/edit2.py` (shaders WGSL GLITCH et ZOOM_BLUR prêts à réutiliser).

Retour sur la v2 (2026-09-30) : « analyse-la 20 fois, reproduis à l'identique : inverse, zoom, shake, blur ». Méthode v3 :
- **MESURER plutôt que regarder** (`.analyse/profonde.py`) : image par image, similarité avec l'image précédente ET avec son **miroir** (ce qui détecte les retournements), mouvement 2D ORB → zoom, dx, dy, rotation cumulés par plan (`courbes_ref.json`). Ces courbes sont ensuite **appliquées telles quelles** aux plans.
- Les « glitchs » de la référence étaient des **retournements miroir** en rythme. Le smear est l'image d'interpolation par flux optique entre l'image et son miroir (`bascule()` dans prep2.py). Ne marche que sur un plan **asymétrique** (profil, 3/4), pas sur un visage de face.
- **Reverse** : le N&B avance, puis rembobinage en ~60 ms au retour de la couleur (loi de temps dans prep2.py).
- Les « shakes » de la marche sont des **coups de zoom +20 % avec rotation −7°** sur le temps, relâchés au temps suivant. Le flou vient de la vitesse du mouvement : flou proportionnel à |Δzoom| et |Δrot|, plus le flou de mouvement.
- Attention : le suivi mesure aussi le mouvement de l'ACTEUR (tête qui baisse). Sur ces plans, remplacer la courbe par le vrai geste de montage.
- Fichiers : prep2.py (plans3/) + edit3.py.

**How to apply:** repartir de edit-01/edit.py (ROLES, CHOIX, table d'événements) pour chaque nouvel edit ; varier les plans d'une répétition à l'autre. Voir [[style-etalonnage-transitions]].
