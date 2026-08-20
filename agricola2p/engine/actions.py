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


def _fence_actions(space_id: str, cost_fn, resource: Resource, player: PlayerState) -> list[Action]:
    fy = player.farmyard
    actions: list[Action] = []
    for r1 in range(fy.rows):
        for r2 in range(r1, fy.rows):
            for c1 in range(fy.cols):
                for c2 in range(c1, fy.cols):
                    if not fy.can_build_pasture(r1, c1, r2, c2):
                        continue
                    edges = fy.fence_cost_for_rectangle(r1, c1, r2, c2)
                    if edges <= 0:
                        continue
                    cost = cost_fn(edges)
                    if player.resources.get(resource, 0) >= cost:
                        actions.append(Action(space_id, "fence", {"rect": (r1, c1, r2, c2), "resource": resource.value}))
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


def _trough_targets(fy) -> list[tuple[str, Any]]:
    """Emplacements ou une auge peut etre posee: (target_kind, target_ref).

    "terrain" = n'importe quelle case de terrain libre OU faisant partie
    d'un enclos (max 1 auge/case) ; "building" = une Stalle/Etable sans
    auge (mecanique separee, +1 capacite fixe).
    """
    targets: list[tuple[str, Any]] = []
    for cell in fy.playable_cells():
        if fy.can_place_trough_on_terrain(cell):
            targets.append(("terrain", cell))
    for cell in fy.building_cells:
        if fy.can_build_trough_on_building(cell):
            targets.append(("building", cell))
    return targets


def _trough_actions(space_id: str, cost_fn, resource: Resource, player: PlayerState) -> list[Action]:
    """Une seule visite peut poser plusieurs auges (illimite): on propose soit
    UNE auge sur un emplacement precis, soit TOUTES les auges possibles en une
    fois (plutot que d'enumerer tous les sous-ensembles, pour rester borne).
    """
    fy = player.farmyard
    targets = _trough_targets(fy)
    out = []
    for target_kind, target_ref in targets:
        cost = cost_fn(1)
        if player.resources.get(resource, 0) >= cost:
            out.append(Action(space_id, "trough", {"targets": [[target_kind, target_ref]]}))
    if len(targets) > 1:
        cost_all = cost_fn(len(targets))
        if player.resources.get(resource, 0) >= cost_all:
            out.append(Action(space_id, "trough", {"targets": [list(t) for t in targets]}))
    return out


def _animal_accum_actions(space_id: str, state: GameState, player: PlayerState) -> list[Action]:
    (species,) = R.ANIMAL_ACCUM_SPACES[space_id].keys()
    if state.accumulators.get(space_id, {}).get(species, 0) <= 0:
        return []
    fy = player.farmyard
    out = []
    for kind, ref, sp, free in fy.available_capacity():
        if sp != species or free <= 0:
            continue
        out.append(Action(space_id, "animal_accum", {"species": species, "target_kind": kind, "target_ref": ref}))
    return out


def _extension_dedicated_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    if not player.can_afford(R.EXTENSION_DEDICATED_COST):
        return []
    return [
        Action("extension_dedicated", "extension_dedicated", {"tile_id": tile["id"]})
        for tile in R.EXTENSION_TILES
        if tile["id"] not in fy.owned_tiles
    ]


def _extension_or_upgrade_actions(player: PlayerState) -> list[Action]:
    fy = player.farmyard
    out = []
    for cost in R.EXTENSION_OR_UPGRADE_COST_OPTIONS:
        if not player.can_afford(cost):
            continue
        cost_payload = {r.value: v for r, v in cost.items()}
        for tile in R.EXTENSION_TILES:
            if tile["id"] not in fy.owned_tiles:
                out.append(
                    Action(
                        "extension_or_upgrade",
                        "extension_or_upgrade",
                        {"effect": "tile", "tile_id": tile["id"], "cost": cost_payload},
                    )
                )
        for cell in fy.building_cells:
            if not fy.can_upgrade_building(cell):
                continue
            for new_level in R.BUILDING_UPGRADE_TARGETS:
                out.append(
                    Action(
                        "extension_or_upgrade",
                        "extension_or_upgrade",
                        {"effect": "building", "cell": cell, "new_level": new_level, "cost": cost_payload},
                    )
                )
        if fy.can_upgrade_house():
            out.append(
                Action("extension_or_upgrade", "extension_or_upgrade", {"effect": "house", "cost": cost_payload})
            )
    return out


def _special_building_actions(space_id: str, state: GameState, player: PlayerState) -> list[Action]:
    out = []
    for building in state.available_buildings:
        if player.can_afford(building.cost):
            out.append(Action(space_id, "special_building", {"building_name": building.name}))
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
            if any(v > 0 for v in state.accumulators.get(space_id, {}).values()):
                out.append(Action(space_id, kind, {}))
        elif kind == "animal_accum":
            out.extend(_animal_accum_actions(space_id, state, player))
        elif kind == "fence_standard":
            out.extend(_fence_actions(space_id, R.fence_standard_cost, R.FENCE_STANDARD_RESOURCE, player))
        elif kind == "fence_alt":
            out.extend(_fence_actions(space_id, R.fence_alt_cost, R.FENCE_ALT_RESOURCE, player))
        elif kind == "building":
            out.extend(_building_actions(player))
        elif kind == "trough_standard":
            out.extend(_trough_actions(space_id, R.trough_standard_cost, R.TROUGH_STANDARD_RESOURCE, player))
        elif kind == "trough_alt":
            out.extend(_trough_actions(space_id, R.trough_alt_cost, R.TROUGH_ALT_RESOURCE, player))
        elif kind == "extension_dedicated":
            out.extend(_extension_dedicated_actions(player))
        elif kind == "extension_or_upgrade":
            out.extend(_extension_or_upgrade_actions(player))
        elif kind == "special_building":
            out.extend(_special_building_actions(space_id, state, player))
    out.extend(_reorganize_actions(state, player))
    if not out:
        out.append(PASS)
    return out


def _apply_trough_targets(fy, targets: list[list]) -> None:
    for target_kind, target_ref in targets:
        if target_kind == "building":
            fy.build_trough_on_building(tuple(target_ref))
        else:
            fy.build_trough_on_terrain(tuple(target_ref))


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
        gained = state.accumulators.get(action.space_id, {})
        player.gain(gained)
        state.accumulators[action.space_id] = dict.fromkeys(gained, 0)
        if action.space_id == R.FIRST_PLAYER_SPACE:
            state.next_starting_player_idx = player_idx

    elif action.kind == "animal_accum":
        species = Animal(action.payload["species"])
        target_kind = action.payload["target_kind"]
        target_ref = action.payload["target_ref"]
        available = state.accumulators.get(action.space_id, {}).get(species, 0)
        if target_kind == "pasture":
            taken = fy.add_animals_to_pasture(target_ref, species, available)
        else:
            taken = fy.add_animals_to_cell(tuple(target_ref), species, available)
        state.accumulators[action.space_id][species] = max(0, available - taken)

    elif action.kind == "fence":
        r1, c1, r2, c2 = action.payload["rect"]
        resource = Resource(action.payload["resource"])
        edges = fy.fence_cost_for_rectangle(r1, c1, r2, c2)
        cost_fn = R.fence_standard_cost if action.space_id == "fencing_standard" else R.fence_alt_cost
        player.pay({resource: cost_fn(edges)})
        fy.build_pasture(r1, c1, r2, c2)

    elif action.kind == "building":
        player.pay(R.STALLE_COST)
        fy.build_building(tuple(action.payload["cell"]))

    elif action.kind == "trough":
        targets = action.payload["targets"]
        cost_fn = R.trough_standard_cost if action.space_id == "build_trough" else R.trough_alt_cost
        resource = R.TROUGH_STANDARD_RESOURCE if action.space_id == "build_trough" else R.TROUGH_ALT_RESOURCE
        player.pay({resource: cost_fn(len(targets))})
        _apply_trough_targets(fy, targets)

    elif action.kind == "extension_dedicated":
        tile_id = action.payload["tile_id"]
        tile = next(t for t in R.EXTENSION_TILES if t["id"] == tile_id)
        player.pay(R.EXTENSION_DEDICATED_COST)
        fy.buy_tile(tile_id, tile["cells"])

    elif action.kind == "extension_or_upgrade":
        cost = {Resource(r): v for r, v in action.payload["cost"].items()}
        player.pay(cost)
        effect = action.payload["effect"]
        if effect == "tile":
            tile_id = action.payload["tile_id"]
            tile = next(t for t in R.EXTENSION_TILES if t["id"] == tile_id)
            fy.buy_tile(tile_id, tile["cells"])
        elif effect == "building":
            fy.upgrade_building(tuple(action.payload["cell"]), action.payload["new_level"])
        elif effect == "house":
            fy.upgrade_house()

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
