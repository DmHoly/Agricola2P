"""Definition des actions possibles et generation des coups legaux.

Un `Action` represente un coup complet et concret (espace choisi + parametres
comme la case, le rectangle de pature, le materiau de renovation...). C'est
ce qu'un bot manipule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import rules_data as R
from .constants import Animal, HouseMaterial
from .farmyard import Cell, FarmyardError
from .state import GameState, PlayerState

SPACE_KIND: dict[str, str] = {
    space_id: kind
    for spaces in R.ACTION_SPACES_BY_STAGE.values()
    for space_id, kind in spaces
}


@dataclass(frozen=True)
class Action:
    space_id: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover - lisibilite debug
        return f"Action({self.space_id}, {self.payload})"


PASS = Action(space_id="pass", kind="pass")


def _fence_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    actions: list[Action] = []
    for r1 in range(fy.rows):
        for r2 in range(r1, fy.rows):
            for c1 in range(fy.cols):
                for c2 in range(c1, fy.cols):
                    if not fy.can_build_pasture(r1, c1, r2, c2):
                        continue
                    cost = fy.fence_cost_for_rectangle(r1, c1, r2, c2)
                    if player.resources.get(R.Resource.WOOD, 0) >= cost and cost > 0:
                        actions.append(Action("fencing", "fence", {"rect": (r1, c1, r2, c2)}))
    return actions


def _stable_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    if not player.can_afford(R.STABLE_COST):
        return []
    out = []
    for cell in fy.all_cells():
        if fy.is_house(cell):
            continue
        if fy.can_build_stable(cell):
            out.append(Action("build_stable", "stable", {"cell": cell}))
    return out


def _market_actions(space_id: str, player: PlayerState) -> list[Action]:
    species = R.ANIMAL_MARKET_SPACES[space_id]
    fy = player.farmyard
    out = []
    for kind, ref, sp, free in fy.available_capacity():
        if sp != species or free <= 0:
            continue
        out.append(Action(space_id, "market", {"species": species, "target_kind": kind, "target_ref": ref}))
    return out


def _renovate_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    nxt = fy.house_material.next
    if nxt is None:
        return []
    cost = R.RENOVATION_COST.get(nxt)
    if cost is None or not player.can_afford(cost):
        return []
    return [Action("renovate", "renovate", {"material": nxt.value})]


def _build_room_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    cost = R.BUILD_ROOM_COST.get(fy.house_material)
    if cost is None or not player.can_afford(cost):
        return []
    out = []
    for cell in fy.free_cells():
        adjacent = any(
            (cell[0] + dr, cell[1] + dc) in fy.house_cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        if adjacent:
            out.append(Action("build_room", "build_room", {"cell": cell}))
    return out


def _wagon_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    if fy.wagons >= R.MAX_WAGONS:
        return []
    if not player.can_afford(R.WAGON_COST):
        return []
    return [Action("wagon", "wagon", {})]


def legal_actions(state: GameState, player_idx: int) -> list[Action]:
    player = state.players[player_idx]
    out: list[Action] = []
    for space_id in state.unlocked_spaces:
        if not state.is_space_free(space_id):
            continue
        kind = SPACE_KIND[space_id]
        if kind == "resource":
            out.append(Action(space_id, kind, {}))
        elif kind == "fence":
            out.extend(_fence_actions(player))
        elif kind == "stable":
            out.extend(_stable_actions(player))
        elif kind == "market":
            out.extend(_market_actions(space_id, player))
        elif kind == "renovate":
            out.extend(_renovate_actions(player))
        elif kind == "build_room":
            out.extend(_build_room_actions(player))
        elif kind == "wagon":
            out.extend(_wagon_actions(player))
        elif kind == "bonus_card":
            out.append(Action(space_id, kind, {}))
    if not out:
        out.append(PASS)
    return out


def apply_action(state: GameState, player_idx: int, action: Action) -> None:
    player = state.players[player_idx]
    fy = player.farmyard

    if action.kind == "pass":
        return

    if action.space_id in state.occupied_spaces or (
        action.space_id != "pass" and action.space_id not in state.unlocked_spaces
    ):
        raise FarmyardError(f"Espace {action.space_id} indisponible")

    if action.kind == "resource":
        player.gain(R.RESOURCE_SPACE_YIELD[action.space_id])

    elif action.kind == "fence":
        r1, c1, r2, c2 = action.payload["rect"]
        cost = fy.fence_cost_for_rectangle(r1, c1, r2, c2)
        player.pay({R.Resource.WOOD: cost})
        fy.build_pasture(r1, c1, r2, c2)

    elif action.kind == "stable":
        player.pay(R.STABLE_COST)
        fy.build_stable(tuple(action.payload["cell"]))

    elif action.kind == "market":
        species = Animal(action.payload["species"])
        target_kind = action.payload["target_kind"]
        target_ref = action.payload["target_ref"]
        if target_kind == "pasture":
            fy.add_animals_to_pasture(target_ref, species, R.ANIMAL_MARKET_TAKE)
        else:
            fy.add_animals_to_cell(tuple(target_ref), species, R.ANIMAL_MARKET_TAKE)

    elif action.kind == "renovate":
        material = HouseMaterial(action.payload["material"])
        player.pay(R.RENOVATION_COST[material])
        fy.renovate(material)

    elif action.kind == "build_room":
        cell = tuple(action.payload["cell"])
        player.pay(R.BUILD_ROOM_COST[fy.house_material])
        fy.add_room(cell)

    elif action.kind == "wagon":
        player.pay(R.WAGON_COST)
        fy.wagons += 1

    elif action.kind == "bonus_card":
        if state.deck:
            card = state.deck.pop()
            player.gain(card.resource_gain)
            player.bonus_points += card.points
            state.discard.append(card)

    else:  # pragma: no cover - garde-fou
        raise ValueError(f"Type d'action inconnu: {action.kind}")

    state.occupied_spaces[action.space_id] = player_idx
