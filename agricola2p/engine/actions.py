"""Definition des actions possibles et generation des coups legaux.

Un `Action` represente un coup complet et concret (espace choisi + parametres
comme la case, le rectangle d'enclos, la tuile ou le batiment choisi...).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import rules_data as R
from .constants import Animal, Resource
from .farmyard import FarmyardError
from .state import GameState, PlayerState


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
                    if cost <= 0:
                        continue
                    for resource in R.FENCE_RESOURCE_OPTIONS:
                        if player.resources.get(resource, 0) >= cost:
                            actions.append(
                                Action("fencing", "fence", {"rect": (r1, c1, r2, c2), "resource": resource.value})
                            )
    return actions


def _building_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    if not player.can_afford(R.STALLE_COST):
        return []
    return [
        Action("build_building", "building", {"cell": cell})
        for cell in fy.playable_cells()
        if fy.can_build_building(cell)
    ]


def _upgrade_building_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    out = []
    for cell in fy.building_cells:
        if not fy.can_upgrade_building(cell):
            continue
        for new_level in R.BUILDING_UPGRADE_TARGETS:
            for cost in R.BUILDING_UPGRADE_COST_OPTIONS:
                if player.can_afford(cost):
                    out.append(
                        Action(
                            "upgrade_building",
                            "upgrade_building",
                            {"cell": cell, "new_level": new_level, "cost": {r.value: v for r, v in cost.items()}},
                        )
                    )
    return out


def _upgrade_house_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    if fy.can_upgrade_house() and player.can_afford(R.HOUSE_UPGRADE_COST):
        return [Action("upgrade_house", "upgrade_house", {})]
    return []


def _trough_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    if not player.can_afford(R.TROUGH_COST):
        return []
    out = []
    for pasture_id in fy.pastures:
        if fy.can_build_trough_on_pasture(pasture_id):
            out.append(Action("build_trough", "trough", {"target_kind": "pasture", "target_ref": pasture_id}))
    for cell in fy.building_cells:
        if fy.can_build_trough_on_building(cell):
            out.append(Action("build_trough", "trough", {"target_kind": "building", "target_ref": cell}))
    for cell in fy.playable_cells():
        if fy.can_build_trough_on_yard(cell):
            out.append(Action("build_trough", "trough", {"target_kind": "yard", "target_ref": cell}))
    return out


def _animal_accum_actions(space_id: str, state: GameState, player: PlayerState) -> list[Action]:
    _kind, species, _amount = R.ACCUMULATING_SPACES[space_id]
    if state.accumulators.get(space_id, 0) <= 0:
        return []
    fy = player.farmyard
    out = []
    for kind, ref, sp, free in fy.available_capacity():
        if sp != species or free <= 0:
            continue
        out.append(Action(space_id, "animal_accum", {"species": species, "target_kind": kind, "target_ref": ref}))
    return out


def _extension_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    out = []
    for tile in R.EXTENSION_TILES:
        if tile["id"] in fy.owned_tiles:
            continue
        if player.can_afford(tile["cost"]):
            out.append(Action("extension", "extension", {"tile_id": tile["id"]}))
    return out


def _special_building_actions(state: GameState, player: PlayerState) -> list[Action]:
    out = []
    for building in state.available_buildings:
        if player.can_afford(building.cost):
            out.append(Action("special_building", "special_building", {"building_name": building.name}))
    return out


def _reorganize_actions(state: GameState, player: PlayerState) -> list[Action]:
    """Redeplacement libre d'animaux entre 2 emplacements deja construits
    (enclos/batiment/case a auge), en respectant 1 seule espece par
    emplacement. Ne consomme pas d'ouvrier ni d'espace du plateau: limite a
    1 par tour d'ouvrier (cf state.reorg_used_this_turn) pour rester borne.
    """
    if state.reorg_used_this_turn:
        return []
    fy = player.farmyard
    sources = fy.occupied_locations()
    destinations = fy.available_capacity()
    out = []
    for from_kind, from_ref, species, count in sources:
        for to_kind, to_ref, dst_species, free in destinations:
            if dst_species != species or (from_kind, from_ref) == (to_kind, to_ref):
                continue
            n = min(count, free)
            if n > 0:
                out.append(
                    Action(
                        "reorganize",
                        "reorganize",
                        {
                            "from_kind": from_kind,
                            "from_ref": from_ref,
                            "to_kind": to_kind,
                            "to_ref": to_ref,
                            "species": species,
                            "count": n,
                        },
                    )
                )
    return out


def legal_actions(state: GameState, player_idx: int) -> list[Action]:
    player = state.players[player_idx]
    out: list[Action] = []
    for space_id in R.ALL_ACTION_SPACES:
        if not state.is_space_free(space_id):
            continue
        kind = R.ACTION_SPACE_KIND[space_id]
        if kind == "resource_accum":
            if state.accumulators.get(space_id, 0) > 0:
                out.append(Action(space_id, kind, {}))
        elif kind == "animal_accum":
            out.extend(_animal_accum_actions(space_id, state, player))
        elif kind == "fence":
            out.extend(_fence_actions(player))
        elif kind == "building":
            out.extend(_building_actions(player))
        elif kind == "upgrade_building":
            out.extend(_upgrade_building_actions(player))
        elif kind == "upgrade_house":
            out.extend(_upgrade_house_actions(player))
        elif kind == "trough":
            out.extend(_trough_actions(player))
        elif kind == "extension":
            out.extend(_extension_actions(player))
        elif kind == "special_building":
            out.extend(_special_building_actions(state, player))
    out.extend(_reorganize_actions(state, player))
    if not out:
        out.append(PASS)
    return out


def apply_action(state: GameState, player_idx: int, action: Action) -> None:
    player = state.players[player_idx]
    fy = player.farmyard

    if action.kind == "pass":
        return

    if action.kind == "reorganize":
        fy.move_animals(
            action.payload["from_kind"],
            action.payload["from_ref"],
            action.payload["to_kind"],
            action.payload["to_ref"],
            Animal(action.payload["species"]),
            action.payload["count"],
        )
        state.reorg_used_this_turn = True
        return

    if action.space_id not in R.ALL_ACTION_SPACES or action.space_id in state.occupied_spaces:
        raise FarmyardError(f"Espace {action.space_id} indisponible")

    if action.kind == "resource_accum":
        _kind, resource, _amount = R.ACCUMULATING_SPACES[action.space_id]
        gained = state.accumulators.get(action.space_id, 0)
        player.gain({resource: gained})
        state.accumulators[action.space_id] = 0

    elif action.kind == "animal_accum":
        species = Animal(action.payload["species"])
        target_kind = action.payload["target_kind"]
        target_ref = action.payload["target_ref"]
        available = state.accumulators.get(action.space_id, 0)
        if target_kind == "pasture":
            taken = fy.add_animals_to_pasture(target_ref, species, available)
        else:
            taken = fy.add_animals_to_cell(tuple(target_ref), species, available)
        state.accumulators[action.space_id] = max(0, available - taken)

    elif action.kind == "fence":
        r1, c1, r2, c2 = action.payload["rect"]
        resource = Resource(action.payload["resource"])
        cost = fy.fence_cost_for_rectangle(r1, c1, r2, c2)
        player.pay({resource: cost})
        fy.build_pasture(r1, c1, r2, c2)

    elif action.kind == "building":
        player.pay(R.STALLE_COST)
        fy.build_building(tuple(action.payload["cell"]))

    elif action.kind == "upgrade_building":
        cell = tuple(action.payload["cell"])
        new_level = action.payload["new_level"]
        cost = {Resource(r): v for r, v in action.payload["cost"].items()}
        player.pay(cost)
        fy.upgrade_building(cell, new_level)

    elif action.kind == "upgrade_house":
        player.pay(R.HOUSE_UPGRADE_COST)
        fy.upgrade_house()

    elif action.kind == "trough":
        player.pay(R.TROUGH_COST)
        target_kind = action.payload["target_kind"]
        target_ref = action.payload["target_ref"]
        if target_kind == "pasture":
            fy.build_trough_on_pasture(target_ref)
        elif target_kind == "building":
            fy.build_trough_on_building(tuple(target_ref))
        else:
            fy.build_trough_on_yard(tuple(target_ref))

    elif action.kind == "extension":
        tile_id = action.payload["tile_id"]
        tile = next(t for t in R.EXTENSION_TILES if t["id"] == tile_id)
        player.pay(tile["cost"])
        fy.buy_tile(tile_id, tile["cells"])

    elif action.kind == "special_building":
        name = action.payload["building_name"]
        building = next(b for b in state.available_buildings if b.name == name)
        player.pay(building.cost)
        player.buildings.append(building)
        state.available_buildings.remove(building)
        if building.resource_bonus:
            player.gain(building.resource_bonus)

    else:  # pragma: no cover - garde-fou
        raise ValueError(f"Type d'action inconnu: {action.kind}")

    state.occupied_spaces[action.space_id] = player_idx
