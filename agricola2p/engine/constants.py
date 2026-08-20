"""Types de base partages par tout le moteur."""

from __future__ import annotations

from enum import Enum


class Resource(str, Enum):
    WOOD = "wood"
    CLAY = "clay"
    REED = "reed"
    STONE = "stone"


class Animal(str, Enum):
    RABBIT = "rabbit"
    SHEEP = "sheep"
    BOAR = "boar"
    CATTLE = "cattle"


class HouseMaterial(str, Enum):
    WOOD = "wood"
    CLAY = "clay"
    STONE = "stone"

    @property
    def next(self) -> "HouseMaterial | None":
        order = [HouseMaterial.WOOD, HouseMaterial.CLAY, HouseMaterial.STONE]
        idx = order.index(self)
        return order[idx + 1] if idx + 1 < len(order) else None


class SpaceKind(str, Enum):
    EMPTY = "empty"
    HOUSE = "house"


RESOURCES = list(Resource)
ANIMALS = list(Animal)
