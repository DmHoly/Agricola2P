"""Etat du jeu: PlayerState et GameState."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import rules_data as R
from .cards import BonusCard, shuffled_deck
from .constants import Resource
from .farmyard import Farmyard


@dataclass
class PlayerState:
    name: str
    farmyard: Farmyard = field(default_factory=Farmyard)
    resources: dict[Resource, int] = field(default_factory=lambda: dict(R.INITIAL_RESOURCES))
    bonus_points: int = 0

    def can_afford(self, cost: dict[Resource, int]) -> bool:
        return all(self.resources.get(res, 0) >= amount for res, amount in cost.items())

    def pay(self, cost: dict[Resource, int]) -> None:
        if not self.can_afford(cost):
            raise ValueError("Ressources insuffisantes")
        for res, amount in cost.items():
            self.resources[res] -= amount

    def gain(self, resources: dict[Resource, int]) -> None:
        for res, amount in resources.items():
            self.resources[res] = self.resources.get(res, 0) + amount


@dataclass
class GameState:
    players: list[PlayerState]
    round_no: int = 1
    stage: int = 1
    active_player_idx: int = 0
    starting_player_idx: int = 0
    occupied_spaces: dict[str, int] = field(default_factory=dict)
    unlocked_spaces: list[str] = field(default_factory=list)
    deck: list[BonusCard] = field(default_factory=list)
    discard: list[BonusCard] = field(default_factory=list)
    moves_this_round: int = 0
    finished: bool = False
    final_scores: list[int] | None = None

    @classmethod
    def new_game(cls, player_names: tuple[str, str] = ("P1", "P2"), seed: int | None = None) -> "GameState":
        import random

        rng = random.Random(seed)
        players = [PlayerState(name=n) for n in player_names]
        state = cls(players=players, deck=shuffled_deck(rng))
        state.unlock_stage_spaces(1)
        return state

    def unlock_stage_spaces(self, stage: int) -> None:
        for space_id, _kind in R.ACTION_SPACES_BY_STAGE.get(stage, []):
            if space_id not in self.unlocked_spaces:
                self.unlocked_spaces.append(space_id)

    def opponent_idx(self, idx: int) -> int:
        return 1 - idx

    def is_space_free(self, space_id: str) -> bool:
        return space_id not in self.occupied_spaces
