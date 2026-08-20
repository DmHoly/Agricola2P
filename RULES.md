# Regles implementees

Reference detaillee du ruleset code dans ce moteur pour **Agricola: Terre
d'Elevage** (*All Creatures Big and Small*), et de ses ecarts avec le jeu
physique. Voir le [README](README.md) pour l'installation et l'usage.

**Toutes les valeurs numeriques sont centralisees dans
`agricola2p/engine/rules_data.py`** — aucun autre module n'en contient "en
dur". Si tu as une source plus precise que le jeu physique, il suffit
d'ajuster ce fichier.

## Structure de la partie

- 8 manches, chaque joueur avec 3 ouvriers (6 placements/manche, en
  alternance stricte J1/J2). 1 seul ouvrier par case: une case occupee est
  indisponible a l'autre joueur pour le reste de la manche.
- **Jeton 1er joueur "collant"**: reste au meme joueur d'une manche a
  l'autre par defaut. Prendre la case "Petit Bois" (`FIRST_PLAYER_SPACE`)
  l'octroie pour la manche suivante a celui qui l'a prise.
- **Reproduction**: a la fin de chaque manche, tout groupe d'au moins 2
  animaux de la meme espece avec de la place produit 1 bebe.
- **Redeplacement des animaux**: barrieres/auges/batiments sont fixes une
  fois poses, mais les animaux peuvent etre redispatches librement entre 2
  emplacements deja construits de sa ferme (1 seule espece/emplacement).
  Action gratuite (`kind="reorganize"`), ne consomme pas le tour — limitee a
  1 par tour d'ouvrier pour borner l'espace de recherche des bots.
- **Egalite**: le joueur qui n'a pas commence la toute premiere manche
  l'emporte.

## Plateau d'action (17 cases, toutes disponibles des la manche 1)

- Ressources: Petit/Grand Bois, Petite/Grande Pierre, Roseau & Bois —
  accumulent si non prises.
- 1 case d'accumulation par espece (mouton/cochon/vache/cheval).
- **Clotures**: case standard (1 bois/segment) et alternative (2 pierres les
  2 premiers segments puis 1/segment). Deux enclos voisins **mutualisent**
  la barriere partagee (payee une fois). Maison et batiments font office de
  **murs naturels gratuits**.
- **Auges**: case standard (1re gratuite puis 3 bois/auge) et alternative (3
  pierres/auge). Une auge se pose sur n'importe quelle case de terrain
  (libre ou dans un enclos), max 1/case. Une visite peut en poser plusieurs.
- **Agrandissement de ferme** (3 pierres + 1 roseau): 1 tuile d'extension de
  3 cases (max 2 au total).
- **Agrandissement ou amelioration** (5 bois OU 5 pierres): au choix, tuile
  d'extension, OU Stalle -> Etable/Etable ouverte, OU maison -> Maison a
  colombage.
- **Batiment special**: 2 cases independantes (jusqu'a 2 achats/manche).
- **Construction d'une Stalle**: case non listee dans la description
  source, conservee car il faut un moyen d'en batir une avant de la
  remplacer.

## Ferme et capacites

- Depart: grille 3x2 (2 maison + 4 ouvertes), jusqu'a 2 tuiles d'extension
  de 3 cases.
- Enclos de N cases: `N x 2` animaux de base, double par auge presente sur
  l'une de ses cases (pas de plafond arbitraire au-dela du nombre de cases).
- Case non cloturee: 0 animal sans auge, 1 avec.
- Stalle (3 bois + 1 pierre, 1 PV): 4 animaux. Etable (2 PV): 5. Etable
  ouverte (2 PV): 4. Auge sur batiment: +1.
- Maison a colombage: +2 PV, aucune capacite animale.

## Score final

`+1 PV`/animal, + bareme par paliers propre a chaque espece (malus fixe de
-3 PV si moins de 4 animaux), + PV des batiments (Stalle/Etable, maison,
batiments speciaux), + 4 PV par tuile d'extension entierement amenagee.

## Ce qui reste une approximation

La synthese fournie par l'utilisateur ne precisait pas ces details; des
valeurs raisonnables ont ete choisies et sont centralisees dans
`rules_data.py`:

- L'incrementation de "Roseau & Bois" (+1 roseau ET +1 bois/tour).
- Les enclos sont des rectangles (pas de formes libres).
- Forme/emplacement fixes des 2 tuiles d'extension (3 cases chacune).
- Pool de batiments speciaux (au-dela de l'Entrepot, donne en exemple):
  noms/couts/PV generiques plutot que la liste exacte du jeu.
- Cout de construction d'une premiere Stalle (3 bois + 1 pierre).
- Le bot MCTS clone l'etat de jeu (accumulation a venir incluse), ce qui en
  fait un jeu a information parfaite depuis un etat donne — simplification
  qui evite un MCTS a information imparfaite (ISMCTS).

## Prochaines etapes possibles

- Remplacer le pool generique de batiments speciaux et les tuiles
  d'extension par les vraies listes du jeu (texte + effet exact + formes).
- Autoriser des formes d'enclos non rectangulaires (clotures libres).
- Ajouter un bot par apprentissage par renforcement (self-play, type
  AlphaZero simplifie) une fois le moteur valide/ajuste par rapport au jeu
  physique — le `MCTSBot` actuel peut deja servir de generateur de parties
  d'entrainement.
- Interface graphique / web pour jouer contre un bot.
