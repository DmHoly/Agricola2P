"""Toutes les valeurs numeriques et tables de regles, regroupees ici.

IMPORTANT (lire le README, section "Fidelite aux regles officielles"):
Ce fichier suit la synthese fournie par l'utilisateur pour Agricola: Terre
d'Elevage, en particulier la description precise du mecanisme central
(cloture/enclos/batiments):

- Plateau de depart: grille de 6 cases (3x2) = 2 cases maison + 4 cases
  ouvertes. Jusqu'a 2 tuiles d'extension de 3 cases chacune.
- Les barrieres se posent sur les bordures entre 2 cases (ou le bord du
  plateau, gratuit) et se paient en bois OU en pierre. Deux enclos voisins
  mutualisent la barriere qui les separe (payee une seule fois). Les bords
  de la maison et des batiments (stalle/etable) font office de murs
  gratuits: pas besoin de barriere le long de leur cote.
- Une fois posee, une barriere/auge/batiment n'est jamais deplacee.
- Un enclos (pature cloturee) de N cases loge N*2 animaux de base, et ce
  nombre double par auge ajoutee (jusqu'a 3 auges -> N*16).
- Une Stalle (1 case, 3 bois + 1 pierre, 4 animaux, 1 PV) peut etre amelioree
  en Etable (5 bois ou 5 pierre, 5 animaux, 2 PV) ou en Etable ouverte (5
  bois ou 5 pierre, 4 animaux, 2 PV).
- La maison de depart peut etre renovee en Maison a colombage (3 bois + 1
  pierre, 2 PV, pas de capacite animale).
- Score final: +1 PV/animal, bareme par paliers propre a chaque espece
  (malus si <4 animaux), PV des batiments (pool "special" + stalle/etable +
  maison), +4 PV par tuile d'extension entierement amenagee (batiment, auge
  ou pature cloturee sur les 3 cases), regle d'egalite (le 1er joueur de la
  toute premiere manche perd les egalites).

Les valeurs qui ne sont pas donnees dans cette synthese (increments
d'accumulation par tour, forme/emplacement exacts des tuiles d'extension,
liste complete des batiments "speciaux" au-dela de l'exemple de l'Entrepot)
restent des approximations raisonnables. Tout est centralise ici pour rester
facile a corriger: il suffit de changer les valeurs dans ce fichier, aucun
autre module ne contient de nombre "en dur".
"""

from __future__ import annotations

from .constants import Animal, Resource

# ---------------------------------------------------------------------------
# Manches / ouvriers
# ---------------------------------------------------------------------------

TOTAL_ROUNDS = 8
WORKERS_PER_PLAYER = 3

# ---------------------------------------------------------------------------
# Plateau / ferme
# ---------------------------------------------------------------------------
# Grille 4 lignes x 3 colonnes: lignes 0-1 = plateau de depart (3x2 = 6
# cases: 2 maison + 4 ouvertes), lignes 2-3 = jusqu'a 2 tuiles d'extension
# de 3 cases chacune, accolees au plateau principal.

GRID_ROWS = 4
GRID_COLS = 3

INITIAL_HOUSE_CELLS = [(0, 0), (0, 1)]
INITIAL_OPEN_CELLS = [(0, 2), (1, 0), (1, 1), (1, 2)]

# ---------------------------------------------------------------------------
# Tuiles d'extension (max 2, 3 cases chacune)
# ---------------------------------------------------------------------------

EXTENSION_TILES = [
    {"id": "tile_a", "cells": [(2, 0), (2, 1), (2, 2)], "cost": {Resource.WOOD: 3}},
    {"id": "tile_b", "cells": [(3, 0), (3, 1), (3, 2)], "cost": {Resource.STONE: 2, Resource.WOOD: 1}},
]

EXTENSION_COMPLETE_BONUS_PER_TILE = 4

# ---------------------------------------------------------------------------
# Barrieres (mutualisees entre encos voisins ; gratuites le long d'un mur
# naturel: bord du plateau, maison, ou batiment)
# ---------------------------------------------------------------------------

FENCE_COST_PER_EDGE = 1
FENCE_RESOURCE_OPTIONS = [Resource.WOOD, Resource.STONE]

# ---------------------------------------------------------------------------
# Auges
# ---------------------------------------------------------------------------

TROUGH_COST = {Resource.REED: 1}
MAX_TROUGHS_PER_PASTURE = 3
BUILDING_TROUGH_BONUS = 1  # +1 animal si le batiment (stalle/etable) a une auge
YARD_TROUGH_CAPACITY = 1  # case non cloturee equipee d'une auge


def pasture_capacity(size: int, troughs: int) -> int:
    """N cases * 2 animaux de base, double par auge (jusqu'a 3 auges)."""
    return size * 2 * (2 ** troughs)


# ---------------------------------------------------------------------------
# Batiments sur case (Stalle -> Etable / Etable ouverte)
# ---------------------------------------------------------------------------

STALLE_COST = {Resource.WOOD: 3, Resource.STONE: 1}

BUILDING_LEVELS = {
    "stalle": {"capacity": 4, "points": 1},
    "etable": {"capacity": 5, "points": 2},
    "etable_ouverte": {"capacity": 4, "points": 2},
}

# Amelioration Stalle -> Etable/Etable ouverte: 5 bois OU 5 pierre au choix.
BUILDING_UPGRADE_COST_OPTIONS = [{Resource.WOOD: 5}, {Resource.STONE: 5}]
BUILDING_UPGRADE_TARGETS = ["etable", "etable_ouverte"]

# ---------------------------------------------------------------------------
# Renovation de la maison (Maison a colombage)
# ---------------------------------------------------------------------------

HOUSE_UPGRADE_COST = {Resource.WOOD: 3, Resource.STONE: 1}
HOUSE_UPGRADE_POINTS = 2

# ---------------------------------------------------------------------------
# Accumulation sur le plateau central
# ---------------------------------------------------------------------------
# space_id -> ("resource"|"animal", Resource|Animal, increment ajoute a
# chaque debut de tour si l'espace n'a pas ete pris)

ACCUMULATING_SPACES: dict[str, tuple[str, object, int]] = {
    "wood_space": ("resource", Resource.WOOD, 3),
    "stone_space": ("resource", Resource.STONE, 1),
    "reed_space": ("resource", Resource.REED, 2),
    "sheep_source": ("animal", Animal.SHEEP, 2),
    "boar_source": ("animal", Animal.BOAR, 1),
    "cattle_source": ("animal", Animal.CATTLE, 1),
    "horse_source": ("animal", Animal.HORSE, 1),
}

# ---------------------------------------------------------------------------
# Espaces d'action (tous disponibles des le tour 1)
# kind in {"resource_accum", "animal_accum", "fence", "building",
#          "upgrade_building", "upgrade_house", "trough", "extension",
#          "special_building"}
# ---------------------------------------------------------------------------

ACTION_SPACE_KIND: dict[str, str] = {
    "wood_space": "resource_accum",
    "stone_space": "resource_accum",
    "reed_space": "resource_accum",
    "sheep_source": "animal_accum",
    "boar_source": "animal_accum",
    "cattle_source": "animal_accum",
    "horse_source": "animal_accum",
    "fencing": "fence",
    "build_building": "building",
    "upgrade_building": "upgrade_building",
    "upgrade_house": "upgrade_house",
    "build_trough": "trough",
    "extension": "extension",
    "special_building": "special_building",
}

ALL_ACTION_SPACES = list(ACTION_SPACE_KIND.keys())

# ---------------------------------------------------------------------------
# Batiments speciaux (pool partage, achete puis retire du pool ; distincts
# des batiments sur case Stalle/Etable ci-dessus)
# ---------------------------------------------------------------------------
# per_leftover_resource: PV supplementaires par unite de ressource restante
# en reserve en fin de partie (ex. l'Entrepot: "+0.5 PV par materiau restant").

SPECIAL_BUILDINGS = [
    {"name": "Bergerie", "cost": {Resource.WOOD: 2}, "points": 2, "resource_bonus": {}, "per_leftover_resource": 0.0},
    {"name": "Porcherie", "cost": {Resource.WOOD: 2, Resource.REED: 1}, "points": 2, "resource_bonus": {}, "per_leftover_resource": 0.0},
    {"name": "Puits", "cost": {Resource.REED: 2}, "points": 2, "resource_bonus": {Resource.REED: 1}, "per_leftover_resource": 0.0},
    {"name": "Carriere privee", "cost": {Resource.STONE: 2}, "points": 3, "resource_bonus": {Resource.STONE: 1}, "per_leftover_resource": 0.0},
    {"name": "Entrepot", "cost": {Resource.WOOD: 2, Resource.STONE: 2}, "points": 0, "resource_bonus": {}, "per_leftover_resource": 0.5},
]

# ---------------------------------------------------------------------------
# Score final
# ---------------------------------------------------------------------------

BASE_POINTS_PER_ANIMAL = 1

# Bareme par paliers, propre a chaque espece: liste de (seuil_min, points)
# triee par seuil croissant. Le palier applique est le plus grand seuil
# atteint par le nombre d'animaux possede. 0 a 3 animaux -> toujours -3.
ANIMAL_SCORE_BRACKETS: dict[Animal, list[tuple[int, int]]] = {
    Animal.SHEEP: [
        (0, -3), (4, 0), (8, 1), (11, 2), (13, 3), (14, 4),
        (15, 5), (16, 6), (17, 7), (18, 8), (19, 9),
    ],
    Animal.BOAR: [
        (0, -3), (4, 0), (7, 1), (9, 2), (11, 3), (12, 4),
        (13, 5), (14, 6), (15, 7), (16, 8), (17, 9),
    ],
    Animal.CATTLE: [
        (0, -3), (4, 0), (6, 1), (8, 2), (10, 3), (11, 4),
        (12, 5), (13, 6), (14, 7), (15, 8), (16, 9),
    ],
    Animal.HORSE: [
        (0, -3), (4, 0), (5, 1), (7, 2), (9, 3), (10, 4),
        (11, 5), (12, 6), (13, 7), (14, 8), (15, 9),
    ],
}


def species_points(species: Animal, count: int) -> int:
    brackets = ANIMAL_SCORE_BRACKETS[species]
    points = brackets[0][1]
    for threshold, pts in brackets:
        if count >= threshold:
            points = pts
        else:
            break
    return points
