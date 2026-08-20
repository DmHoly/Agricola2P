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
- Les animaux peuvent etre redeplaces librement entre emplacements deja
  construits (mais 1 seule espece par emplacement); les enclos/barrieres/
  batiments, eux, restent fixes une fois poses.
- Plateau d'action precis (liste fournie par l'utilisateur): chaque case
  n'accueille qu'1 seul ouvrier ("capacite_ouvriers_max": 1 partout);
  Petit/Grand Bois, Petite/Grande Pierre, Roseau&Bois, et 1 case par espece
  animale pour l'accumulation; les clotures et les auges ont chacune 2 cases
  distinctes (une "standard" au cout en bois, une "alternative" au cout en
  pierre, un peu plus cher) -- si la standard est prise, l'autre joueur peut
  toujours agir via l'alternative; l'agrandissement de ferme a sa propre
  case dediee (3 pierre + 1 roseau) en plus d'une case combinee
  agrandissement-OU-amelioration (5 bois ou 5 pierre); et il y a 2 cases
  independantes pour acheter un batiment special (jusqu'a 2 par manche).

Les valeurs qui ne sont pas donnees dans cette synthese (liste complete des
batiments "speciaux" au-dela de l'exemple de l'Entrepot, cout de
construction initial d'une Stalle -- absent de la liste d'actions fournie,
conserve tel quel car le jeu a besoin d'un moyen de batir une premiere
Stalle avant de pouvoir la remplacer) restent des approximations
raisonnables. Tout est centralise ici pour rester facile a corriger: il
suffit de changer les valeurs dans ce fichier, aucun autre module ne
contient de nombre "en dur".
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
# Tuiles d'extension (max 2, 3 cases chacune). Le cout est celui de la case
# d'action utilisee pour les acheter (cf EXTENSION_DEDICATED_COST /
# EXTENSION_OR_UPGRADE_COST_OPTIONS ci-dessous), pas un cout par tuile.
# ---------------------------------------------------------------------------

EXTENSION_TILES = [
    {"id": "tile_a", "cells": [(2, 0), (2, 1), (2, 2)]},
    {"id": "tile_b", "cells": [(3, 0), (3, 1), (3, 2)]},
]

EXTENSION_COMPLETE_BONUS_PER_TILE = 4

# ---------------------------------------------------------------------------
# Barrieres: 2 cases distinctes (standard bois, alternative pierre plus
# chere) ; mutualisees entre enclos voisins et gratuites le long d'un mur
# naturel (bord du plateau, maison, batiment) -- cf farmyard.py.
# ---------------------------------------------------------------------------

FENCE_STANDARD_RESOURCE = Resource.WOOD
FENCE_ALT_RESOURCE = Resource.STONE


def fence_standard_cost(n: int) -> int:
    """1 bois par barriere, illimite."""
    return max(0, n)


def fence_alt_cost(n: int) -> int:
    """2 pierres pour les 2 premieres barrieres, puis 1 pierre chacune."""
    if n <= 0:
        return 0
    return 2 + max(0, n - 2)


# ---------------------------------------------------------------------------
# Auges: 2 cases distinctes (standard: 1re gratuite puis 3 bois/auge ;
# alternative: 3 pierre/auge, jamais de gratuite). Une case peut en poser
# plusieurs en une seule visite.
# ---------------------------------------------------------------------------

TROUGH_STANDARD_RESOURCE = Resource.WOOD
TROUGH_STANDARD_EXTRA_COST = 3  # par auge au-dela de la 1ere (gratuite)
TROUGH_ALT_RESOURCE = Resource.STONE
TROUGH_ALT_COST = 3  # par auge, des la 1ere

MAX_TROUGHS_PER_PASTURE = 3
BUILDING_TROUGH_BONUS = 1  # +1 animal si le batiment (stalle/etable) a une auge
YARD_TROUGH_CAPACITY = 1  # case non cloturee equipee d'une auge


def trough_standard_cost(k: int) -> int:
    return 0 if k <= 0 else TROUGH_STANDARD_EXTRA_COST * (k - 1)


def trough_alt_cost(k: int) -> int:
    return TROUGH_ALT_COST * max(0, k)


def pasture_capacity(size: int, troughs: int) -> int:
    """N cases * 2 animaux de base, double par auge (jusqu'a 3 auges)."""
    return size * 2 * (2 ** troughs)


# ---------------------------------------------------------------------------
# Batiments sur case (Stalle -> Etable / Etable ouverte)
# ---------------------------------------------------------------------------
# NB: la construction initiale d'une Stalle n'apparait pas dans la liste
# d'actions fournie par l'utilisateur ; conservee telle quelle (cf note en
# tete de fichier) puisqu'il faut bien un moyen d'en batir une premiere.

STALLE_COST = {Resource.WOOD: 3, Resource.STONE: 1}

BUILDING_LEVELS = {
    "stalle": {"capacity": 4, "points": 1},
    "etable": {"capacity": 5, "points": 2},
    "etable_ouverte": {"capacity": 4, "points": 2},
}

BUILDING_UPGRADE_TARGETS = ["etable", "etable_ouverte"]

# ---------------------------------------------------------------------------
# Case "Agrandissement de ferme" (dediee) et case "Agrandissement OU
# amelioration" (tuile d'extension, ou remplacement Stalle->Etable/Etable
# ouverte, ou renovation de la maison en Maison a colombage -- au choix).
# ---------------------------------------------------------------------------

EXTENSION_DEDICATED_COST = {Resource.STONE: 3, Resource.REED: 1}
EXTENSION_OR_UPGRADE_COST_OPTIONS = [{Resource.WOOD: 5}, {Resource.STONE: 5}]

# ---------------------------------------------------------------------------
# Renovation de la maison (Maison a colombage) -- meme cout que la case
# "agrandissement ou amelioration" ci-dessus, cf EXTENSION_OR_UPGRADE_COST_OPTIONS.
# ---------------------------------------------------------------------------

HOUSE_UPGRADE_POINTS = 2

# ---------------------------------------------------------------------------
# Accumulation sur le plateau central
# ---------------------------------------------------------------------------
# space_id -> increments ajoutes a chaque debut de tour si l'espace n'a pas
# ete pris (dict de Resource->montant pour les cases ressource, dict a 1 cle
# Animal->montant pour les cases animal ; "Roseau & Bois" cumule 2
# ressources a la fois).

RESOURCE_ACCUM_SPACES: dict[str, dict[Resource, int]] = {
    "wood_small": {Resource.WOOD: 1},
    "wood_large": {Resource.WOOD: 2},
    "stone_small": {Resource.STONE: 1},
    "stone_large": {Resource.STONE: 2},
    "reed_wood_space": {Resource.REED: 1, Resource.WOOD: 1},
}

ANIMAL_ACCUM_SPACES: dict[str, dict[Animal, int]] = {
    "sheep_source": {Animal.SHEEP: 1},
    "boar_source": {Animal.BOAR: 1},
    "cattle_source": {Animal.CATTLE: 1},
    "horse_source": {Animal.HORSE: 1},
}

ACCUM_SPACES: dict[str, dict] = {**RESOURCE_ACCUM_SPACES, **ANIMAL_ACCUM_SPACES}

# ---------------------------------------------------------------------------
# Espaces d'action (tous disponibles des le tour 1 ; 1 seul ouvrier par
# case -- cf state.is_space_free)
# kind in {"resource_accum", "animal_accum", "fence_standard", "fence_alt",
#          "building", "trough_standard", "trough_alt",
#          "extension_dedicated", "extension_or_upgrade", "special_building"}
# "extension_or_upgrade" offre 3 effets au choix: acheter une tuile,
# ameliorer une Stalle (-> Etable/Etable ouverte), ou renover la maison.
# ---------------------------------------------------------------------------

ACTION_SPACE_KIND: dict[str, str] = {
    "wood_small": "resource_accum",
    "wood_large": "resource_accum",
    "stone_small": "resource_accum",
    "stone_large": "resource_accum",
    "reed_wood_space": "resource_accum",
    "sheep_source": "animal_accum",
    "boar_source": "animal_accum",
    "cattle_source": "animal_accum",
    "horse_source": "animal_accum",
    "fencing_standard": "fence_standard",
    "fencing_alt": "fence_alt",
    "build_building": "building",
    "build_trough": "trough_standard",
    "build_trough_alt": "trough_alt",
    "extension_dedicated": "extension_dedicated",
    "extension_or_upgrade": "extension_or_upgrade",
    "special_building_1": "special_building",
    "special_building_2": "special_building",
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
