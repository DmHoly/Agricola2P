"""Petit adaptateur: transforme un ValueNet entraine en fonction
`value_fn(state, player_idx) -> float` directement utilisable par
`agricola2p.bots.mcts_bot.MCTSBot(value_fn=...)` comme evaluateur de feuille
(bootstrap au lieu de simuler jusqu'a la fin de la partie).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..engine.state import GameState
from .features import encode
from .value_net import DEFAULT_WEIGHTS_PATH, ValueNet


def load_value_fn(weights_path: Path | str = DEFAULT_WEIGHTS_PATH) -> Callable[[GameState, int], float]:
    net = ValueNet.load(weights_path)

    def value_fn(state: GameState, player_idx: int) -> float:
        return float(net.predict(encode(state, player_idx)))

    return value_fn
