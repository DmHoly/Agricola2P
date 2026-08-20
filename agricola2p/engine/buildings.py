"""Batiments speciaux: pool partage, achete via l'espace d'action
"special_building" puis retire du pool (chaque batiment est unique).

Comme pour les cartes bonus de la version precedente, le jeu reel a
vraisemblablement des batiments avec des textes/capacites tres varies que
nous ne pouvons pas reproduire fidelement de memoire. On utilise un pool
generique: cout en ressources, points de victoire directs, et un "bonus
ressource" immediat en guise de capacite speciale simplifiee.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import rules_data as R
from .constants import Resource


@dataclass(frozen=True)
class SpecialBuilding:
    name: str
    cost: dict[Resource, int] = field(default_factory=dict)
    points: int = 0
    resource_bonus: dict[Resource, int] = field(default_factory=dict)


def build_pool() -> list[SpecialBuilding]:
    return [
        SpecialBuilding(b["name"], b["cost"], b["points"], b["resource_bonus"])
        for b in R.SPECIAL_BUILDINGS
    ]


def shuffled_pool(rng: random.Random) -> list[SpecialBuilding]:
    pool = build_pool()
    rng.shuffle(pool)
    return pool
