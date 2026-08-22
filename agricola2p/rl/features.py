"""Encodage d'un GameState (point de vue d'un joueur) en vecteur numpy de
taille fixe, pour le reseau de valeur.

Principe: plutot que de faire tout redecouvrir au reseau depuis zero, on lui
donne a la fois le score final actuel (`score_player`, deja tres informatif)
ET les ingredients bruts qui annoncent une croissance future non encore
capturee par ce score (capacite d'enclos non utilisee, ressources/animaux
accumules sur le plateau mais pas encore recoltes...). Le reseau n'a plus
qu'a apprendre l'ecart entre "score actuel" et "score final probable".
"""

from __future__ import annotations

import numpy as np

from ..engine import rules_data as R
from ..engine.constants import Animal, Resource
from ..engine.game import score_player
from ..engine.state import GameState, PlayerState

# Ordre stable des cles d'accumulateurs (utilise a l'encodage).
_ACCUM_SPACE_IDS = list(R.ACCUM_SPACES.keys())


def _player_features(player: PlayerState) -> list[float]:
    fy = player.farmyard

    feats: list[float] = [float(player.resources.get(r, 0)) for r in Resource]

    animals = fy.total_animals()
    feats += [float(animals[a]) for a in Animal]
    feats.append(float(sum(animals.values())))

    total_cap = sum(fy.pasture_capacity(p) for p in fy.pastures.values())
    total_count = sum(p.count for p in fy.pastures.values())
    feats += [float(len(fy.pastures)), float(total_cap), float(total_count), float(total_cap - total_count)]

    feats.append(float(len(fy.building_cells)))
    feats.append(float(sum(b.capacity() for b in fy.building_cells.values())))
    feats.append(float(sum(b.points() for b in fy.building_cells.values())))

    feats.append(1.0 if fy.house_upgraded else 0.0)

    feats.append(float(len(fy.owned_tiles)))
    fully_used = sum(
        1 for t in R.EXTENSION_TILES if t["id"] in fy.owned_tiles and fy.tile_fully_used(t["cells"])
    )
    feats.append(float(fully_used))

    feats.append(float(len(player.buildings)))
    feats.append(float(sum(b.points for b in player.buildings)))
    feats.append(1.0 if any(b.per_leftover_resource > 0 for b in player.buildings) else 0.0)

    feats.append(float(len(fy.free_cells())))
    feats.append(float(score_player(player)))

    return feats


def encode(state: GameState, player_idx: int) -> np.ndarray:
    """Vecteur de features du point de vue de `player_idx` (adversaire inclus)."""
    me = state.players[player_idx]
    opponent = state.players[1 - player_idx]

    feats: list[float] = [
        state.round_no / R.TOTAL_ROUNDS,
        (R.TOTAL_ROUNDS - state.round_no + 1) / R.TOTAL_ROUNDS,
        state.turn_index / max(1, len(state.turn_order)),
    ]

    for space_id in _ACCUM_SPACE_IDS:
        bucket = state.accumulators.get(space_id, {})
        feats.append(float(sum(bucket.values())))

    feats += _player_features(me)
    feats += _player_features(opponent)

    return np.asarray(feats, dtype=np.float64)


FEATURE_DIM = len(encode(GameState.new_game(seed=0), 0))
