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

Le ruleset implemente suit la synthese fournie (basee sur la presentation
video d'Agricola: Terre d'Elevage par la chaine Ludovox):

- **Partie en 8 tours**, chaque joueur disposant de **3 ouvriers** (6
  placements d'ouvrier au total par tour). Une case d'action occupee par un
  ouvrier devient indisponible a l'autre joueur pour le reste du tour.
- **3 ressources**: bois, pierre, roseau. Elles s'accumulent sur leurs cases
  du plateau central a chaque debut de tour si personne ne les prend
  (`rules_data.ACCUMULATING_SPACES`); prendre la case donne tout ce qui s'y
  est accumule et la remet a zero.
- **4 especes animales**: mouton, cochon, vache, cheval. Elles proviennent
  elles aussi de cases d'accumulation dediees sur le plateau (pas d'achat
  contre ressources).
- **Enclos/clotures**: un enclos pose (rectangle de cases cloturees) ne peut
  plus etre deplace ni modifie ensuite. Un animal seul peut occuper une case
  non cloturee (1 max); un enclos loge plusieurs animaux de la meme espece;
  une etable (batiment construit sur une case) abrite aussi des animaux et en
  augmente la capacite.
- **Reproduction**: a la fin de **chaque** tour, tout groupe d'au moins 2
  animaux de la meme espece avec de la place produit 1 bebe supplementaire.
- **Agrandissement**: la ferme grandit exclusivement via l'achat de tuiles
  d'extension (`rules_data.EXTENSION_TILES`), payees en ressources.
- **Batiments speciaux**: construits contre ressources, rapportent des points
  de victoire directs et parfois un petit bonus immediat.
- **Score final**: total par espece selon un bareme unique
  (`rules_data.ANIMAL_SCORE_TABLE`) qui penalise avoir **moins de 3** animaux
  d'une espece et recompense les paliers superieurs, + points des batiments
  speciaux construits, + bonus "exploitation complete" par tuile d'extension
  entierement amenagee (aucune case libre dessus) en fin de partie.

**Ce qui reste une approximation** (la synthese fournie ne donne pas ces
details, donc des valeurs raisonnables ont ete choisies et sont centralisees
dans `rules_data.py` pour rester faciles a corriger):

- Les incrementations exactes d'accumulation par tour (bois/pierre/roseau/
  animaux), les couts de cloture/etable/tuiles/batiments, et le bareme de
  score precis sont des choix d'equilibrage, pas une retranscription du
  livret officiel.
- Les enclos sont des **rectangles** (pas de formes libres).
- Les tuiles d'extension ont une forme, un emplacement et un cout fixes
  choisis arbitrairement (5 tuiles de 2 cases), plutot que le systeme exact
  du jeu (ordre d'achat, formes variees, etc.).
- Les "batiments speciaux" utilisent un **pool generique** de 7 batiments a
  cout/points/bonus simples, plutot que la liste exacte et les capacites
  particulieres du jeu physique.
- Le bot MCTS clone l'etat de jeu (y compris l'accumulation a venir, fixee au
  moment du clone): depuis un etat donne, la partie redevient donc a
  information parfaite, ce qui simplifie l'algorithme (MCTS classique plutot
  qu'un MCTS a information imparfaite/ISMCTS).

**Tout est centralise dans `agricola2p/engine/rules_data.py`** precisement
pour que ce soit facile a corriger: si une source plus precise (livret de
regles) est disponible, il suffit d'ajuster les constantes/tables de ce
fichier — aucun autre module ne contient de valeur numerique "en dur". Le
reste du moteur (`farmyard.py`, `actions.py`, `game.py`) reste correct quelles
que soient ces valeurs.

## Prochaines etapes possibles

- Remplacer le pool generique de batiments speciaux et les tuiles
  d'extension par les vraies listes du jeu (texte + effet exact + formes).
- Autoriser des formes d'enclos non rectangulaires (clotures libres).
- Ajouter un bot par apprentissage par renforcement (self-play, type
  AlphaZero simplifie) une fois le moteur valide/ajuste par rapport au jeu
  physique — le `MCTSBot` actuel peut deja servir de generateur de parties
  d'entrainement.
- Interface graphique / web pour jouer contre un bot.
