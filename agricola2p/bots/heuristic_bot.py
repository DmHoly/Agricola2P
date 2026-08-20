"""Bot glouton: essaie chaque coup legal 1 coup a l'avance et garde celui qui
maximise (mon score - score adverse) apres application, selon le bareme de
score final (agricola2p.engine.game.score_player), plus 2 heuristiques
correctives qui compensent l'horizon 1-coup du glouton pour la reproduction
(cf mecanique dans farmyard.py: `breed()`) et l'accumulation des especes sur
le plateau (cf `rules_data.ANIMAL_ACCUM_SPACES`, le "taux de respawn"):

1. **Anti-gaspillage de reproduction**: a la fin de chaque manche, tout
   groupe d'au moins 2 animaux produit 1 tete gratuite -- MAIS seulement s'il
   reste de la place (`farmyard.breed()`). Un glouton pur 1-coup ne "voit"
   jamais cette perte (poser une auge n'ameliore pas le score immediat tant
   que la capacite n'est pas utilisee), donc il sous-investit en auges. On
   penalise ici tout groupe reproducteur (>=2 animaux) deja a pleine
   capacite: le coup qui laisse ce gaspillage en l'etat est deconseille par
   rapport a celui qui ouvre de la place.
2. **Demarrage precoce de la reproduction**: chaque case d'accumulation
   d'espece a son propre taux de "respawn" (+1/manche si personne ne la
   prend, cf `rules_data.ANIMAL_ACCUM_SPACES`) et ne coute rien a recolter --
   seule la place manque. Faire passer un enclos de <2 a >=2 animaux
   declenche la reproduction gratuite pour TOUTES les manches restantes: un
   glouton 1-coup sous-evalue une petite recolte precoce face a une grosse
   recolte tardive, alors que demarrer tot rapporte une tete gratuite par
   manche restante. On ajoute donc un bonus proportionnel aux manches
   restantes des qu'un coup fait franchir ce seuil pour la 1ere fois.

Ces 2 poids sont des estimations heuristiques (valeur moyenne d'une tete
supplementaire), pas une valeur exacte -- voir STRATEGY.md.
"""

from __future__ import annotations

import copy
import random

from ..engine import rules_data as R
from ..engine.actions import Action
from ..engine.farmyard import Farmyard
from ..engine.game import AgricolaGame, score_player
from .base import Bot

# Valeur moyenne estimee d'une tete de reproduction gratuite (~1 PV de base
# + une fraction de palier). Sert a la fois de bonus (demarrage precoce) et
# de penalite (gaspillage par manque de place).
AVERAGE_HEAD_VALUE = 1.3


def _breeding_groups(fy: Farmyard) -> dict[tuple[str, object], tuple[int, int]]:
    """(kind, ref) -> (count, capacite) pour chaque emplacement occupe."""
    out = {}
    for kind, ref, _species, count in fy.occupied_locations():
        cap = fy.pasture_capacity(fy.pastures[ref]) if kind == "pasture" else fy.cell_capacity(ref)
        out[(kind, ref)] = (count, cap)
    return out


def _breeding_heuristic_bonus(fy_before: Farmyard, fy_after: Farmyard, rounds_remaining: int) -> float:
    after_groups = _breeding_groups(fy_after)
    before_groups = _breeding_groups(fy_before)

    bonus = 0.0

    # 1) anti-gaspillage: groupe reproducteur (>=2) sans place pour la
    #    prochaine reproduction gratuite.
    for (count, cap) in after_groups.values():
        if count >= 2 and count >= cap:
            bonus -= AVERAGE_HEAD_VALUE

    # 2) demarrage precoce: un emplacement qui franchit le seuil de 2
    #    animaux pour la 1ere fois declenche la reproduction gratuite pour
    #    chaque manche restante.
    for key, (count, _cap) in after_groups.items():
        if count < 2:
            continue
        prior_count = before_groups.get(key, (0, 0))[0]
        if prior_count < 2:
            bonus += AVERAGE_HEAD_VALUE * rounds_remaining

    return bonus


class HeuristicBot(Bot):
    name = "heuristic"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        actions = game.legal_actions()
        if len(actions) == 1:
            return actions[0]

        opponent_idx = 1 - player_idx
        rounds_remaining = R.TOTAL_ROUNDS - game.state.round_no + 1
        fy_before = game.state.players[player_idx].farmyard

        best_actions: list[Action] = []
        best_value = float("-inf")

        for action in actions:
            clone = copy.deepcopy(game)
            clone.apply(action)
            fy_after = clone.state.players[player_idx].farmyard
            value = score_player(clone.state.players[player_idx]) - score_player(
                clone.state.players[opponent_idx]
            )
            value += _breeding_heuristic_bonus(fy_before, fy_after, rounds_remaining)
            if value > best_value:
                best_value = value
                best_actions = [action]
            elif value == best_value:
                best_actions.append(action)

        return self.rng.choice(best_actions)
