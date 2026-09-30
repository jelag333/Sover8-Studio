---
name: studio-tesseract
description: Studio de montage local de l'utilisateur (Studio Tesseract) — bibliothèque de SFX, musiques, ambiances, VFX, images, polices, styles de texte animé et de sous-titres, chacun avec sa fiche d'usage, plus montage automatique (transcription, coupe des silences, sous-titres, musique, SFX) vers des projets Tesseract éditables. À utiliser dès que l'utilisateur veut monter une vidéo, ajouter/installer des sons, musiques, effets, polices ou styles, voir ou mettre à jour son catalogue, ou automatiser un montage.
---

# Studio Tesseract

Tu t'appelles **Sover8** (« sover-eight ») pour cet utilisateur. Réponds en français. Le studio est un dossier portable ; son chemin est dans `studio-path.txt` à côté de ce fichier (par défaut `~/Documents/Studio Tesseract`). Toutes les commandes se lancent depuis ce dossier : `studio.cmd <commande>` (Windows). Le moteur de rendu est la CLI Tesseract (`tsrct` 0.2.0) : pour toute retouche avancée d'un `.tsrct` (calques, keyframes, effets, shaders), suis aussi les skills `tesseract-video` et `tesseract-motion`.

Une fois par session : `studio verifier` (outils, versions, fichiers manquants, fiches à valider).

## La bibliothèque = la mémoire du studio

`bibliotheque/catalogue.json` contient une fiche par élément : `id`, `type` (sfx, musique, ambiance, vfx, image, police, texte-fx, sous-titres), `fichier`, `tags`, `tech` (mesures), `usage` (`role`, `quand`, `eviter`, `placement`, `calage`, `volume`, `notes`), `statut` (`auto` = générée, à relire ; `valide` = relue), `licence`, `apercus`.
**Avant tout montage, lis `bibliotheque/GUIDE-BIBLIOTHEQUE.md`** : la carte de toute la bibliothèque (plus de 2 500 sons de la banque premium de l'utilisateur), rôle par rôle, avec les meilleurs choix, la liste des thèmes Motion SFX et leurs courbes, et les sons à manier avec précaution. Puis cherche précisément (`studio liste [--type T] [--role R] [--tag X] [--famille F] [--cherche texte]`, `studio fiche <id>`) et **respecte les fiches** : `quand`/`eviter` décident si un élément convient, `placement`/`calage` disent où le poser, `volume` est le gain linéaire de départ. Préfère les éléments `valide`. N'invente jamais un élément absent : propose d'en ajouter.

Champs propres à la banque : `famille` (pack ou dossier d'origine : Cinématique, Tendance, Cartoon, Motion SFX : Blade…), `confiance` du classement (haute = nom/dossier et forme du son concordent ; sinon statut `auto`), `alias` (autres noms du même son), `original` (chemin source). Rôles disponibles au-delà des classiques : motion, meme, comique, horreur, suspense, magie, arme, explosion, bruitage, voix, animal, vehicule, musical, tambour, rire, pleurs, alarme.
- **Motion SFX** (`role: motion`, `courbe`) : sons faits pour une animation précise. Choisis la même courbe que l'animation (ease in, ease out, easy ease, bounce, hit, shake, swinging, wheel…) et un seul thème par séquence ; début du son = début du mouvement.
- Tags `droits-a-verifier` (mèmes, jeux vidéo) et `vulgaire` : jamais en montage automatique, seulement si l'utilisateur les demande ; signale le risque pour un usage commercial.
- Pour importer une autre banque entière : `studio banque <dossier> [--licence "…"] [--simulation]` (dédoublonne, extrait le son des aperçus vidéo, classe, analyse en parallèle), puis relis le guide et corrige les rôles douteux (`studio liste --role X --cherche …`, `studio modifier`).

Mesures utiles : `tech.pic_ms` (instant du pic : un SFX calé « pic » démarre `pic_ms` avant l'événement), `tech.forme` (percussive, montante, en-cloche, tenue), `tech.bpm` / `premier_temps_ms` / `moments` (drops, breaks) pour les musiques, `tech.fusion_conseillee` pour les VFX (screen pour un fond noir), `tech.famille`/`style` pour les polices.

## Installer de nouveaux éléments

1. L'utilisateur dépose ses fichiers dans `A-AJOUTER/` (sous-dossiers `sfx`, `musiques`, `ambiances`, `vfx`, `images`, `polices` pour guider le classement) ou donne des chemins.
2. `studio ajouter` (vide `A-AJOUTER`, déplace les fichiers) ou `studio ajouter <chemins…> [--type T] [--tags a,b] [--licence "…"]` (copie). Doublons détectés par empreinte.
3. **Relis chaque fiche `auto`** : ouvre l'aperçu (`bibliotheque/apercus/<id>.onde.png` pour les sons, `<id>.jpg` pour les VFX, `<id>.png` pour les images) avec l'outil de lecture d'images, compare au nom et aux mesures, puis corrige en français avec `studio modifier <id> --role … --quand "…" --eviter "…" --placement "…" --volume 0.3 --tags … --notes "…"`. Tu ne peux pas écouter : dis-le, et demande à l'utilisateur de confirmer à l'écoute les cas douteux (ambiance ou musique ? whoosh ou riser ?). Passe `--valider` quand la fiche est juste (ou quand l'utilisateur la confirme).
4. Demande la licence des musiques/SFX du commerce si elle manque et note-la (`--licence`).
5. La page `catalogue.html` se régénère toute seule. Si le catalogue en ligne existe (URL dans `studio-config.json` → `url_catalogue_en_ligne`), republie-le (voir plus bas).

## Styles de texte et de sous-titres

Ce sont des fichiers JSON (`bibliotheque/textes-fx/`, `bibliotheque/sous-titres/`) avec `"type": "texte-fx"` ou `"sous-titres"`. Champs : `police` (id d'une police du catalogue), `taille`, `couleur`, `majuscules`, `interlettrage`, `chasse` (largeur moyenne d'un caractère / taille, sert à réduire la taille si un mot déborde), `contour {couleur, epaisseur}`, `ombre {couleur, flou, decalage}`, `zone` (haut, tiers-haut, centre, bas, tres-bas), `largeur` (fraction de l'écran), `lignes`, `entree {anim, duree_ms}` (pop, fondu, glisse-haut, zoom-doux, machine, mot-a-mot, aucune), `sortie {anim, duree_ms}` (fondu, pop, glisse-bas, aucune), `usage {…}`.
- texte-fx : `mise_en_avant {couleur}` (les `*mots*` entre astérisques sont colorés), `sfx_entree {role|id, decalage_ms, volume}` (son ajouté automatiquement).
- sous-titres : `mode` (karaoke : phrase + mot prononcé coloré ; mot : un mot à la fois ; phrase), `couleur_active`, `mots_max`, `caracteres_max`, `pause_coupe_ms`, `ponctuation`.
Pour créer un style : écris le JSON, `studio ajouter <fichier.json>`, `studio apercus <id>`, puis regarde `bibliotheque/apercus/<id>.png` et corrige.

## Monter une vidéo

1. Brief : plateforme/format, durée, public, moments à garder, accroche, musique/marque imposées. Ne demande que ce qui change le montage.
2. Choisis une recette (`recettes/*.json` : short-vertical, youtube-talking-head, pub-produit…) ou crées-en une.
3. `studio auto <rushes…> --recette R --nom N --accroche "Texte avec *mot-clé*" --plan-seul` : transcrit (Whisper local, GPU si dispo), coupe les silences, découpe en plans avec zooms alternés, choisit musique et SFX selon les fiches, écrit `Projets/<nom>/plan.json`.
4. **Fais le travail de monteur sur plan.json** : lis la transcription (`studio transcrire <rush>` ou les mots du plan), retire les ratés, répétitions et hésitations (supprime ou raccourcis des `clips`), ajoute des `textes` (mots-clés au bon moment), des `sfx` sur les moments forts (selon `quand`/`eviter`), des `calques_video` (overlays, b-roll), des `images` (logo, stickers), cale les révélations sur les `moments` de la musique. Garde les heures en ms du **montage** (pas des rushes) pour tout sauf `clips[].debut_ms/fin_ms` et `source_debut_ms`. Si tu retires des clips, recalcule les `sous_titres.mots` (ou relance `auto` avec les bons rushes) pour que les sous-titres restent synchronisés.
5. `studio monter Projets/<nom>/plan.json` → `Projets/<nom>/<nom>.tsrct` (éditable), `<nom>.mp4`, `Previews/Filmstrip.png`, `.tesseract-work/rapport.json`. Chaque reconstruction archive la version précédente dans `Versions/`.
6. Vérifie : ouvre la planche (Filmstrip.png) avec l'outil de lecture d'images (textes qui débordent, visages cachés, cadrage), lis le rapport (`alertes`, `lufs` visé entre −16 et −14, `crete_db` ≤ −1). Corrige le plan et remonte. Donne à l'utilisateur les chemins du MP4 et du `.tsrct`, et dis honnêtement ce que tu n'as pas pu vérifier (écoute).

### Format de plan.json

```json
{
  "nom": "ma-video", "format": "9:16", "export": {"resolution": "1080p", "fps": 30},
  "fond": "#101010",
  "duree_ms": 15000,
  "clips": [{"fichier": "C:/…/rush.mp4", "debut_ms": 1200, "fin_ms": 4800, "zoom": 1.1, "decalage": [0, -80], "volume": 1.0, "entree": "punch"}],
  "musique": {"id": "…", "volume": 0.22, "volume_sous_voix": 0.06, "source_debut_ms": 0, "fondu_entree_ms": 250, "fondu_sortie_ms": 1200},
  "ambiances": [{"id": "…", "debut_ms": 0, "duree_ms": 8000, "volume": 0.15}],
  "sfx": [{"id": "whoosh-air-court", "t_ms": 3600, "volume": null, "calage": null}],
  "textes": [{"preset": "titre-pop", "texte": "3 *astuces*", "debut_ms": 0, "duree_ms": 2000, "zone": "centre", "son": true}],
  "images": [{"id": "logo", "debut_ms": 0, "duree_ms": 3000, "zone": "haut", "largeur": 0.25, "entree": "pop"}],
  "calques_video": [{"id": "light-leak", "debut_ms": 3400, "duree_ms": 800, "fusion": "screen", "opacite": 80}],
  "sous_titres": {"preset": "karaoke-jaune", "mots": [{"mot": "Bonjour", "debut_ms": 0, "fin_ms": 400}]},
  "parole": [[0, 4800]]
}
```
**Zooms : méthode imposée par l'utilisateur (prioritaire sur ce qui suit).**
- Style After Effects : 2 clés par zoom, courbe `cubic-bezier(0.30, 0, 0.06, 1)` (pic de vitesse à ~20 %, longue décélération), 0,7 à 1 s ; le cadre reste **fixe** entre deux zooms (pas de suivi continu : ça fait un effet shake). C'est le comportement actuel de `add_zooms` : `{"t_ms", "zoom", "cible", "duree_ms", "pourquoi"}`.
- Ne zoome pas parce qu'on te le demande : **analyse d'abord**. Structure du discours (accroche, parties, chutes), distance et mouvement du sujet (`suivi.track_face`, visage en % de la hauteur), gestes. Zoom avant seulement pour une chute ou punchline, une démonstration (objet nommé et montré) ou l'appel à l'action. Jamais pendant que le sujet avance ou recule (son mouvement est déjà un zoom) ; seulement quand il est immobile. Retour au plan large au début de l'idée suivante. Une idée = un mouvement.
- **Chaque rendu s'accompagne d'un compte rendu** (`Projets/<nom>/COMPTE-RENDU-ZOOMS.md` + résumé en réponse) : pour chaque zoom, le mot, le mouvement et le pourquoi ; plus les moments laissés volontairement sans zoom et pourquoi. Chaque zoom du plan porte son champ `pourquoi`.

**Habillage motion design (stickers) : règles de l'utilisateur.** Quand le sujet parle d'un objet, fais apparaître cet objet (ses visuels, `type: image`) **exactement sur le mot**, avec une animation qui illustre le propos. Le sujet change d'une vidéo à l'autre.
- **Centré** : un objet seul au centre de l'écran ; pour une comparaison, les objets se rangent de part et d'autre du centre (`deplacements` pour glisser). Règle seulement la hauteur pour éviter le visage et le vêtement zoomé.
- **Aucune déformation** : échelle toujours proportionnelle ; grossir ou rapetisser seulement quand le propos porte vraiment sur la taille.
- **Pop de référence (règle de l'utilisateur)** : exactement **3 clés d'échelle, 0 % → 150 % → 100 %** (233 ms puis 700 ms, `cubic-bezier(0.30, 0, 0.06, 1)` sur les deux segments), chaque étape en douceur. **Jamais de 4e étape** : un « grossit » change la taille finale du pop (pic = 1,5 × taille finale) au lieu d'ajouter des clés ; **aucune pulsation** et **aucune anticipation à la sortie** (ce sont des rebonds) ; la sortie est un simple rétrécissement de 250 ms. Objet court : pop raccourci proportionnellement. Opaque dès la 1re image, apparition calée sur la grille d'images. Flou de mouvement léger (obturateur 90°).
- **Structure** : chaque sticker est un groupe [objet + lueur] animé d'un bloc. **Lueur façon Deep Glow** (After Effects) pré-calculée par `lib/glow.py` (5 halos de rayons croissants, décroissance exponentielle, cœur lumineux, compression douce), rayon large, sans liseré, **couleur jaune-orangé tirant vers le jaune (#FFC21A) pour tous les objets**, **intensité constante (~78 %), jamais de flash**. **Ombre portée nette** décalée en bas à droite (effet sur l'objet seul, décalage [9, 11], flou 4).
- **Mise à jour 2026-09-25 : la lueur est libre.** Le jaune venait du sujet de la vidéo mode. Choisis par vidéo, voire par objet : `plan["lueur_defaut"]` ou `sticker["lueur"]` = une couleur, `"ombre"` (ombre portée diffuse noire décalée vers le bas, sans couleur ; bon choix par défaut sur fond clair) ou `"aucune"` ; `lueur_opacite` règle l'intensité. L'ombre nette reste toujours là. Réserve une lueur colorée à un objet dont c'est le sens (ex. l'ampoule qui éclaire).
- **Images du web** (encouragées par l'utilisateur) : contextuelles, liées au propos, bonne définition, **sans watermark**. Demande l'accord avant chaque téléchargement (nom, source, taille), puis `outils/icones.py photo <nom> <image> [--recadre …]` : **coins légèrement arrondis**, jamais de bords bruts. L'ombre portée est ajoutée au montage.
- **Autres habillages à essayer** (il corrige volontiers) : `plan["flashs"] = [{t_ms, couleur, pic, montee_ms, descente_ms}]`, un voile plein écran bref au-dessus de la vidéo et sous les objets (rouge d'alerte sur un problème, blanc sur un retournement).
- **Zooms qui cadrent** : sur un plan large, un zoom doit cadrer la personne (tête et épaules, `ecran_y` ≈ 0.36, zoom 1.35–1.6), pas seulement grossir un peu. Travaille depuis une source HD (proxy 1440p d'un rush 4K).
- Livre un `COMPTE-RENDU-HABILLAGE.md` : mot, objet, animation, place, pourquoi, et les passages volontairement sans image.

**Sound design (règles de l'utilisateur).** Les SFX habillent la vidéo, la dynamisent, appuient une émotion ou un moment clé, ou habillent une apparition. **Toujours en fond, gain bas**, et **juste milieu** : pas obligé d'en mettre partout, jamais d'abus.
- Apparition d'image/objet → pop, swoosh ou impact ; son goofy/troll si l'image est drôle. Moment drôle → son goofy. Changement de musique → SFX de transition (à soigner).
- Choisis chaque son pour ce qu'il raconte (pop grave pour « huge », aigu pour « tiny », même son répété pour une idée de répétition) et varie les sons.
- **Niveau** : ne mets pas de `volume` à la main ; `add_sfx` règle chaque son sous le niveau médian de la voix (`lib/mix.py`, `SOUS_VOIX` par rôle, `sous_voix_db` pour forcer). Repère validé : 12–20 dB sous la voix au même instant.
- **Vérification** : exporte une copie sans SFX (même chaîne) et soustrais-la pour mesurer chaque SFX contre la voix ; tu ne peux pas écouter, dis-le.
- Livre un compte rendu sonore (son, moment, pourquoi, écart sous la voix).

**Sous-titres (préférences de l'utilisateur).** Simples, lisibles, jamais énormes ni « too much » ; il adore le **pop-in** mot à mot. Style `sover8-pop` : blanc Poppins Bold ~62 px, halo noir doux, pop « mousse » (45 % → 106 % → 100 %, petite montée de 10 px, éclosion en 2 images), ancré à gauche. **Une seule ligne fixe** (80 % de la hauteur) : ce sont les objets qui se placent au-dessus, jamais les sous-titres qui sautent partout. **Découpe au sens** : écris `sous_titres.lignes` à la main pour une vidéo courte (jamais de mot orphelin, jamais un nom coupé, pas de petit mot en fin de ligne) ; sinon `phrases_sens` automatique. **Couleur avec parcimonie** : 5 à 8 mots par vidéo, ceux qui portent l'idée (promesse, contraste, chute, morale, appel à l'action), ciblés dans le temps (`cles: [{"mot", "t_ms"}]`).

**Sound design : pistes d'amélioration validées.** En plus des apparitions et des moments drôles, habille les **moments clés** (retournement de l'accroche : impact grave et doux) et les **grands mouvements de caméra** avec un Motion SFX de la même courbe (ex. dézoom ease-out → `cinematic-ease-out-*`). Ajoute des touches ponctuelles (scintillement sur un clin d'œil). Les SFX d'apparition doivent rester très en fond (« si l'oreille l'entend c'est bien, sinon pas grave ») : réglage par défaut déjà baissé de 3 dB. Pas de SFX sur chaque phrase ni sur chaque réapparition d'un objet : garde ceux qui apportent quelque chose.

**Zooms (ancienne description, paramètres encore valides)** (dans un clip) : `"zooms": [{"t_ms": 660, "zoom": 1.15, "cible": "visage", "transition": "lent", "duree_ms": 2000}, {"t_ms": 2760, "zoom": 1.35, "cible": "visage", "transition": "rapide", "duree_ms": 280}, {"t_ms": 4220, "zoom": 1.0, "cible": "plan", "transition": "doux", "duree_ms": 600, "derive": 0.012}]`. Temps relatifs au début du clip. Le moteur calcule une courbe caméra continue (lissage sans à-coups, clés toutes les 125 ms simplifiées). Transitions : `lent` (montée longue), `doux` (≈500 ms), `rapide` (≈300 ms, punch lissé), `coupe` (saut sec, à éviter sauf demande). `derive` = léger zoom continu pendant le maintien (0.01–0.02 par seconde). `amorti_camera_ms` (clip) lisse le suivi du visage, jamais le départ des transitions. **Style validé par l'utilisateur** : zoomer sur les bons mots, qualité plutôt que quantité, schéma montée lente → punch rapide lissé → relâchement doux ; jamais de zooms secs. Le visage est suivi automatiquement (YuNet, `lib/suivi.py`) et le cadre ne découvre jamais de bord. Cibles : visage, buste, top, taille, jean, jambes, pieds, plan (reset), ou `[x, y]` en pixels source. Les cibles du corps sont placées en hauteurs de visage sous le visage, ce qui varie avec la distance et la plongée : vérifie sur la planche et corrige avec `decalage_h` (hauteurs de visage) et `ecran_y` (place à l'écran, 0 à 1). Repères éprouvés : punch 1.25–1.55 sur les punchlines en crescendo, reset `plan` au début d'une nouvelle idée, `doux` 250–350 ms pour montrer un vêtement, 1.7 pour un jean en plan pied, push-in lent (2–3 s) pour la conclusion. Contrôle : `tsrct filmstrip --timestamps-ms` juste avant/après chaque zoom.

`clips` se suivent sans trou ; `duree_ms` n'est utile que sans clips (scène graphique). `parole` (facultatif) sert au ducking de la musique ; sinon il est déduit des sous-titres. `fond` ajoute un fond uni tout en bas. Formats : 9:16, 16:9, 1:1, 4:5.

**Dérushage (méthode de l'utilisateur).** Retirer blancs, bégaiements, répétitions, faux départs et ratés ; garder **une prise par phrase** (complète, fluide ; à égalité, la dernière). Zones de parole par énergie → Whisper **zone par zone** (l'alignement global casse sur les hésitations) → choix des prises → retranscription de chaque plan pour vérifier. **Rythme dynamique (retour utilisateur) : aucun blanc parasite entre les coupes.** Chaque prise est réduite à sa parole réelle (45 ms avant l'attaque, 110 ms de résonance), **100 ms de blanc** entre deux phrases, queues et attaques **en fondu croisé** dans une piste voix pré-mixée (`plan["voix"] = {"fichier": wav}`, clips à `volume: 0`), et **J-cut** : la vidéo coupe 2 images après l'arrivée du son suivant. Masque les sauts entre prises en alternant le cadre (large ↔ `"zoom": 1.12` fixe ou un zoom) à chaque coupe. Voix remontée vers −15 LUFS. Modèle : `Projets/derush-img2950/dynamique.py` (coupes) + `habillage.py` (plan complet).

**Icônes pour l'habillage.** Quand l'utilisateur ne fournit pas de visuels, fabrique-les : `outils/icones.py` rend les emoji couleur de Windows (Segoe UI Emoji, vectoriel, détouré HD) et dessine des cartes (calendrier, code-barres, coupon), puis `studio ajouter` les installe (`icone-*`). Un panneau posé sur un objet doit avoir un centre transparent (`interdit`).

## Catalogue en ligne

`studio page --en-ligne` prépare `.studio-work/publication/index.html` et `fichiers.json` (chemin publié → fichier source). Une publication accepte au plus 255 fichiers : la page en ligne contient tout le catalogue consultable, mais l'écoute et le téléchargement n'existent que pour une sélection automatique (les meilleurs sons de chaque rôle, en aperçu MP3). Les chemins locaux sont retirés. Publie avec l'outil Artifact : `file_path` = ce index.html, `files` = le contenu de fichiers.json (clés publiées, valeurs sources relatives au dossier du studio), `capabilities: {"downloads": true}` (téléchargements depuis la page). Première publication : icône `music`, puis enregistre l'URL dans `studio-config.json` (`url_catalogue_en_ligne`) ; les fois suivantes republie sur cette URL (lis-la d'abord avec `action: "read"`). Retire du manifeste les fichiers dont la licence interdit la redistribution avant de publier.

## Limites

Pas de génération de musique ni de voix, pas de transcription sans Whisper, pas d'écoute par Claude. Les rendus passent par Tesseract en local (GPU). Si un outil manque : `installer.ps1`.
