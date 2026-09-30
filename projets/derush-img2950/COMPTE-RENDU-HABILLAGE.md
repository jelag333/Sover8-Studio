# IMG_2950 — v3 (Sover8)

29,6 s · 1080×1920 · 30 i/s · voix −12,8 LUFS

## Ce qui change par rapport à la v2
| Retour | Correction |
|---|---|
| Blanc entre les phrases → 50 ms | 50 ms entre la fin d'une phrase et l'attaque de la suivante, fondus croisés, J-cut de 2 images |
| « Boonbuy » | orthographe corrigée dans les sous-titres (Whisper l'entend « Boombuy / Boonbaï ») |
| Lueur jaune pas obligatoire | plus de lueur jaune : **ombre portée diffuse** noire + ombre nette sur tous les objets ; l'ampoule seule garde une lueur (elle éclaire, c'est son sens) ; rien sous l'interdit (pour ne pas salir le colis) |
| Cadrer la personne en zoomant | zooms 1,35 à 1,6, visage à 36 % de la hauteur : tête + épaules remplissent l'image. Source refaite en **1440p depuis le 4K** pour rester net |
| Améliorer le sound design | 5 sons en plus, chacun avec un sens (voir plus bas) |
| Essayer d'autres habillages | **flash rouge** d'alerte sur « bloqué », **flash blanc** sur « je te rassure » (retournement) |

## Zooms
| Mot | Zoom | Pourquoi |
|---|---|---|
| « la fin de la **REP** » | 1,55 | le choc de l'accroche |
| « je vous **explique** » | 1,40 | la promesse |
| « le colis est **bloqué** » | 1,60 (le plus serré) | le moment le plus fort, avec flash rouge + interdit + son d'erreur |
| « je te **rassure** » | 1,35, lent | le retournement, ton doux |
| « c'est **toujours pas** la fin » | 1,50 | la chute, même cadre que l'accroche |
| « et si tu veux commander » | retour large | place aux coupons |
Plans « Étiquette » et « Agents » : cadre fixe 1,15 pour masquer le saut entre deux prises.

## Sound design (16 sons, 19 à 24 dB sous la voix)
Nouveaux :
- **clic** sur les 2 téléphones en cascade ;
- **souffle ease-out** sur le zoom de la promesse, et un plus doux sur celui de « je te rassure » (même courbe que la caméra) ;
- **papier** sur la déclaration ;
- **même impact qu'à l'accroche** sur « c'est toujours pas la fin de la REP » : rappel sonore de la phrase du début.

Déjà là : impact de l'accroche, pops (téléphone, t-shirt, étiquette, colis grave), bip de scanner, son d'erreur, scintillement, clic du lien, caisse, pièces.

## Technique
- Source courte `rushes/selects-1440.mp4` : seulement les 8 prises utilisées, calées à l'image près (contrôle automatique image par image). Rendu en 3 min au lieu de plus de 40.
- `outils/icones.py photo` : prêt pour les images du web (coins légèrement arrondis, jamais de bords bruts).
