"""Types de base partages par tout le moteur."""

from __future__ import annotations

from enum import Enum


class Resource(str, Enum):
    WOOD = "wood"
    STONE = "stone"
    REED = "reed"


class Animal(str, Enum):
    SHEEP = "sheep"
    BOAR = "boar"
    CATTLE = "cattle"
    HORSE = "horse"


RESOURCES = list(Resource)
ANIMALS = list(Animal)
