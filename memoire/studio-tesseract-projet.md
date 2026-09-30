---
name: studio-tesseract-projet
description: "Studio Tesseract de l'utilisateur (Documents\\Studio Tesseract) — bibliothèque d'assets avec fiches d'usage + montage auto ; catalogue en ligne"
metadata:
  node_type: memory
  type: project
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-23T13:51:37.266Z
---

Construit le 2026-09-23 dans `C:\Users\mtzti\Documents\Studio Tesseract` : bibliothèque (catalogue.json, une fiche d'usage par élément), recettes, moteur Python (`studio.cmd`), skill `studio-tesseract`, `installer.ps1` portable. Catalogue en ligne : https://claude.ai/artifact/8jFWLxo2MCmibQbmqJS11s (URL aussi dans studio-config.json ; republier après chaque ajout).

2026-09-23 : banque SFX premium de l'utilisateur (F:\sfx, 3 555 fichiers) importée via `studio banque` → 2 565 sons uniques (dont 1 146 Motion SFX « Thème [Courbe] »), carte dans bibliotheque/GUIDE-BIBLIOTHEQUE.md. Page en ligne limitée à 255 fichiers/version : écoute seulement pour une sélection (~100 sons) ; publier les suppressions et les ajouts en deux fois si besoin.

**Why:** l'utilisateur veut un système où tout ce qu'il ajoute (SFX, musiques, VFX, textes animés, sous-titres) est « installé » avec la compréhension de quand/comment l'utiliser, une page HTML téléchargeable, et des montages automatisés.
**How to apply:** suivre le skill studio-tesseract ; l'utilisateur a dit avoir ses propres fichiers à installer (pas encore fournis au 2026-09-23). Pièges connus : [[user-language-french]] ; un commit tsrct retire les polices inutilisées (importer après commit) ; utiliser les noms typographiques (Poppins/Black).
