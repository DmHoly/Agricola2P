"""Bot qui joue un coup legal au hasard (baseline)."""

from __future__ import annotations

import random

from ..engine.actions import Action
from ..engine.game import AgricolaGame
from .base import Bot


class RandomBot(Bot):
    name = "random"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        actions = game.legal_actions()
        return self.rng.choice(actions)
