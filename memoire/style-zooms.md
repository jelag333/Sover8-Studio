---
name: style-zooms
description: "Préférences de l'utilisateur pour les zooms de montage (courbe AE, cadres fixes, justification obligatoire)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f5af91df-535b-47fd-b8a4-a691df54e721
  modified: 2026-09-25T20:57:33.835Z
---

Zooms façon After Effects : 2 clés par zoom, ease-out cubic-bezier(0.30, 0, 0.06, 1) (pic de vitesse ~20 %, longue décélération), ~0,8 s ; cadre FIXE entre les zooms — pas de suivi continu (perçu comme un « shake »). Placement sur les bons mots (validé), qualité plutôt que quantité, les punchs donnent du rythme. Chaque zoom doit être justifié par l'analyse de la vidéo (structure, chutes, démonstrations, mouvement du sujet) et chaque rendu s'accompagne d'un compte rendu « pourquoi ce zoom ici ».

2026-09-25 (IMG_2950) : zooms jugés « parfaits, dynamiques » ; il demande de **cadrer la personne** quand on zoome (plan serré buste/visage, peu d'air au-dessus de la tête), pas un simple petit grossissement. Travailler depuis une source HD (proxy 1440p du 4K) pour rester net.

**Why:** retours successifs sur « fashion-tips-proportions » (2026-09-23) : trop sec → trop de zooms → effet shake du suivi ; il a envoyé son graphe de vitesse After Effects comme référence et demandé des comptes rendus.
**How to apply:** `add_zooms` du [[studio-tesseract-projet]] (mode cadres fixes) ; ne pas zoomer pendant que le sujet avance/recule ; écrire COMPTE-RENDU-ZOOMS.md avec chaque rendu.
