---
name: methode-derushage
description: "Méthode de dérushage apprise le 2026-09-25 (IMG_2950) — une prise par phrase, coupes très serrées, J-cuts, vérif par transcription"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-25T20:48:19.781Z
---

Dérushage = retirer blancs, bégaiements, répétitions, faux départs, ratés ; garder une vidéo dynamique et clean. Demandé le 2026-09-25 (IMG_2950 : 5 min 49 → 30,9 s, validé « très bon dérush »).

Retour suivant (même jour) : **encore trop de blancs entre les coupes** → coupes serrées (100 ms entre phrases), pistes son qui se chevauchent en fondu croisé, **J-cut** (le son de la phrase suivante arrive avant l'image). Il me laisse juger seul du choix des prises (« c'est à toi d'évaluer : est-ce que l'auditeur reste, est-ce compréhensible »).

**Why:** ses rushs face caméra répètent chaque phrase plusieurs fois ; les petits blancs parasites cassent le rythme.
**How to apply:** zones de parole par énergie → Whisper par zone → une prise complète par phrase → voix pré-mixée serrée + J-cut 2 images → cadre alterné à chaque coupe pour masquer les sauts → retranscrire pour vérifier. Puis habillage complet (zooms, objets, SFX, sous-titres) si demandé. Détails dans la skill studio-tesseract. Voir [[studio-tesseract-projet]], [[style-zooms]], [[style-habillage]].
