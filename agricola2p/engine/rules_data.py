"""Toutes les valeurs numeriques et tables de regles, regroupees ici.

IMPORTANT (lire le README, section "Fidelite aux regles officielles"):
La structure ci-dessous suit la synthese fournie par l'utilisateur (basee sur
la video de la chaine Ludovox presentant Agricola: Terre d'Elevage): partie
en 8 tours, 3 ouvriers par joueur (6 actions/tour), ressources bois/pierre/
roseau qui s'accumulent sur le plateau central, 4 especes (mouton, cochon,
vache, cheval), clotures/enclos immuables une fois poses, tuiles d'extension
pour agrandir la ferme, batiments speciaux (points + capacites), penalite de
diversite si moins de 3 animaux d'une espece, bonus "exploitation complete".

Les valeurs numeriques precises non donnees dans cette synthese (couts
exacts, incrementations d'accumulation, forme/emplacement des tuiles
d'extension, liste des batiments speciaux) restent des approximations
raisonnables choisies pour donner un jeu jouable et equilibre. Tout est
centralise ici pour rester facile a corriger si une source plus precise
(livret officiel) devient disponible: il suffit de changer les valeurs dans
ce fichier, aucun autre module ne contient de nombre "en dur".
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

GRID_ROWS = 4
GRID_COLS = 4

INITIAL_HOUSE_CELLS = [(0, 0), (0, 1)]
# Cases jouables des le debut de la partie (en plus de la maison).
INITIAL_OPEN_CELLS = [(0, 2), (0, 3), (1, 0), (1, 1)]

# ---------------------------------------------------------------------------
# Tuiles d'extension (agrandissement de la ferme)
# ---------------------------------------------------------------------------

EXTENSION_TILES = [
    {"id": "tile_a", "cells": [(1, 2), (1, 3)], "cost": {Resource.WOOD: 2}},
    {"id": "tile_b", "cells": [(2, 0), (2, 1)], "cost": {Resource.WOOD: 2, Resource.REED: 1}},
    {"id": "tile_c", "cells": [(2, 2), (2, 3)], "cost": {Resource.STONE: 1, Resource.WOOD: 1}},
    {"id": "tile_d", "cells": [(3, 0), (3, 1)], "cost": {Resource.STONE: 2}},
    {"id": "tile_e", "cells": [(3, 2), (3, 3)], "cost": {Resource.STONE: 2, Resource.REED: 1}},
]

EXTENSION_COMPLETE_BONUS_PER_TILE = 2

# ---------------------------------------------------------------------------
# Clotures / etables
# ---------------------------------------------------------------------------

FENCE_COST_PER_EDGE = {Resource.WOOD: 1}
STABLE_COST = {Resource.WOOD: 2}

# Une etable (batiment qui "abrite des animaux") loge jusqu'a ce nombre
# d'animaux d'une meme espece sur sa case.
STABLE_CAPACITY = 2

# Un enclos (pature) sans etable loge 1 animal par case cloturee; chaque
# etable construite a l'interieur ajoute STABLE_CAPACITY-1 places
# supplementaires par etable (cf farmyard.Pasture.capacity).
MAX_ANIMALS_UNFENCED_NO_STABLE = 1

# ---------------------------------------------------------------------------
# Accumulation sur le plateau central
# ---------------------------------------------------------------------------
# space_id -> ("resource"|"animal", Resource|Animal, increment ajoute a
# chaque debut de tour si l'espace n'a pas ete pris)

ACCUMULATING_SPACES: dict[str, tuple[str, object, int]] = {
    "wood_space": ("resource", Resource.WOOD, 3),
    "stone_space": ("resource", Resource.STONE, 1),
    "reed_space": ("resource", Resource.REED, 2),
    "sheep_source": ("animal", Animal.SHEEP, 1),
    "boar_source": ("animal", Animal.BOAR, 1),
    "cattle_source": ("animal", Animal.CATTLE, 1),
    "horse_source": ("animal", Animal.HORSE, 1),
}

# ---------------------------------------------------------------------------
# Espaces d'action (tous disponibles des le tour 1)
# kind in {"resource_accum", "animal_accum", "fence", "stable", "extension",
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
    "build_stable": "stable",
    "extension": "extension",
    "special_building": "special_building",
}

ALL_ACTION_SPACES = list(ACTION_SPACE_KIND.keys())

# ---------------------------------------------------------------------------
# Batiments speciaux (pool partage, achete puis retire du pool)
# ---------------------------------------------------------------------------

SPECIAL_BUILDINGS = [
    {"name": "Bergerie", "cost": {Resource.WOOD: 2}, "points": 2, "resource_bonus": {}},
    {"name": "Porcherie", "cost": {Resource.WOOD: 2, Resource.REED: 1}, "points": 2, "resource_bonus": {}},
    {"name": "Etable a vaches", "cost": {Resource.STONE: 1, Resource.WOOD: 1}, "points": 3, "resource_bonus": {}},
    {"name": "Ecurie", "cost": {Resource.STONE: 1, Resource.REED: 1}, "points": 3, "resource_bonus": {}},
    {"name": "Grange", "cost": {Resource.WOOD: 3}, "points": 2, "resource_bonus": {Resource.WOOD: 1}},
    {"name": "Puits", "cost": {Resource.REED: 2}, "points": 2, "resource_bonus": {Resource.REED: 1}},
    {"name": "Carriere privee", "cost": {Resource.STONE: 2}, "points": 3, "resource_bonus": {Resource.STONE: 1}},
]

# ---------------------------------------------------------------------------
# Score final
# ---------------------------------------------------------------------------

# Meme bareme pour les 4 especes (index = nombre d'animaux, cappe au dernier
# indice). Moins de 3 animaux d'une espece penalise (valeurs <= -1), 3+
# rapporte des points croissants ("palier").
ANIMAL_SCORE_TABLE = [-2, -1, -1, 2, 3, 4, 5]
ANIMAL_DIVERSITY_THRESHOLD = 3
