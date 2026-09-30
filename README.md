# Sover8 Studio

Le studio de montage automatique construit avec **Sover8** (Claude) sur la CLI **Tesseract**, et **tout ce qui a été
appris** depuis le premier jour : dérushage, zooms, motion design, sound design, sous-titres, musique, colorimétrie,
transitions et edits.

**À lire en premier : [COURS-SOVER8.md](COURS-SOVER8.md)**, toutes les règles et méthodes avec leur pourquoi.

## Contenu

| Dossier | Ce qu'il contient |
|---|---|
| `COURS-SOVER8.md` | Le cours complet (règles, retours, méthodes, pièges) |
| `memoire/` | Les fiches mémoire brutes de Sover8 (une règle par fichier) |
| `skill/studio-tesseract/` | La skill que Sover8 charge à chaque montage (SKILL.md) |
| `vendor/skills/` | Les skills Tesseract officielles (vidéo et motion) |
| `outils/` | Le moteur du studio (`studio.py` et `lib/` : montage, stickers, glow, mix, sous-titres, transcription, banque SFX, catalogue…) et `icones.py` (fabrique de visuels) |
| `bibliotheque/` | `catalogue.json` (toutes les fiches, dont 2 565 SFX), le guide, les styles de sous-titres et de texte, les polices, les visuels créés (icônes, cartes, logos, photos arrondies) |
| `recettes/` | Recettes de montage (short vertical, talking head, pub produit) |
| `projets/` | Chaque montage réel : scripts (`zones.py`, `dynamique.py`, `habillage.py`, `prep*.py`, `edit*.py`), `plan.json`, comptes rendus, analyses de l'edit |
| `rendus/` | Les 6 vidéos finales (ignorées par git : trop lourdes) |

### Les projets, dans l'ordre

1. `fashion-tips-proportions` : zooms AE, pop 0 → 150 → 100, Deep Glow, premiers SFX, sous-titres sover8-pop.
2. `derush-img2950` : dérushage, J-cuts à 50 ms, zooms qui cadrent, visuels sans emoji, logo Boonbuy, musique.
3. `img2856` : colorimétrie, transitions flash photo, logos de marques, tampons BLOQUÉ / DISPONIBLES.
4. `img2893` : plaque PNJ motion-trackée, médailles avec glow et light sweep, tambour, confettis.
5. `img2859` : liste cochée, trajet vendeur → entrepôt, avion ANNULÉ.
6. `edit-01` : premier edit (reproduction de `tyyvixedit`, v1 → v3).

## Réinstaller sur une autre machine

1. `installer.ps1` : Python (venv), FFmpeg, faster-whisper (GPU), OpenCV, Pillow, CLI Tesseract (`tsrct` 0.2.0, somme de contrôle vérifiée).
2. Réimporter la banque SFX : `studio banque F:\sfx` (les fichiers audio ne sont pas dans le dépôt : banque premium, 1,2 Go), puis `studio ajouter` pour les musiques.
3. Copier `skill/studio-tesseract` dans `~/.claude/skills/` et `memoire/` dans la mémoire de Claude.
4. Monter : `studio monter Projets/<nom>/plan.json` (ou lancer les scripts d'un projet : `dynamique.py` puis `habillage.py`).

## Ce qui n'est pas dans le dépôt (volontairement)

Rushes et sources vidéo, sons de la banque SFX et musiques (droits), environnement Python (`.venv`), fichiers de travail
(`.studio-work`, `.tesseract-work`, plans intermédiaires). Les rendus sont dans `rendus/` mais exclus de git.
