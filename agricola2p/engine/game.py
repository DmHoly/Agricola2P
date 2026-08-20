"""Boucle de jeu complete: tours (6 placements), reproduction, score final."""

from __future__ import annotations

from . import rules_data as R
from .actions import Action, apply_action, legal_actions
from .state import GameState, PlayerState, _round_turn_order


def score_player(player: PlayerState) -> float:
    fy = player.farmyard
    total = 0.0

    animals = fy.total_animals()
    total += sum(animals.values()) * R.BASE_POINTS_PER_ANIMAL
    for species, count in animals.items():
        total += R.species_points(species, count)

    total += sum(b.points for b in player.buildings)
    leftover = sum(player.resources.values())
    total += sum(b.per_leftover_resource * leftover for b in player.buildings)

    total += sum(building.points() for building in fy.building_cells.values())
    if fy.house_upgraded:
        total += R.HOUSE_UPGRADE_POINTS

    for tile in R.EXTENSION_TILES:
        if tile["id"] in fy.owned_tiles and fy.tile_fully_used(tile["cells"]):
            total += R.EXTENSION_COMPLETE_BONUS_PER_TILE

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
        if action.kind != "reorganize":
            # le redeplacement libre d'animaux ne consomme pas le tour de
            # l'ouvrier: le meme joueur continue avec sa vraie action.
            self._advance_turn()

    def scores(self) -> list[float]:
        return [score_player(p) for p in self.state.players]

    def winner(self) -> int | None:
        """Index du gagnant. En cas d'egalite stricte des scores, le joueur
        qui N'a PAS commence la toute premiere manche l'emporte (regle
        d'egalite: "le 1er joueur de la manche 1 perd l'egalite")."""
        s = self.scores()
        if s[0] == s[1]:
            return 1 - self.state.first_mover_idx
        return 0 if s[0] > s[1] else 1

    # -- interne ----------------------------------------------------
    def _advance_turn(self) -> None:
        state = self.state
        state.reorg_used_this_turn = False  # nouveau tour d'ouvrier: redeplacement gratuit dispo a nouveau
        state.turn_index += 1
        if state.turn_index < len(state.turn_order):
            return

        # les 6 placements du tour ont eu lieu: fin de manche
        state.occupied_spaces = {}
        for player in state.players:
            player.farmyard.breed()

        state.round_no += 1
        if state.round_no > R.TOTAL_ROUNDS:
            state.finished = True
            state.final_scores = self.scores()
            return

        state.starting_player_idx = state.opponent_idx(state.starting_player_idx)
        state.turn_order = _round_turn_order(state.starting_player_idx)
        state.turn_index = 0
        state.accumulate_round()
