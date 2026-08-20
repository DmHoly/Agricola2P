"""Interface commune a tous les bots."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..engine.actions import Action
from ..engine.game import AgricolaGame


class Bot(ABC):
    name: str = "bot"

    @abstractmethod
    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        """Retourne l'action choisie parmi game.legal_actions()."""
        raise NotImplementedError
