"""Bot glouton 1-coup, comme HeuristicBot, mais qui evalue chaque etat
resultant avec un reseau de valeur appris par self-play
(agricola2p.rl.value_net.ValueNet) au lieu du bareme de score final exact.

Necessite numpy et des poids entraines (`python3 -m agricola2p.rl.train`,
cf agricola2p/rl/weights.npz). Si aucun poids n'est fourni/trouve, leve une
erreur explicite plutot que de jouer avec un reseau non entraine.
"""

from __future__ import annotations

import copy
import random
from pathlib import Path

from ..engine.actions import Action
from ..engine.game import AgricolaGame
from .base import Bot


class RLBot(Bot):
    name = "rl"

    def __init__(self, weights_path=None, seed: int | None = None, net=None):
        """`net`: instance ValueNet deja chargee, a reutiliser telle quelle
        (evite de relire le fichier de poids a chaque partie -- utile pour
        generer des milliers de parties de self-play). Prioritaire sur
        `weights_path` si fourni."""
        try:
            from ..rl.features import encode
            from ..rl.value_net import DEFAULT_WEIGHTS_PATH, ValueNet
        except ImportError as exc:  # pragma: no cover - depend de l'environnement
            raise ImportError(
                "RLBot necessite numpy (pip install numpy, ou l'extra "
                "'rl': pip install -e '.[rl]')."
            ) from exc

        self._encode = encode
        if net is not None:
            self.net = net
        else:
            path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
            if not path.exists():
                raise FileNotFoundError(
                    f"Aucun poids entraine trouve ({path}). Lance d'abord: "
                    "python3 -m agricola2p.rl.train"
                )
            self.net = ValueNet.load(path)
        self.rng = random.Random(seed)

    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        actions = game.legal_actions()
        if len(actions) == 1:
            return actions[0]

        best_actions: list[Action] = []
        best_value = float("-inf")

        for action in actions:
            clone = copy.deepcopy(game)
            clone.apply(action)
            features = self._encode(clone.state, player_idx)
            value = self.net.predict(features)
            if value > best_value:
                best_value = value
                best_actions = [action]
            elif value == best_value:
                best_actions.append(action)

        return self.rng.choice(best_actions)
