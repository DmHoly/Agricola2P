"""Toutes les valeurs numeriques et tables de regles, regroupees ici.

IMPORTANT (lire le README, section "Fidelite aux regles officielles"):
Ce module reconstitue de memoire les regles d'Agricola: Terre d'Elevage
(All Creatures Big and Small, Uwe Rosenberg). La structure du jeu (pas de
recoltes/faim, 1 seul ouvrier par joueur, 14 manches en 4 stades, especes
animales, ressources bois/argile/roseau/pierre) est fidele. En revanche les
valeurs numeriques precises (couts, capacites, bareme de score, texte exact
des cartes bonus) sont des approximations raisonnables, PAS une retranscription
verifiee du livret de regles. Tout est centralise ici pour que ce soit trivial
a corriger: il suffit de changer les valeurs dans ce fichier, aucun autre
module ne contient de nombre "en dur".
"""

from __future__ import annotations

from .constants import Animal, HouseMaterial, Resource

# ---------------------------------------------------------------------------
# Plateau / ferme
# ---------------------------------------------------------------------------

GRID_ROWS = 4
GRID_COLS = 3

# Cases occupees par la maison au depart (ligne, colonne), 0-indexe.
INITIAL_HOUSE_CELLS = [(0, 0), (0, 1)]

# ---------------------------------------------------------------------------
# Manches / stades
# ---------------------------------------------------------------------------

TOTAL_ROUNDS = 14

# Dernier round de chaque stade -> a la fin de ce round: phase de reproduction
# + reveal des espaces d'action du stade suivant.
STAGE_END_ROUNDS = [4, 8, 11, 14]
NUM_STAGES = len(STAGE_END_ROUNDS)


def stage_for_round(round_no: int) -> int:
    """Stade (1-indexe) auquel appartient un round donne (1-indexe)."""
    for i, end in enumerate(STAGE_END_ROUNDS):
        if round_no <= end:
            return i + 1
    return NUM_STAGES


# ---------------------------------------------------------------------------
# Ressources de depart et actions de recolte de ressources
# ---------------------------------------------------------------------------

INITIAL_RESOURCES = {
    Resource.WOOD: 0,
    Resource.CLAY: 0,
    Resource.REED: 0,
    Resource.STONE: 0,
}

# space_id -> {resource: quantite} gagnee en s'y placant.
RESOURCE_SPACE_YIELD = {
    "forest": {Resource.WOOD: 3},
    "clay_pit": {Resource.CLAY: 3},
    "reed_bank": {Resource.REED: 2},
    "quarry": {Resource.STONE: 2},
    "forest_2": {Resource.WOOD: 2},
    "clay_pit_2": {Resource.CLAY: 2},
}

# ---------------------------------------------------------------------------
# Clotures / etables
# ---------------------------------------------------------------------------

FENCE_COST_PER_EDGE = {Resource.WOOD: 1}
STABLE_COST = {Resource.WOOD: 2}

# Un stable multiplie la capacite d'une case/pature: unites de capacite
# = taille_pature * (1 + nb_etables_dans_la_pature).
# Une case non cloturee sans etable ne loge jamais qu'1 animal, quelle que
# soit l'espece (case "non amenagee").
ANIMAL_SPACE_FACTOR = {
    Animal.RABBIT: 2,
    Animal.SHEEP: 1,
    Animal.BOAR: 1,
    Animal.CATTLE: 1,
}

MAX_ANIMALS_UNFENCED_NO_STABLE = 1

# ---------------------------------------------------------------------------
# Marches aux animaux
# ---------------------------------------------------------------------------

ANIMAL_MARKET_SPACES = {
    "rabbit_market": Animal.RABBIT,
    "sheep_market": Animal.SHEEP,
    "boar_market": Animal.BOAR,
    "cattle_market": Animal.CATTLE,
}
ANIMAL_MARKET_TAKE = 1

# ---------------------------------------------------------------------------
# Renovation de la maison
# ---------------------------------------------------------------------------

RENOVATION_COST = {
    HouseMaterial.CLAY: {Resource.CLAY: 2, Resource.REED: 1},
    HouseMaterial.STONE: {Resource.STONE: 3, Resource.REED: 1},
}

BUILD_ROOM_COST = {
    HouseMaterial.WOOD: {Resource.WOOD: 5},
    HouseMaterial.CLAY: {Resource.CLAY: 5},
    HouseMaterial.STONE: {Resource.STONE: 5},
}

ROOM_POINTS = {
    HouseMaterial.WOOD: 1,
    HouseMaterial.CLAY: 2,
    HouseMaterial.STONE: 3,
}

# ---------------------------------------------------------------------------
# Chariots
# ---------------------------------------------------------------------------

WAGON_COST = {Resource.WOOD: 2, Resource.REED: 1}
WAGON_POINTS = 2
MAX_WAGONS = 3

# ---------------------------------------------------------------------------
# Cartes bonus (pool generique simplifie, cf cards.py)
# ---------------------------------------------------------------------------

BONUS_CARD_DRAW_SPACES = ["bonus_card", "bonus_card_2"]

# ---------------------------------------------------------------------------
# Definition des espaces d'action par stade (id -> kind)
# kind in {"resource", "fence", "stable", "market", "renovate", "build_room",
#          "wagon", "bonus_card"}
# ---------------------------------------------------------------------------

ACTION_SPACES_BY_STAGE = {
    1: [
        ("forest", "resource"),
        ("clay_pit", "resource"),
        ("reed_bank", "resource"),
        ("fencing", "fence"),
        ("build_stable", "stable"),
        ("sheep_market", "market"),
        ("bonus_card", "bonus_card"),
    ],
    2: [
        ("boar_market", "market"),
        ("cattle_market", "market"),
        ("quarry", "resource"),
        ("renovate", "renovate"),
    ],
    3: [
        ("rabbit_market", "market"),
        ("forest_2", "resource"),
        ("build_room", "build_room"),
        ("wagon", "wagon"),
    ],
    4: [
        ("clay_pit_2", "resource"),
        ("bonus_card_2", "bonus_card"),
    ],
}

# ---------------------------------------------------------------------------
# Score final
# ---------------------------------------------------------------------------

# Bareme par espece: index = nombre d'animaux possede (cappe au dernier
# indice), valeur = points. -1 si 0 animal (case "vide" penalisee comme en
# Agricola classique).
ANIMAL_SCORE_TABLE = {
    Animal.RABBIT: [-1, 1, 1, 2, 2, 3, 3, 4],
    Animal.SHEEP: [-1, 1, 2, 2, 3, 3, 4, 4],
    Animal.BOAR: [-1, 1, 2, 3, 3, 4, 4, 5],
    Animal.CATTLE: [-1, 1, 2, 3, 4, 4, 5, 5],
}

PASTURE_POINTS = 1
STABLE_POINTS = 1
EMPTY_SPACE_PENALTY = -1

# points par ressource inutilisee en fin de partie (souvent 0 dans Agricola)
LEFTOVER_RESOURCE_POINTS = 0
