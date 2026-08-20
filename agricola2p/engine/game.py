"""Boucle de jeu complete: tours, manches, stades, reproduction, score final."""

from __future__ import annotations

from . import rules_data as R
from .actions import Action, apply_action, legal_actions
from .state import GameState, PlayerState


def score_player(player: PlayerState) -> int:
    fy = player.farmyard
    total = 0

    animals = fy.total_animals()
    for species, count in animals.items():
        table = R.ANIMAL_SCORE_TABLE[species]
        idx = min(count, len(table) - 1)
        total += table[idx]

    total += len(fy.pastures) * R.PASTURE_POINTS
    num_stables = sum(p.stables for p in fy.pastures.values()) + len(fy.stable_cells)
    total += num_stables * R.STABLE_POINTS
    total += len(fy.house_cells) * R.ROOM_POINTS[fy.house_material]
    total += fy.wagons * R.WAGON_POINTS
    total += fy.empty_cells_count() * R.EMPTY_SPACE_PENALTY
    total += player.bonus_points

    return total


class AgricolaGame:
    """Wrapper haut-niveau autour de GameState, utilise par les bots/CLI."""

    def __init__(self, state: GameState | None = None):
        self.state = state or GameState.new_game()

    @classmethod
    def new_game(cls, player_names: tuple[str, str] = ("P1", "P2"), seed: int | None = None) -> "AgricolaGame":
        return cls(GameState.new_game(player_names, seed=seed))

    # -- interface publique ------------------------------------------
    @property
    def current_player_idx(self) -> int:
        return self.state.active_player_idx

    def is_terminal(self) -> bool:
        return self.state.finished

    def legal_actions(self) -> list[Action]:
        if self.is_terminal():
            return []
        return legal_actions(self.state, self.state.active_player_idx)

    def apply(self, action: Action) -> None:
        if self.is_terminal():
            raise RuntimeError("La partie est terminee")
        player_idx = self.state.active_player_idx
        apply_action(self.state, player_idx, action)
        self.state.moves_this_round += 1
        self._advance_turn()

    def scores(self) -> list[int]:
        return [score_player(p) for p in self.state.players]

    def winner(self) -> int | None:
        """Index du gagnant, ou None en cas d'egalite (partie doit etre finie)."""
        s = self.scores()
        if s[0] == s[1]:
            return None
        return 0 if s[0] > s[1] else 1

    # -- interne ----------------------------------------------------
    def _advance_turn(self) -> None:
        state = self.state
        if state.moves_this_round < len(state.players):
            state.active_player_idx = state.opponent_idx(state.active_player_idx)
            return

        # les deux joueurs ont joue: fin de manche
        state.occupied_spaces = {}
        state.moves_this_round = 0

        if state.round_no in R.STAGE_END_ROUNDS:
            for player in state.players:
                player.farmyard.breed()
            if state.stage < R.NUM_STAGES:
                state.stage += 1
                state.unlock_stage_spaces(state.stage)

        state.round_no += 1
        if state.round_no > R.TOTAL_ROUNDS:
            state.finished = True
            state.final_scores = self.scores()
            return

        state.starting_player_idx = state.opponent_idx(state.starting_player_idx)
        state.active_player_idx = state.starting_player_idx
