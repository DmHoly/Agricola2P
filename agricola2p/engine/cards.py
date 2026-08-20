"""Cartes bonus (equivalent simplifie des ~40 cartes "ameliorations
mineures / cartes bonus" du jeu reel).

Le jeu original a des dizaines de cartes uniques avec un texte et un effet
tres specifiques que nous ne pouvons pas reproduire fidelement de memoire
(voir README). On utilise ici un pool generique de cartes a effet immediat
(ressources ou points), ce qui garde la mecanique "piocher une carte bonus"
jouable et strategiquement pertinente sans pretendre a l'exactitude du jeu
physique. Remplace facilement `build_deck()` par la vraie liste de cartes
si tu veux plus de fidelite.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .constants import Resource


@dataclass(frozen=True)
class BonusCard:
    name: str
    resource_gain: dict[Resource, int] = field(default_factory=dict)
    points: int = 0
    description: str = ""


def build_deck() -> list[BonusCard]:
    return [
        BonusCard("Bucheron", {Resource.WOOD: 2}, 0, "Gagnez 2 bois."),
        BonusCard("Carriere", {Resource.STONE: 1}, 0, "Gagnez 1 pierre."),
        BonusCard("Argilier", {Resource.CLAY: 2}, 0, "Gagnez 2 argile."),
        BonusCard("Vannier", {Resource.REED: 2}, 0, "Gagnez 2 roseau."),
        BonusCard("Eleveur", {}, 3, "Gagnez 3 points de victoire."),
        BonusCard("Marchand", {Resource.WOOD: 1, Resource.CLAY: 1}, 0, "Gagnez 1 bois et 1 argile."),
        BonusCard("Charpentier", {Resource.WOOD: 3}, 0, "Gagnez 3 bois."),
        BonusCard("Tailleur de pierre", {Resource.STONE: 2}, 0, "Gagnez 2 pierre."),
        BonusCard("Fermier chanceux", {}, 2, "Gagnez 2 points de victoire."),
        BonusCard("Collectionneur", {Resource.WOOD: 1, Resource.REED: 1, Resource.CLAY: 1}, 0,
                   "Gagnez 1 bois, 1 roseau et 1 argile."),
    ]


def shuffled_deck(rng: random.Random) -> list[BonusCard]:
    deck = build_deck()
    rng.shuffle(deck)
    return deck
