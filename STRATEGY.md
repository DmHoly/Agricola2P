# Guide strategique

Enseignements tires de parties MCTS vs MCTS jouees avec ce moteur (voir
[RULES.md](RULES.md) pour le detail des regles). A prendre comme des
tendances observees a 250 iterations/coup, pas comme une solution optimale
prouvee — un MCTS a si peu d'iterations sur un espace de recherche de cette
taille reste imparfait, et certains choix ci-dessous ressemblent a des
angles morts exploitables plutot qu'a de la vraie theorie du jeu.

## Partie de reference (seed 77, 250 iterations/coup)

Score final: **P1 37 — P2 39**. Detail:

| | P1 | P2 |
|---|---|---|
| Animaux (+1/tete) | 26 (14 cochons, 12 chevaux) | 22 (15 vaches, 6 chevaux, 1 mouton) |
| Bareme par espece | +6 | +3 |
| Batiments sur case | 0 | Etable +2 |
| Batiments speciaux | Carriere privee (3) + Porcherie (2) | Entrepot (0 + 0.5/ressource) + Puits (2) + Bergerie (2) |
| Bonus ressources restantes | — | +8 (16 ressources x 0.5, Entrepot) |
| Tuiles d'extension | 0 | 0 |
| **Total** | **37** | **39** |

## Ce qui a fait gagner P2

1. **L'Entrepot a rapporte plus que tout le reste combine.** 0,5 PV par
   ressource en reserve en fin de partie, applique a 16 ressources
   inutilisees = **+8 PV**, soit plus que n'importe quel autre batiment de
   la partie. Si tu obtiens cette carte, **arrete de tout depenser en fin
   de partie**: chaque ressource stockee vaut autant qu'un animal
   supplementaire au palier median.
2. **3 batiments speciaux contre 2.** Il n'y a que 2 cases "batiment
   special" par manche, partagees entre les 2 joueurs: les prendre tot prive
   l'adversaire d'options ET rapporte des PV directs quasi gratuits (pas de
   case de ferme consommee).
3. **Une Etable plutot qu'une Stalle simple.** +1 PV et +1 capacite pour un
   cout modeste (5 bois ou 5 pierre) une fois la Stalle batie.

## Ce qui a coute des points aux deux joueurs

- **Chaque joueur a laisse 2 especes a 0 animal** (P1: moutons et vaches;
  P2: cochons) → **-3 PV chacune**, soit **-6 PV** perdus "gratuitement".
  Avec seulement 8 manches et des ouvriers limites, se specialiser semble
  payant sur le papier (voir plus bas), mais **descendre a 1 animal sur une
  3e espece pour eviter un -3** est presque toujours rentable si tu as un
  ouvrier qui ne sert a rien d'autre ce tour-la.
- **Aucun des deux n'a achete de tuile d'extension**, alors que le bonus
  "tuile entierement amenagee" vaut **+4 PV** pour un cout de 3 pierres + 1
  roseau (case dediee) — potentiellement rentable si tu as 3 emplacements a
  y mettre (batiment/auge/enclos) avant la fin de partie. C'est le point le
  plus suspect de cette partie: a iterations limitees, le MCTS n'a
  visiblement pas explore cette branche assez profondement. **Une tuile
  d'extension bien remplie est probablement sous-jouee par ce bot — teste-la
  toi-meme.**
- **Personne n'a renove la maison** (Maison a colombage, +2 PV pour 5 bois
  ou 5 pierre) alors que les deux joueurs terminent avec des ressources
  inutilisees. Un coup quasi gratuit en fin de partie si tu as le choix
  entre "gaspiller" et "+2 PV garantis".

## Principes generaux qui se degagent

1. **Concentre-toi sur 1-2 especes a fort volume plutot que de diluer sur
   4.** Le bareme par paliers recompense fortement les hauts totaux (8-9 PV
   au sommet) alors que le premier palier positif (0 PV, "juste au-dessus du
   malus") ne rapporte rien. Un enclos de 2 cases + 2 auges loge 16 animaux
   (`N x 2 x 2^auges`) — assez pour toucher les paliers hauts d'une seule
   espece. Mais ne laisse jamais une espece a 0-3: un seul animal de plus
   suffit a transformer -3 en 0 (voir plus haut).
2. **Priorise les auges tres tot.** Elles doublent la capacite d'un enclos
   par unite achetee (jusqu'a x16 pour 2 cases + 3 auges) — c'est le
   multiplicateur le plus puissant du jeu, bien plus rentable au PV/ressource
   que d'agrandir un enclos case par case. Une case standard offre 1 auge
   gratuite: ne la laisse jamais partir sans la prendre.
3. **Regarde les 2 cases "batiment special" en priorite des que tu peux te
   les offrir**: elles rapportent des PV directs sans consommer de case de
   ferme, et c'est une ressource rare partagee (2 par manche, 2 joueurs).
   L'Entrepot en particulier change de valeur selon ta gestion de fin de
   partie: ne le prends que si tu comptes finir avec des ressources non
   depensees.
4. **Guette la case "Petit Bois"** (jeton 1er joueur, cf RULES.md): comme le
   1er joueur reste fixe sauf si quelqu'un la prend, un joueur en retard
   peut s'en servir pour reprendre l'initiative durablement, pas seulement
   pour le bois gagne.
5. **Les clotures et batiments sont irreversibles**: reflechis a la
   mutualisation des barrieres avant de placer un enclos (deux enclos
   adjacents partagent le cout de la barriere commune) et laisse les bords
   de ta maison/tes batiments faire office de murs gratuits plutot que de
   payer une barriere en double.
6. **N'oublie pas le redeplacement gratuit des animaux** (`reorganize`,
   1x par tour d'ouvrier): consolider des animaux epars dans un seul enclos
   avant la reproduction peut debloquer un palier de score sans depenser de
   ressources.

## Pour aller plus loin

Ces observations viennent d'un seul appariement MCTS(250) vs MCTS(250) — un
echantillon de taille 1. Pour affiner ce guide: fais tourner plusieurs seeds
(`python3 -m agricola2p.cli --p1 mcts --p2 mcts --iterations 300 --seed N`),
augmente le nombre d'iterations pour un jeu plus fort, et verifie en
particulier si un bot qui priorise les tuiles d'extension bat regulierement
celui de cette partie.
