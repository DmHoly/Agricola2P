"""Etat du jeu: PlayerState et GameState."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import rules_data as R
from .buildings import SpecialBuilding, shuffled_pool
from .constants import Resource
from .farmyard import Farmyard


@dataclass
class PlayerState:
    name: str
    farmyard: Farmyard = field(default_factory=Farmyard)
    resources: dict[Resource, int] = field(default_factory=lambda: {r: 0 for r in Resource})
    buildings: list[SpecialBuilding] = field(default_factory=list)

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


def _initial_accumulators() -> dict[str, int]:
    return {space_id: 0 for space_id in R.ACCUMULATING_SPACES}


@dataclass
class GameState:
    players: list[PlayerState]
    round_no: int = 1
    starting_player_idx: int = 0
    turn_order: list[int] = field(default_factory=list)
    turn_index: int = 0
    occupied_spaces: dict[str, int] = field(default_factory=dict)
    accumulators: dict[str, int] = field(default_factory=_initial_accumulators)
    available_buildings: list[SpecialBuilding] = field(default_factory=list)
    finished: bool = False
    final_scores: list[int] | None = None

    @classmethod
    def new_game(cls, player_names: tuple[str, str] = ("P1", "P2"), seed: int | None = None) -> "GameState":
        import random

        rng = random.Random(seed)
        players = [PlayerState(name=n) for n in player_names]
        state = cls(players=players, available_buildings=shuffled_pool(rng))
        state.turn_order = _round_turn_order(state.starting_player_idx)
        state.accumulate_round()
        return state

    @property
    def active_player_idx(self) -> int:
        return self.turn_order[self.turn_index]

    def opponent_idx(self, idx: int) -> int:
        return 1 - idx

    def is_space_free(self, space_id: str) -> bool:
        return space_id not in self.occupied_spaces

    def accumulate_round(self) -> None:
        for space_id, (_kind, _target, amount) in R.ACCUMULATING_SPACES.items():
            self.accumulators[space_id] = self.accumulators.get(space_id, 0) + amount


def _round_turn_order(starting_player_idx: int) -> list[int]:
    other = 1 - starting_player_idx
    return [starting_player_idx, other] * R.WORKERS_PER_PLAYER
