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

## Fidelite aux regles officielles — a lire avant de juger la "force" des bots

Ce depot **n'est pas** une retranscription exacte et verifiee du livret de
regles officiel. La structure generale du jeu est fidele:

- 2 joueurs, 1 seul ouvrier chacun, pas de phase de recolte/faim (contrairement
  a l'Agricola classique) — le jeu tourne autour de la construction et de
  l'elevage.
- 14 manches decoupees en 4 stades (fins de stade aux manches 4, 8, 11, 14),
  avec deverrouillage progressif de nouveaux espaces d'action et une phase de
  reproduction des animaux a chaque fin de stade.
- 4 especes animales (lapin, mouton, sanglier, vache), 4 ressources
  (bois, argile, roseau, pierre), clotures/patures, etables, renovation de la
  maison, chariots, cartes bonus.

En revanche, **les valeurs numeriques precises** (couts exacts, capacites de
patures par espece, bareme de score final, texte et effets exacts des
dizaines de cartes bonus/ameliorations du jeu physique) sont des
approximations raisonnables reconstruites de memoire, pas une source de
verite. Simplifications assumees notables:

- Les patures sont des **rectangles** (pas de formes quelconques).
- Les cartes bonus utilisent un **pool generique** de ~10 cartes a effet
  immediat (ressources ou points) plutot que les dizaines de cartes uniques
  du jeu reel (`agricola2p/engine/cards.py`).
- Le bot MCTS clone l'etat de jeu (y compris l'ordre restant de la pioche de
  cartes bonus, fixe au moment du clone) : depuis un etat donne, la partie
  redevient donc a information parfaite, ce qui simplifie l'algorithme
  (MCTS classique plutot qu'un MCTS a information imparfaite/ISMCTS) au prix
  d'un leger avantage "omniscient" sur l'ordre des cartes a venir.

**Tout est centralise dans `agricola2p/engine/rules_data.py`** precisement
pour que ce soit facile a corriger: si tu as le livret de regles sous la
main, il suffit d'ajuster les constantes/tables de ce fichier (couts,
capacites, bareme de score, plateau des manches/stades) — aucun autre module
ne contient de valeur numerique "en dur". Le reste du moteur (`farmyard.py`,
`actions.py`, `game.py`) est ecrit pour rester correct quelles que soient ces
valeurs.

## Prochaines etapes possibles

- Remplacer le pool generique de cartes bonus par la vraie liste de cartes du
  jeu (texte + effet exact).
- Autoriser des formes de pature non rectangulaires (clotures libres).
- Ajouter un bot par apprentissage par renforcement (self-play, type
  AlphaZero simplifie) une fois le moteur valide/ajuste par rapport au jeu
  physique — le `MCTSBot` actuel peut deja servir de generateur de parties
  d'entrainement.
- Interface graphique / web pour jouer contre un bot.
