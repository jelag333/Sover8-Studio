# Studio Tesseract

Ton studio de montage local : une bibliothèque qui **retient comment utiliser** chaque son, musique, effet et style de texte, et un montage automatique qui s'en sert.

## Au quotidien

| Je veux… | Je fais… |
|---|---|
| Ajouter des sons, musiques, VFX, images, polices | Je les dépose dans `A-AJOUTER` (rangés dans `sfx`, `musiques`, `ambiances`, `vfx`, `images`, `polices` si possible) et je dis à Claude « installe mes nouveaux éléments » — ou `studio ajouter` |
| Voir / écouter / télécharger la bibliothèque | J'ouvre `catalogue.html` (ou la version en ligne) |
| Monter une vidéo | Je donne mes rushes à Claude avec le format et l'idée — ou `studio auto mes-rushes.mp4 --recette short-vertical --accroche "Mon *hook*"` |
| Corriger une fiche | `studio modifier <id> --quand "…" --eviter "…" --volume 0.3 --valider` |
| Créer un nouveau style de texte ou de sous-titres | Je le décris à Claude, il écrit le style et rend son aperçu |

## Ce qu'il y a dedans

- `bibliotheque/` : les fichiers + `catalogue.json` (une fiche par élément : rôle, quand l'utiliser, quoi éviter, où le caler, volume, mesures)
- `recettes/` : les modèles de montage (short vertical, YouTube face caméra, pub produit)
- `Projets/<nom>/` : chaque montage — `plan.json` (le plan modifiable), `<nom>.tsrct` (projet Tesseract éditable), `<nom>.mp4`, `Previews/Filmstrip.png`, `Versions/`
- `outils/` : le moteur (Python) · `studio.cmd` : le lanceur
- `skill/` et `vendor/skills/` : les instructions pour Claude (Studio + Tesseract)

## Installer sur un autre PC

Copie tout le dossier (le sous-dossier `.venv` peut être omis), puis :

```
powershell -ExecutionPolicy Bypass -File installer.ps1
```

Il installe ou vérifie la CLI Tesseract 0.2.0 (somme SHA-256 contrôlée), Python, FFmpeg, Whisper (+ CUDA si carte NVIDIA) et les skills Claude. Aucun droit administrateur requis.

## Commandes

`studio ajouter | liste | fiche | modifier | supprimer | transcrire | auto | monter | apercus | page [--en-ligne] | verifier` — `studio <commande> -h` pour le détail.
