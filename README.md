# Agricola2P

Moteur de regles + bots pour **Agricola: Terre d'Elevage** (*All Creatures Big
and Small*, Uwe Rosenberg), le jeu de placement d'ouvriers a 2 joueurs centre
sur l'elevage.

Le detail des regles implementees (et leurs limites/hypotheses par rapport au
jeu physique) est dans **[RULES.md](RULES.md)**, et un guide strategique tire
de parties bot vs bot dans **[STRATEGY.md](STRATEGY.md)**.

## Contenu

- `agricola2p/engine/` — le moteur de jeu, entierement data-driven (voir
  `rules_data.py`).
- `agricola2p/bots/` — `RandomBot`, `HeuristicBot` (glouton 1 coup a
  l'avance, avec 2 heuristiques de reproduction), `MCTSBot` (Monte Carlo Tree
  Search, UCB1) et `RLBot` (glouton 1 coup guide par un reseau de valeur
  entraine par self-play, cf `agricola2p/rl/`).
- `agricola2p/rl/` — apprentissage par renforcement: encodage d'etat
  (`features.py`), reseau de valeur numpy (`value_net.py`), generation de
  parties de self-play et entrainement (`self_play.py`, `train.py`). Le
  meme reseau peut aussi remplacer les simulations du `MCTSBot` par une
  evaluation directe ("bootstrap", `mcts_value_fn.py`) — beaucoup plus
  rapide, cf plus bas.
- `agricola2p/cli.py` — fait jouer deux bots l'un contre l'autre en terminal.
- `tests/` — tests pytest (regles de la ferme, boucle de partie complete,
  bots).

## Installation rapide

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

Pour les bots RL (optionnel, necessite numpy):

```bash
python3 -m pip install -e ".[rl]"
python3 -m agricola2p.rl.train --games 3000 --epochs 80   # ~5-10 min, sauve agricola2p/rl/weights.npz
```

## Jouer une partie bot vs bot

```bash
python3 -m agricola2p.cli --p1 heuristic --p2 mcts --iterations 200 --seed 1
```

Bots disponibles: `random`, `heuristic`, `mcts`, `rl` (necessite d'avoir
entraine des poids au prealable, voir ci-dessus), `mcts_rl` (MCTS dont les
feuilles sont evaluees par le reseau appris au lieu d'etre simulees).

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
