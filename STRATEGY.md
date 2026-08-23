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

## Score maximum theorique (sans opposition)

En simulant un environnement "solo" (l'adversaire prend toujours un coup
different du notre, donc aucune contention: on dispose exactement de nos 24
actions normales sur 8 manches, sans jamais etre bloque), la recherche du
meilleur score atteignable donne des enseignements complementaires:

- Un **MCTS solo a 600 iterations/coup** atteint **58,5 PV** avec une
  configuration a priori contre-intuitive: seulement 2 especes developpees
  (11 cochons, 14 chevaux — mouton et vache laisses a 0-1, donc en malus),
  mais **3 batiments speciaux achetes et surtout des ressources
  deliberement non depensees** (37 en fin de partie) pour maximiser le bonus
  de l'Entrepot (+0,5 PV/ressource restante = +18,5 PV a lui seul, la plus
  grosse ligne du score). Un plan construit a la main avec une logique
  "developper les 4 especes a fond" ne depassait que 49 PV — la difference
  vient entierement de cet arbitrage entre elevage et thesaurisation.
- Ce chiffre (58,5) n'est probablement pas le maximum absolu (mouton et
  vache restent en malus -3 chacun; les corriger a moindre cout semble
  possible avec les ressources non depensees) mais c'est un score
  rigoureusement verifie par le moteur, pas une estimation theorique.
- **2 mecaniques sont determinantes** pour cette optimisation, toutes deux
  deja bien implementees dans le moteur (verifie dans `farmyard.py:breed`
  et `rules_data.ACCUM_SPACES`):
  1. La reproduction gratuite en fin de manche (`breed()`) exige de la place
     libre — un groupe reproducteur (>=2 animaux) deja a pleine capacite
     perd sa tete gratuite.
  2. Chaque espece a son propre "taux de respawn" sur le plateau (+1/manche
     si personne ne la prend) qui s'accumule gratuitement — attendre pour
     recolter un gros tas ne coute rien, mais demarrer la reproduction TOT
     (des que 2 animaux sont reunis) rapporte 1 tete gratuite par manche
     restante, un effet compose qu'un glouton 1-coup ne voit pas.

### Heuristiques ajoutees au `HeuristicBot`

Pour partiellement compenser l'horizon 1-coup du bot glouton
(`agricola2p/bots/heuristic_bot.py`), 2 heuristiques exploitent directement
ces 2 mecaniques:

1. **Anti-gaspillage de reproduction**: penalise tout groupe reproducteur
   (>=2 animaux) deja a pleine capacite dans l'etat resultant d'un coup —
   incite le bot a batir des auges *avant* que ca deborde, pas apres.
2. **Demarrage precoce de la reproduction**: bonifie un coup qui fait
   franchir le seuil de 2 animaux pour la 1ere fois sur un emplacement,
   proportionnellement au nombre de manches restantes (chacune rapportera
   potentiellement 1 tete gratuite).

Verifie empiriquement (20 seeds, mode solo et 2 joueurs): amelioration
**nette mais pas dominante** — +2,1 PV de moyenne en solo, et gagne 11
parties sur 20 face a la version sans heuristiques en tete-a-tete 2 joueurs
(8 defaites, 1 nulle). Un glouton 1-coup, meme aide par ces 2 heuristiques,
reste loin du niveau atteint par une vraie recherche en arbre (MCTS): il
gagne rarement plus de ~30 PV en solo contre 58,5 pour MCTS, ce qui confirme
que planifier une sequence de 24 actions interdependantes depasse ce qu'un
glouton peut voir, quelles que soient les heuristiques ajoutees.

## Bot par apprentissage par renforcement (RLBot)

`agricola2p/rl/` entraine un reseau de valeur (petit MLP numpy, cf
`value_net.py`) par self-play: des parties sont jouees par des bots
existants (`HeuristicBot`/`RandomBot`, melanges avec de l'exploration
aleatoire pour diversifier les etats visites), et le reseau apprend a
predire, a partir d'un etat encode (`features.py`, ~60 dimensions:
ressources, animaux, capacites d'enclos/batiments, tuiles, batiments
speciaux, accumulateurs partages du plateau, score actuel), le retour final
Monte-Carlo (`score(moi) - score(adversaire)` en fin de partie) — une
evaluation de politique par apprentissage supervise sur les resultats
observes.

Poids fournis dans le depot (`agricola2p/rl/weights.npz`, entraine sur 3000
parties de self-play, 80 epoques — reentrainable via
`python3 -m agricola2p.rl.train`). Deux facons de l'utiliser:

- **`RLBot`**: glouton 1 coup comme `HeuristicBot`, mais qui evalue chaque
  etat resultant avec le reseau appris au lieu du bareme de score exact.
- **`MCTSBot(value_fn=...)`**: remplace les simulations jusqu'en fin de
  partie par une evaluation directe du reseau a chaque feuille non-terminale
  ("bootstrap", a la AlphaZero) — ~10x plus rapide par iteration, donc bien
  plus d'iterations pour le meme temps de calcul.

**Resultats mesures** (parties completes via le moteur reel, pas une
estimation):

| Confrontation | Resultat |
|---|---|
| RLBot vs RandomBot (20 seeds) | **20-0** |
| RLBot vs HeuristicBot (20 seeds) | **20-0** |
| RLBot vs MCTSBot-rollout (150 iterations, 10 seeds) | 4-6 (competitif malgre un seul coup d'avance) |
| MCTS+bootstrap (300 iter, reseau appris) vs MCTS+rollout classique (300 iter, 10 seeds) | **7-3** |

Le reseau de valeur, bien qu'entraine sur un signal bruite (la loss de
validation oscille pendant l'entrainement — la variance d'issue d'une
partie a partir d'un etat donne reste elevee vu la taille de l'espace de
recherche), capture visiblement mieux le potentiel latent d'un etat que le
score exact seul (capacite d'enclos pas encore exploitee, ressources/
animaux accumules sur le plateau...): c'est precisement ce qu'un glouton
base sur `score_player` ne peut pas voir a 1 coup. Meme constat que pour les
heuristiques de reproduction (section precedente), en plus marque: la valeur
d'un etat depend de ce qu'il permettra de faire dans les manches suivantes,
pas seulement de ce qu'il vaut a l'instant T.

### Tentative de generation 2 (reseau plus profond, self-play RLBot vs RLBot) — echec instructif

`agricola2p/rl/` supporte maintenant des reseaux a plusieurs couches cachees
(`ValueNet(hidden_dim=(64, 32), ...)`) et un mode d'auto-jeu ou RLBot
s'affronte lui-meme pour generer les donnees d'entrainement
(`train.py --self-play rl`, cf `self_play.make_rl_self_play_pair`: 75% des
parties opposent 2 copies du RLBot courant partageant le meme reseau, 25%
l'opposent a un Heuristic/Random comme partenaire d'entrainement fixe, plus
15% de coups aleatoires pour diversifier).

**Resultat mesure**: un reseau entraine sur 3000 parties de self-play RLBot
vs RLBot (profond, 2 couches 64+32) **perd 0-20** contre le modele
precedent (1 couche, entraine sur des parties Heuristic/Random). Pour
isoler la cause, un 2e run a profondeur EGALE (1 couche, memes
hyperparametres, seule la source des parties change) a ete teste: memes
resultats desastreux (**0-15**, et seulement 10-0 contre RandomBot au lieu
de 20-0 pour la generation precedente). La profondeur du reseau n'y est
donc pour rien: **c'est la donnee de self-play elle-meme qui est en cause**,
pas l'architecture.

Diagnostic le plus probable: un RLBot est un glouton **deterministe** (il
ne randomise qu'en cas d'egalite stricte) — faire jouer 2 copies du meme
reseau l'une contre l'autre produit des parties bien plus repetitives et
etroites que le melange Heuristic/Random original (qui inclut un vrai style
aleatoire et un vrai style base sur une formule figee, deux sources de
diversite tres differentes). Le reseau apprend alors a bien predire l'issue
de SA PROPRE politique imparfaite plutot que d'ancrer ses estimations sur
des parties variees — un biais d'auto-reference classique en self-play
naif, faute des mecanismes d'exploration qu'utilise un vrai AlphaZero
(recherche en arbre MCTS a la selection, bruit de Dirichlet a la racine,
echantillonnage par temperature sur les visites — bien plus riches qu'un
epsilon fixe sur un glouton deterministe).

**Consequence pratique**: `agricola2p/rl/weights.npz` livre dans le depot
reste le modele de la 1ere generation (1 couche, self-play Heuristic/Random)
— nettement plus fort en pratique malgre son architecture plus simple. Le
code du self-play RLBot vs RLBot et des reseaux profonds reste disponible
(`--self-play rl`, `--hidden 64 32`) pour qui veut experimenter, mais n'est
pas ce qui est utilise par defaut. Pistes pour qu'une generation 2 batte
reellement la generation 1: generer les parties de self-play avec `mcts_rl`
(recherche en arbre, donc bien plus d'exploration qu'un glouton pur) plutot
qu'avec RLBot brut, ou constituer un "pool" d'adversaires (plusieurs
generations passees, pas seulement le modele courant) pour eviter le
sur-ajustement a sa propre politique.

## Pour aller plus loin

Ces observations viennent d'un seul appariement MCTS(250) vs MCTS(250) — un
echantillon de taille 1. Pour affiner ce guide: fais tourner plusieurs seeds
(`python3 -m agricola2p.cli --p1 mcts --p2 mcts --iterations 300 --seed N`),
augmente le nombre d'iterations pour un jeu plus fort, et verifie en
particulier si un bot qui priorise les tuiles d'extension bat regulierement
celui de cette partie.
