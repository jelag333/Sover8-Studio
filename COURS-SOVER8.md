# Le cours de Sover8 — tout ce que tu m'as appris depuis le début

> Sover8 (« sover-eight ») : l'IA monteuse du Studio Tesseract. Ce document rassemble **toutes les règles, méthodes et
> corrections** apprises vidéo après vidéo, avec le *pourquoi* (ton retour) et le *comment* (où c'est codé).
> Ordre chronologique d'apprentissage : zooms → habillage → SFX → sous-titres → dérushage → rythme/J-cut →
> images web → musique → colorimétrie → transitions → nouveaux styles → edits.

---

## 0. Façon de travailler

- **Toujours en français.** Je m'appelle **Sover8**.
- **Questions à la toute fin des messages** : tu lis surtout la fin et tu regardes la vidéo.
- **Chaque rendu s'accompagne d'un compte rendu** : chaque zoom, objet et son, avec *le mot, le moment et le pourquoi*.
- **Délai** : un montage complet (dérush, habillage, SFX, musique, colorimétrie) prend **40 min maximum**, rendus compris. « Ne confonds pas vitesse et précipitation. »
- **Essayer de nouveaux styles** (animations, SFX) : tu corriges ensuite. « Tente, essaye, je suis derrière toi. »
- Je ne peux pas écouter : je **mesure** (niveaux par soustraction, analyse image par image), et je le dis.

---

## 1. Zooms

**Règle** (Fashion Tips, avec ton graphe de vitesse After Effects) :
- **2 clés par zoom**, courbe **ease-out `cubic-bezier(0.30, 0, 0.06, 1)`** : pic de vitesse à ~20 %, longue décélération, 0,6 à 1 s.
- **Cadre fixe** entre deux zooms, sans suivi continu : le suivi en continu donnait un effet « shake » que tu as refusé.
- **Qualité plutôt que quantité** : on zoome sur les **bons mots** (punchline, chute, démonstration, appel à l'action). On revient au plan large au début de l'idée suivante. Jamais pendant que le sujet avance ou recule (son mouvement est déjà un zoom).
- **Cadrer la personne** (IMG_2950) : un zoom doit donner un vrai plan serré (tête et épaules, visage à ~36 % de la hauteur, zoom 1,35 à 1,6), pas un petit grossissement.
- Source **HD** : proxy 1440p tiré du 4K pour que les zooms restent nets.
- **Masquer les sauts entre deux prises** en changeant de cadre à chaque coupe (large ↔ serré, `"zoom": 1.15`).

Code : `outils/lib/montage.py → add_zooms` (champ `pourquoi` obligatoire sur chaque zoom).

---

## 2. Habillage / motion design (objets qui apparaissent sur le mot)

**Principe** : quand la personne parle d'une chose, **cette chose apparaît exactement sur le mot**, avec une animation qui illustre le propos. Le sujet change à chaque vidéo.

- **Centré** : un objet seul au centre. Pour une comparaison, les objets se placent de part et d'autre du centre (et glissent avec `deplacements`).
- **Jamais déformé** : échelle toujours proportionnelle.
- **Pop de référence** (tes 2 graphes AE) : **exactement 3 clés, 0 % → 150 % → 100 %** (233 ms puis 700 ms, même courbe ease-out). **Jamais de 4e étape**, pas de pulsation ni d'anticipation (ce sont des rebonds). Sortie = simple rétrécissement de 250 ms. Opaque dès la 1re image, calé sur la grille d'images.
- **Ombre portée toujours** : une ombre nette (décalage [9, 11], flou 4), plus une ombre diffuse (mode `"ombre"`).
- **Lueur** : au départ, Deep Glow jaune-orangé (#FFC21A), parce que la vidéo mode parlait de vêtements jaunes. Aujourd'hui elle est **libre** : une couleur qui a du sens (l'ampoule éclaire, les médailles ont la couleur de leur métal), ou **aucune**.
- **Apparaître un peu avant le mot** (~100 ms), sinon l'objet semble arriver en retard.
- **Plus d'emojis Windows** (« style Android, pas beau »). À la limite des emojis Apple. De préférence de **vrais visuels** :
  - **photos réelles** contextuelles : logos officiels, produits (Moncler, Canada Goose, Burberry), avion cargo, étiquette de douane… en bonne définition, **sans watermark**, **coins légèrement arrondis** (jamais de bords bruts), avec ombre ;
  - **cartes dessinées** : calendrier, coupon, code-barres, bandeau FLASH INFO, pastilles barrées, carte mystère, courbe qui monte, trajet vendeur → entrepôt, commentaire façon appli, drapeau ;
  - **gestes graphiques** : tampons qui s'écrasent (BLOQUÉ, FINITO, ANNULÉ en rouge ; OUVERT, DISPONIBLES en vert, en écho), laser de scan, liste cochée qui se remplit mot par mot, maquettes de téléphone avec les propres prises du créateur.
- **Grandes photos** : pop plus doux (pic à 120 %) et jamais sur le visage.
- **Un badge (médaille) passe devant l'image** qu'il décore.
- **Nouveautés validées (IMG_2893)** :
  - **plaque de PNJ façon jeu vidéo** au-dessus de la tête, **motion-trackée** (suivi du visage toutes les 100 ms), avec la pointe juste au-dessus de la casquette. En running gag : niveau 1 → 50 → MAX ;
  - **médailles #1 / #2 / #3** avec un **petit glow de leur couleur**, animé au pop ;
  - un **light sweep** (reflet qui balaie l'objet, découpé à sa forme).

Code : `outils/lib/montage.py → add_stickers` (lueur, ombre, reflet, suivi), `outils/lib/glow.py` (deep_glow, soft_shadow, reflet_images), `outils/icones.py` (toutes les cartes dessinées, photo arrondie, plaque PNJ, médailles…).

---

## 3. Sound design (SFX)

- Les SFX **habillent** : apparitions, moments drôles, moments clés, changements de musique. **Toujours en fond, gain bas, juste milieu**, pas sur chaque phrase.
- Apparitions : pop, swoosh, impact. Moment drôle : son goofy. Mouvement de caméra : Motion SFX de la même courbe.
- **Niveau** : environ **19–20 dB sous la voix** (appris : −3 dB de moins sur les apparitions, entre −1 et −4 dB). Règle de ton oreille : « si l'oreille l'entend, c'est bien ; sinon, pas grave ».
- **Un son qui raconte** : pop grave pour un gros objet, aigu pour un petit ; le même son pour une idée répétée (le coup du tampon BLOQUÉ repris sur DISPONIBLES) ; bip de scanner sur un code-barres ; caisse enregistreuse et pièces sur les coupons ; roulement de tambour qui finit pile sur une révélation ; corne de fête sur « félicitations » ; level-up sur la plaque niveau MAX ; déclencheur photo sur les transitions flash.
- **Vérification** : je soustrais la voix du mixage final pour mesurer chaque SFX.

Code : `outils/lib/mix.py` (gain sous la voix par rôle, `sous_voix_db`), `add_sfx` (`calage`, `source_debut_ms`, `duree_ms`).

---

## 4. Sous-titres

- Style **`sover8-pop`** : blanc, Poppins Bold ~62 px, halo noir doux, **pop-in mot à mot** « mousse » (45 → 106 → 100 %, petite montée, apparition en 2 images), ancré à gauche.
- **Une seule ligne fixe** (80 % de la hauteur). Ce sont les objets qui se placent au-dessus.
- **Découpe au sens, écrite à la main** (`lignes`) : jamais de mot orphelin, de nom coupé ou de petit mot en fin de ligne.
- **Couleur avec parcimonie** : 5 à 8 mots dorés (promesse, contraste, chute, offre), ciblés dans le temps.
- Orthographe exacte des noms : **Boonbuy**, Sugargoo, Stüssy…

Code : `outils/lib/presets.py → build_subtitles_pop`, preset `bibliotheque/sous-titres/sover8-pop.json`.

---

## 5. Dérushage

**Définition** : retirer tous les blancs, bégaiements, répétitions, faux départs et ratés, pour garder une vidéo **dynamique et clean**.

Méthode :
1. Zones de parole par énergie, puis **Whisper zone par zone** (l'alignement global casse sur les hésitations).
2. **Une prise par phrase** : complète, fluide ; à égalité, la dernière.
3. Retranscrire chaque plan pour vérifier.
4. **Premier mot de chaque prise repéré par la prise, jamais par le texte** : « c'est », « et », « en » existent aussi au milieu des phrases. Ce bug décalait tout l'habillage.
5. Option **début strict** pour couper une reprise collée (« Bon, » ou « Top 3, c'est » répétés).

**Rythme (ton retour « encore des blancs »)** :
- **50 ms** entre la fin d'une phrase et le début de la suivante ;
- queues et attaques **en fondu croisé** dans une piste voix pré-mixée ;
- **J-cut** : la vidéo coupe 2 images après l'arrivée du son suivant ;
- **niveau égalisé d'une prise à l'autre**, voix remontée vers −15 LUFS, limiteur final à −1 dB.

Code : `projets/*/zones.py`, `dynamique.py` (coupes, J-cuts, voix pré-mixée, source courte 1440p calée à l'image près).

---

## 6. Musique

- **Douce**, elle accompagne : **~20 dB sous la voix** (repères −18 à −25 dB), creux d'EQ vers 1,2 kHz si besoin.
- Style **jeune / trend TikTok** : rap US, rap FR, instrus trap. Tu m'envoies plusieurs sons, **je choisis et je dis pourquoi** :
  - un son **sans chant** passe mieux sous une voix ;
  - un son **chanté** se met plus bas ;
  - j'écarte un fichier cassé (presque silencieux).
- **Caler la structure** : drop sur la fin de l'accroche ou sur le retournement, retombée sur le problème.

Code : `plan["musique"]` (`source_debut_ms`, `volume_sous_voix`).

---

## 7. Colorimétrie et transitions

- **Colorimétrie douce à chaque montage**, même minime : contraste en S léger, vibrance, saturation +6 %, pointe de chaleur, micro-netteté. Appliquée à l'encodage des prises (variable `ETALO`).
- **Transitions** : de temps en temps, un **flash blanc** sur une coupe entre deux idées, avec un **déclencheur photo** en SFX. Tu as validé : 3 ou 4 par vidéo, pas partout.
- Essai validé : voile rouge d'alerte sur un moment grave.

Code : `dynamique.py → ETALO`, `plan["flashs"]`.

---

## 8. Les edits (le gros sujet)

**Définition** : plusieurs moments d'un ou plusieurs clips, avec des effets calés sur une musique stylée. Tu fournis les clips, la musique et des edits de référence à reproduire.

**Leçons, dans l'ordre des corrections :**
1. **v1, « niveau débutant »** : j'avais analysé la référence à 12 images/s et raté tous les effets de 1 à 5 images.
2. **v2, fluidité** : jamais de clips 24 i/s tels quels dans un edit à 60 i/s. Il faut un ralenti par **flux optique à 120 i/s** puis une **courbe de vitesse type Twixtor** (rapide près des coupes, lent au centre). Chaque image doit être unique.
3. **v3, « analyse-la 20 fois »** : il faut **MESURER** la référence image par image :
   - la similarité avec l'image précédente **et avec son miroir**, ce qui détecte les **retournements** ;
   - le **mouvement ORB** entre deux images : zoom, décalage, rotation, cumulés par plan ;
   - la netteté, la saturation, la luminosité.

   Ensuite, on **applique les courbes mesurées** aux nouveaux plans.
4. **Effets identifiés sur `tyyvixedit`** :
   - zoom puis dézoom avec shake ;
   - **retournement miroir en rythme**, avec une image d'interpolation par flux optique à chaque bascule ;
   - N&B qui s'assombrit progressivement, puis **reverse** au retour de la couleur ;
   - coups de zoom avec rotation sur les temps (les « shakes ») ;
   - flou proportionnel à la vitesse du mouvement, flou radial à **centre net** (shader) ;
   - étalonnage ciné (noirs denses, teinte froide).
5. Un miroir ne se voit que sur un **plan asymétrique** (profil, trois-quarts). Et le suivi mesure aussi l'acteur : sur ces plans, il faut remplacer la courbe mesurée par le vrai geste de montage.

Code : `projets/edit-01/` → `.analyse/profonde.py` (mesures + graphique), `courbes_ref.json`, `prep2.py` (flux optique, loi de temps, miroirs, bascules, reverse), `edit3.py` (courbes appliquées, shaders WGSL `zoomBlurCentreNet`), `edit2.py` (shader `glitchSmear`).

---

## 9. Pièges techniques retenus

- `tsrct` : un commit retire les polices inutilisées, donc importer les polices **après** le commit, avec leurs noms typographiques. Deux *styles* sur un calque : seul le dernier est rendu (l'ombre doit être un *effet*).
- Chemins de plus de 260 caractères : `tsrct` échoue.
- Rendu lent sur un long rush 1440p : faire une **source courte** (seulement les prises), calée à l'image près.
- Wikimedia : passer par l'URL `thumb/…/1280px-…` avec un User-Agent descriptif, sinon erreur 429.
- Fichiers CapCut : erreurs H.264 sans conséquence, lire avec `-v quiet`.
- PowerShell : `Set-Content` en UTF-8, remplacements multilignes sensibles aux fins de ligne (CRLF/LF).

---

## 10. Contexte métier

- Vidéos **REP** (commandes via agent Taobao). **Boonbuy** = l'agent partenaire (logo fourni, lien en bio, −40 % et −500 $ de coupons).
- Formats : TikTok 9:16, 30 i/s pour les vidéos face caméra, 60 i/s pour les edits.
