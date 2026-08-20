"""Bot MCTS (Monte Carlo Tree Search) avec selection UCB1.

Simplification assumee: la seule source d'alea du moteur (l'ordre de la
pioche de cartes bonus) est fixee au moment ou l'etat de jeu est clone, donc
depuis un GameState donne, la partie devient un jeu a information parfaite et
deterministe. On peut donc faire du MCTS "classique" (comme aux echecs/Go)
sans les complications d'un MCTS a information imparfaite (ISMCTS). C'est une
approximation raisonnable pour une premiere version: en pratique un joueur
humain ne connait pas l'ordre des cartes a venir, donc ce bot est legerement
"omniscient" sur ce point precis.
"""

from __future__ import annotations

import copy
import math
import random

from ..engine.actions import Action
from ..engine.game import AgricolaGame
from .base import Bot


class _Node:
    def __init__(self, game: AgricolaGame, owner: int | None, parent: "_Node | None"):
        self.game = game
        self.owner = owner  # joueur qui a joue le coup menant a ce noeud (None = racine)
        self.parent = parent
        self.children: list[tuple[Action, "_Node"]] = []
        self.untried: list[Action] | None = None
        self.visits = 0
        self.total_value = 0.0

    def uct_score(self, parent_visits: int, c: float) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.total_value / self.visits
        exploration = c * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration


class MCTSBot(Bot):
    name = "mcts"

    def __init__(
        self,
        iterations: int = 200,
        exploration: float = 1.4,
        rollout_policy: Bot | None = None,
        seed: int | None = None,
        max_rollout_moves: int = 400,
    ):
        self.iterations = iterations
        self.c = exploration
        self.rng = random.Random(seed)
        self.max_rollout_moves = max_rollout_moves
        if rollout_policy is None:
            from .random_bot import RandomBot

            rollout_policy = RandomBot(seed=seed)
        self.rollout_policy = rollout_policy

    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        actions = game.legal_actions()
        if len(actions) == 1:
            return actions[0]

        root = _Node(copy.deepcopy(game), owner=None, parent=None)

        for _ in range(self.iterations):
            node = self._select(root)
            if not node.game.is_terminal():
                node = self._expand(node)
            value_for_root = self._rollout(node.game, player_idx)
            self._backpropagate(node, player_idx, value_for_root)

        best_action, _ = max(root.children, key=lambda pair: pair[1].visits)
        return best_action

    def _select(self, node: "_Node") -> "_Node":
        while not node.game.is_terminal():
            if node.untried is None:
                node.untried = list(node.game.legal_actions())
            if node.untried:
                return node
            if not node.children:
                return node
            _, node = max(node.children, key=lambda pair: pair[1].uct_score(node.visits, self.c))
        return node

    def _expand(self, node: "_Node") -> "_Node":
        if node.untried is None:
            node.untried = list(node.game.legal_actions())
        if not node.untried:
            return node
        action = node.untried.pop(self.rng.randrange(len(node.untried)))
        clone = copy.deepcopy(node.game)
        mover = clone.current_player_idx
        clone.apply(action)
        child = _Node(clone, owner=mover, parent=node)
        node.children.append((action, child))
        return child

    def _rollout(self, game: AgricolaGame, player_idx: int) -> float:
        sim = copy.deepcopy(game)
        moves = 0
        while not sim.is_terminal() and moves < self.max_rollout_moves:
            mover = sim.current_player_idx
            action = self.rollout_policy.choose_action(sim, mover)
            sim.apply(action)
            moves += 1
        scores = sim.scores()
        opponent_idx = 1 - player_idx
        return float(scores[player_idx] - scores[opponent_idx])

    def _backpropagate(self, node: "_Node", player_idx: int, value_for_root: float) -> None:
        n: _Node | None = node
        while n is not None:
            n.visits += 1
            if n.owner is not None:
                contribution = value_for_root if n.owner == player_idx else -value_for_root
                n.total_value += contribution
            n = n.parent
