# Agricola2P

Moteur de regles + bots pour **Agricola: Terre d'Elevage** (*All Creatures Big
and Small*, Uwe Rosenberg), le jeu de placement d'ouvriers a 2 joueurs centre
sur l'elevage.

## Contenu

- `agricola2p/engine/` — le moteur de jeu, entierement data-driven (voir
  `rules_data.py`).
- `agricola2p/bots/` — trois bots: `RandomBot`, `HeuristicBot` (glouton 1 coup
  a l'avance) et `MCTSBot` (Monte Carlo Tree Search, UCB1).
- `agricola2p/cli.py` — fait jouer deux bots l'un contre l'autre en terminal.
- `tests/` — tests pytest (regles de la ferme, boucle de partie complete,
  bots).

## Installation rapide

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

## Jouer une partie bot vs bot

```bash
python3 -m agricola2p.cli --p1 heuristic --p2 mcts --iterations 200 --seed 1
```

Bots disponibles: `random`, `heuristic`, `mcts`.

## Utilisation programmatique

```python
from agricola2p.engine.game import AgricolaGame
from agricola2p.bots.mcts_bot import MCTSBot
from agricola2p.bots.heuristic_bot import HeuristicBot

game = AgricolaGame.new_game(seed=42)
bots = [HeuristicBot(seed=1), MCTSBot(iterations=300, seed=1)]

while not game.is_terminal():
    idx = game.current_player_idx
    action = bots[idx].choose_action(game, idx)
    game.apply(action)

print(game.scores())
```

## Fidelite aux regles officielles

Le ruleset implemente suit la synthese fournie par l'utilisateur (basee sur
une presentation d'Agricola: Terre d'Elevage), precisee ensuite en detail sur
le mecanisme central des clotures/enclos/batiments:

- **Partie en 8 tours**, chaque joueur disposant de **3 ouvriers** (6
  placements d'ouvrier au total par tour). Une case d'action occupee par un
  ouvrier devient indisponible a l'autre joueur pour le reste du tour.
- **3 ressources**: bois, pierre, roseau, qui s'accumulent sur leurs cases du
  plateau central a chaque debut de tour si personne ne les prend
  (`rules_data.ACCUMULATING_SPACES`).
- **4 especes animales** (mouton, cochon, vache, cheval), obtenues via des
  cases d'accumulation dediees sur le plateau.
- **Plateau de depart**: grille 3x2 (2 cases maison + 4 cases ouvertes), avec
  jusqu'a **2 tuiles d'extension** de 3 cases chacune (achetees en
  ressources).
- **Clotures**: se posent sur les bordures entre 2 cases (ou le bord du
  plateau, toujours gratuit) et se paient en bois OU en pierre, 1 ressource
  par segment. **Deux enclos voisins mutualisent** la barriere qui les
  separe (payee une seule fois — le moteur retient chaque arete deja
  cloturee). Les bords de la **maison** et des **batiments** (stalle/etable)
  font office de **murs naturels gratuits**. Une fois posee, une
  barriere/auge/batiment n'est plus jamais deplacee.
- **Capacite des enclos**: un enclos de N cases loge `N x 2` animaux de base,
  et ce nombre **double par auge** ajoutee (jusqu'a 3 auges -> `N x 16`). Une
  case non cloturee ne loge un animal que si elle est equipee d'une auge (1
  animal). Une **Stalle** (1 case, 3 bois + 1 pierre, 1 PV) loge 4 animaux
  sans cloture, et peut etre amelioree en **Etable** (5 bois ou 5 pierre, 2
  PV, 5 animaux) ou **Etable ouverte** (5 bois ou 5 pierre, 2 PV, 4 animaux).
  Une auge sur un batiment ajoute +1 animal.
- **Maison a colombage**: renovation de la maison de depart (3 bois + 1
  pierre, +2 PV en fin de partie, aucune capacite animale).
- **Reproduction**: a la fin de **chaque** tour, tout groupe d'au moins 2
  animaux de la meme espece avec de la place produit 1 bebe supplementaire.
- **Batiments speciaux**: pool partage distinct (Bergerie, Porcherie, Puits,
  Carriere privee, Entrepot...), achetes contre ressources sans occuper de
  case de ferme, rapportent des PV directs et parfois un bonus. L'Entrepot
  rapporte +0.5 PV par ressource restante en reserve en fin de partie.
- **Score final**: `+1 PV` par animal, plus un **bareme par paliers propre a
  chaque espece** (malus fixe de -3 PV si moins de 4 animaux d'une espece,
  paliers croissants ensuite), plus les PV des batiments (stalle/etable,
  maison a colombage, batiments speciaux), plus **+4 PV par tuile
  d'extension entierement amenagee** (batiment, auge ou pature cloturee sur
  ses 3 cases) en fin de partie.
- **Egalite**: en cas de score final egal, le joueur qui n'a **pas** commence
  la toute premiere manche l'emporte.

**Ce qui reste une approximation** (la synthese fournie ne donne pas ces
details, donc des valeurs raisonnables ont ete choisies et sont centralisees
dans `rules_data.py` pour rester faciles a corriger):

- Les incrementations exactes d'accumulation par tour (bois/pierre/roseau/
  animaux) sont des choix d'equilibrage.
- Les enclos sont des **rectangles** (pas de formes libres).
- Les tuiles d'extension ont une forme/un emplacement/un cout fixes choisis
  arbitrairement (2 tuiles de 3 cases), plutot que le systeme exact du jeu.
- Le pool de "batiments speciaux" (au-dela de l'Entrepot, donne en exemple)
  utilise des noms/couts/PV generiques plutot que la liste exacte du jeu
  physique.
- Les animaux places restent **fixes** une fois poses: le moteur ne modelise
  pas le redeplacement libre des animaux entre emplacements (contrairement
  aux barrieres/auges/batiments qui sont bien immuables comme dans le vrai
  jeu, les animaux, eux, peuvent normalement etre redeplaces librement).
- Le bot MCTS clone l'etat de jeu (y compris l'accumulation a venir, fixee au
  moment du clone): depuis un etat donne, la partie redevient donc a
  information parfaite, ce qui simplifie l'algorithme (MCTS classique plutot
  qu'un MCTS a information imparfaite/ISMCTS).

**Tout est centralise dans `agricola2p/engine/rules_data.py`** precisement
pour que ce soit facile a corriger: si une source plus precise est
disponible, il suffit d'ajuster les constantes/tables de ce fichier — aucun
autre module ne contient de valeur numerique "en dur". Le reste du moteur
(`farmyard.py`, `actions.py`, `game.py`) reste correct quelles que soient ces
valeurs.

## Prochaines etapes possibles

- Modeliser le redeplacement libre des animaux entre emplacements.
- Remplacer le pool generique de batiments speciaux et les tuiles
  d'extension par les vraies listes du jeu (texte + effet exact + formes).
- Autoriser des formes d'enclos non rectangulaires (clotures libres).
- Ajouter un bot par apprentissage par renforcement (self-play, type
  AlphaZero simplifie) une fois le moteur valide/ajuste par rapport au jeu
  physique — le `MCTSBot` actuel peut deja servir de generateur de parties
  d'entrainement.
- Interface graphique / web pour jouer contre un bot.
