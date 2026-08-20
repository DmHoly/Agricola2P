"""Bot glouton: essaie chaque coup legal 1 coup a l'avance et garde celui qui
maximise (mon score - score adverse) apres application, selon le bareme de
score final (agricola2p.engine.game.score_player). Simple mais deja un
adversaire correct pour tester le moteur et servir de rollout policy au MCTS.
"""

from __future__ import annotations

import copy
import random

from ..engine.actions import Action
from ..engine.game import AgricolaGame, score_player
from .base import Bot


class HeuristicBot(Bot):
    name = "heuristic"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        actions = game.legal_actions()
        if len(actions) == 1:
            return actions[0]

        opponent_idx = 1 - player_idx
        best_actions: list[Action] = []
        best_value = float("-inf")

        for action in actions:
            clone = copy.deepcopy(game)
            clone.apply(action)
            value = score_player(clone.state.players[player_idx]) - score_player(
                clone.state.players[opponent_idx]
            )
            if value > best_value:
                best_value = value
                best_actions = [action]
            elif value == best_value:
                best_actions.append(action)

        return self.rng.choice(best_actions)
