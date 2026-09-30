# Dérush IMG_2950 — compte rendu (Sover8)

Rush de 5 min 49 s, réduit à **30,9 s** (8 plans, 1080×1920, 30 i/s, voix normalisée vers −14 LUFS).

## Méthode
1. Détection de la parole sur l'énergie de la voix, puis transcription de chaque zone séparément (Whisper large-v3-turbo).
2. Regroupement des zones par phrase du script : chaque phrase avait été dite 1 à 7 fois.
3. Choix d'**une seule prise par phrase** : complète, fluide, sans bégaiement ; à égalité, la dernière, souvent la plus assurée.
4. Coupe au plus près : 90 ms de respiration avant la parole et 160 ms après, sans mordre sur la prise voisine.
5. Vérification : chaque plan est retranscrit (texte complet, aucun blanc interne de plus de 250 ms).

## Prises retenues
| # | Phrase | Rush | Pourquoi |
|---|---|---|---|
| 1 | « C'est la fin de la REP, le 1er novembre. » | 23,97–25,93 | 7e et dernière prise de l'accroche : la plus posée |
| 2 | « Vous avez sûrement dû voir plein de TikTok… » | 51,75–56,26 | seule prise complète, les essais de 38 à 47 s cassent |
| 3 | « À partir du 1er novembre, chaque article doit avoir un identifiant produit… » | 150,81–155,19 | la plus fluide des 5 prises complètes |
| 4 | « En gros, ce sera une étiquette qui dit exactement ce qu'il y a dans le colis. » | 222,09–224,83 | dernière prise, la plus claire |
| 5 | « Et s'il n'y a pas cette étiquette… reste à la frontière. » | 261,91–266,09 | seule prise complète |
| 6 | « Je te rassure tout de suite, c'est pas toi qui remplis ça… » | 276,85–279,69 | dite d'un seul souffle |
| 7 | « Les agents comme Boonbuy ont déjà trouvé des solutions… ne vous inquiétez pas. » | 304,20–307,84 | version avec la chute rassurante |
| 8 | « Bref, c'est toujours pas la fin de la REP… coupon sur ta livraison. » | 338,42–345,05 | seule prise complète du CTA |

## Retiré
Faux départs, reprises, phrases dites plusieurs fois, les essais de 65 à 93 s (texte buté et voix basse), les blancs entre les prises et les bruits de fond.
