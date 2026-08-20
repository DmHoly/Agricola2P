"""Modele de la ferme (farmyard) d'un joueur.

Mecanique centrale (cloture/enclos/batiments), cf README:

- Une barriere se pose sur une bordure entre 2 cases (ou le bord du plateau,
  toujours gratuit) et coute 1 ressource (bois OU pierre) par segment.
- Deux enclos voisins MUTUALISENT la barriere qui les separe: elle n'est
  payee qu'une fois (le moteur retient les aretes deja cloturees dans
  `fences` et ne les refacture jamais).
- Les bords de la maison et des batiments (stalle/etable) sont des murs
  naturels gratuits: pas besoin de barriere le long de leur cote.
- Une fois posee, une barriere/auge/batiment n'est jamais deplacee ni
  retiree (seul le contenu - les animaux - reste, par simplification,
  fixe une fois place: voir limitation documentee dans le README).
- Un enclos de N cases loge N*2 animaux, doublant par auge (jusqu'a 3
  auges -> N*16).
- Une Stalle (1 case) loge 4 animaux (1 PV), amelio(rable en Etable (5
  animaux, 2 PV) ou Etable ouverte (4 animaux, 2 PV).
- Une case libre (hors maison/batiment/enclos) ne loge aucun animal tant
  qu'elle n'a pas recu une auge (alors capacite 1).

Simplification assumee: les enclos sont des rectangles axis-aligned (pas de
formes quelconques). La ferme grandit uniquement par l'achat de tuiles
d'extension (rules_data.EXTENSION_TILES, max 2, 3 cases chacune).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import rules_data as R
from .constants import Animal

Cell = tuple[int, int]
Edge = frozenset  # frozenset({cellA, cellB})

_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class FarmyardError(ValueError):
    """Tentative d'action illegale sur la ferme."""


@dataclass
class Pasture:
    pasture_id: int
    cells: frozenset[Cell]
    troughs: int = 0
    animal: Animal | None = None
    count: int = 0

    @property
    def size(self) -> int:
        return len(self.cells)

    def capacity(self) -> int:
        return R.pasture_capacity(self.size, self.troughs)


@dataclass
class Building:
    level: str = "stalle"  # "stalle" | "etable" | "etable_ouverte"
    has_trough: bool = False

    def capacity(self) -> int:
        base = R.BUILDING_LEVELS[self.level]["capacity"]
        return base + (R.BUILDING_TROUGH_BONUS if self.has_trough else 0)

    def points(self) -> int:
        return R.BUILDING_LEVELS[self.level]["points"]


@dataclass
class Farmyard:
    rows: int = R.GRID_ROWS
    cols: int = R.GRID_COLS
    house_cells: set[Cell] = field(default_factory=lambda: set(R.INITIAL_HOUSE_CELLS))
    house_upgraded: bool = False
    unlocked_cells: set[Cell] = field(
        default_factory=lambda: set(R.INITIAL_HOUSE_CELLS) | set(R.INITIAL_OPEN_CELLS)
    )
    owned_tiles: set[str] = field(default_factory=set)
    pastures: dict[int, Pasture] = field(default_factory=dict)
    cell_pasture: dict[Cell, int] = field(default_factory=dict)
    fences: set = field(default_factory=set)  # set[frozenset[Cell, Cell]]
    building_cells: dict[Cell, Building] = field(default_factory=dict)
    trough_cells: set[Cell] = field(default_factory=set)  # case non cloturee equipee d'une auge
    animal_cells: dict[Cell, tuple[Animal, int]] = field(default_factory=dict)
    _next_pasture_id: int = 1

    # -- cases -------------------------------------------------------
    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_house(self, cell: Cell) -> bool:
        return cell in self.house_cells

    def is_unlocked(self, cell: Cell) -> bool:
        return cell in self.unlocked_cells

    def playable_cells(self) -> list[Cell]:
        """Cases deverrouillees, hors maison, utilisables pour enclos/batiment/auge."""
        return [c for c in self.unlocked_cells if c not in self.house_cells]

    def used_cells(self) -> set[Cell]:
        used = set(self.house_cells) | set(self.cell_pasture.keys())
        used |= self.building_cells.keys()
        used |= self.trough_cells
        return used

    def free_cells(self) -> list[Cell]:
        used = self.used_cells()
        return [c for c in self.playable_cells() if c not in used]

    # -- tuiles d'extension -----------------------------------------
    def buy_tile(self, tile_id: str, cells: list[Cell]) -> None:
        if tile_id in self.owned_tiles:
            raise FarmyardError("Tuile deja possedee")
        self.owned_tiles.add(tile_id)
        self.unlocked_cells |= set(cells)

    def tile_fully_used(self, cells: list[Cell]) -> bool:
        used = self.used_cells()
        return all(c in used for c in cells)

    # -- murs naturels & mutualisation des barrieres --------------------
    def _is_natural_wall(self, cell: Cell) -> bool:
        return cell in self.house_cells or cell in self.building_cells

    def _boundary_edges_requiring_fence(self, cells: set[Cell]) -> set:
        edges = set()
        for cell in cells:
            for dr, dc in _DIRECTIONS:
                nb = (cell[0] + dr, cell[1] + dc)
                if nb in cells:
                    continue  # arete interne au nouvel enclos: pas de barriere
                if not self.in_bounds(nb):
                    continue  # bord du plateau: gratuit
                if self._is_natural_wall(nb):
                    continue  # mur naturel (maison/batiment): gratuit
                edge = Edge((cell, nb))
                if edge in self.fences:
                    continue  # deja cloturee par un enclos voisin: mutualisee
                edges.add(edge)
        return edges

    # -- enclos / clotures --------------------------------------------
    def rectangle_cells(self, r1: int, c1: int, r2: int, c2: int) -> list[Cell]:
        lo_r, hi_r = sorted((r1, r2))
        lo_c, hi_c = sorted((c1, c2))
        return [(r, c) for r in range(lo_r, hi_r + 1) for c in range(lo_c, hi_c + 1)]

    def fence_cost_for_rectangle(self, r1: int, c1: int, r2: int, c2: int) -> int:
        cells = set(self.rectangle_cells(r1, c1, r2, c2))
        return len(self._boundary_edges_requiring_fence(cells))

    def can_build_pasture(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        cells = self.rectangle_cells(r1, c1, r2, c2)
        if not all(self.is_unlocked(c) and c not in self.house_cells for c in cells):
            return False
        used = self.used_cells()
        return all(c not in used for c in cells)

    def build_pasture(self, r1: int, c1: int, r2: int, c2: int) -> Pasture:
        if not self.can_build_pasture(r1, c1, r2, c2):
            raise FarmyardError("Rectangle d'enclos invalide ou deja occupe")
        cells_set = set(self.rectangle_cells(r1, c1, r2, c2))
        new_fences = self._boundary_edges_requiring_fence(cells_set)
        self.fences |= new_fences

        cells = frozenset(cells_set)
        pasture = Pasture(pasture_id=self._next_pasture_id, cells=cells)
        self._next_pasture_id += 1
        self.pastures[pasture.pasture_id] = pasture
        for c in cells:
            self.cell_pasture[c] = pasture.pasture_id
        return pasture

    # -- batiments (Stalle -> Etable / Etable ouverte) --------------------
    def can_build_building(self, cell: Cell) -> bool:
        return self.is_unlocked(cell) and not self.is_house(cell) and cell not in self.used_cells()

    def build_building(self, cell: Cell) -> None:
        if not self.can_build_building(cell):
            raise FarmyardError("Impossible de construire un batiment ici")
        self.building_cells[cell] = Building(level="stalle")

    def can_upgrade_building(self, cell: Cell) -> bool:
        building = self.building_cells.get(cell)
        return building is not None and building.level == "stalle"

    def upgrade_building(self, cell: Cell, new_level: str) -> None:
        if not self.can_upgrade_building(cell):
            raise FarmyardError("Impossible d'ameliorer ce batiment")
        if new_level not in R.BUILDING_UPGRADE_TARGETS:
            raise FarmyardError("Niveau de batiment inconnu")
        self.building_cells[cell].level = new_level

    # -- renovation de la maison -----------------------------------------
    def can_upgrade_house(self) -> bool:
        return not self.house_upgraded

    def upgrade_house(self) -> None:
        if not self.can_upgrade_house():
            raise FarmyardError("Maison deja renovee")
        self.house_upgraded = True

    # -- auges ---------------------------------------------------------
    def can_build_trough_on_pasture(self, pasture_id: int) -> bool:
        pasture = self.pastures.get(pasture_id)
        return pasture is not None and pasture.troughs < R.MAX_TROUGHS_PER_PASTURE

    def can_build_trough_on_building(self, cell: Cell) -> bool:
        building = self.building_cells.get(cell)
        return building is not None and not building.has_trough

    def can_build_trough_on_yard(self, cell: Cell) -> bool:
        return self.is_unlocked(cell) and not self.is_house(cell) and cell not in self.used_cells()

    def build_trough_on_pasture(self, pasture_id: int) -> None:
        if not self.can_build_trough_on_pasture(pasture_id):
            raise FarmyardError("Impossible d'ajouter une auge a cet enclos")
        self.pastures[pasture_id].troughs += 1

    def build_trough_on_building(self, cell: Cell) -> None:
        if not self.can_build_trough_on_building(cell):
            raise FarmyardError("Impossible d'ajouter une auge a ce batiment")
        self.building_cells[cell].has_trough = True

    def build_trough_on_yard(self, cell: Cell) -> None:
        if not self.can_build_trough_on_yard(cell):
            raise FarmyardError("Impossible d'ajouter une auge sur cette case")
        self.trough_cells.add(cell)

    # -- animaux -----------------------------------------------------
    def cell_capacity(self, cell: Cell) -> int:
        if cell in self.building_cells:
            return self.building_cells[cell].capacity()
        if cell in self.trough_cells:
            return R.YARD_TROUGH_CAPACITY
        return 0

    def total_animals(self) -> dict[Animal, int]:
        totals = {a: 0 for a in Animal}
        for pasture in self.pastures.values():
            if pasture.animal is not None:
                totals[pasture.animal] += pasture.count
        for animal, count in self.animal_cells.values():
            totals[animal] += count
        return totals

    def add_animals_to_pasture(self, pasture_id: int, species: Animal, n: int) -> int:
        pasture = self.pastures[pasture_id]
        if pasture.animal is not None and pasture.animal != species and pasture.count > 0:
            raise FarmyardError("L'enclos contient deja une autre espece")
        prior_count = pasture.count if pasture.animal == species else 0
        free = pasture.capacity() - prior_count
        added = min(n, free)
        if added <= 0:
            raise FarmyardError("Capacite de l'enclos depassee")
        pasture.animal = species
        pasture.count = prior_count + added
        return added

    def add_animals_to_cell(self, cell: Cell, species: Animal, n: int) -> int:
        cap = self.cell_capacity(cell)
        existing_species, existing_n = self.animal_cells.get(cell, (species, 0))
        if existing_n > 0 and existing_species != species:
            raise FarmyardError("La case contient deja une autre espece")
        free = cap - existing_n
        added = min(n, free)
        if added <= 0:
            raise FarmyardError("Capacite de la case depassee")
        self.animal_cells[cell] = (species, existing_n + added)
        return added

    def available_capacity(self) -> list[tuple[str, Cell | int, Animal, int]]:
        """Liste des emplacements avec de la place: (kind, ref, espece_ou_None, place_libre).

        kind == "pasture" -> ref est pasture_id ; kind == "cell" -> ref est Cell.
        """
        out: list[tuple[str, Cell | int, Animal, int]] = []
        for pasture in self.pastures.values():
            if pasture.animal is not None:
                free = pasture.capacity() - pasture.count
                if free > 0:
                    out.append(("pasture", pasture.pasture_id, pasture.animal, free))
            else:
                cap = pasture.capacity()
                if cap > 0:
                    for species in Animal:
                        out.append(("pasture", pasture.pasture_id, species, cap))
        housing_cells = set(self.building_cells.keys()) | self.trough_cells
        for cell in housing_cells:
            existing = self.animal_cells.get(cell)
            if existing and existing[1] > 0:
                species, n = existing
                free = self.cell_capacity(cell) - n
                if free > 0:
                    out.append(("cell", cell, species, free))
            else:
                cap = self.cell_capacity(cell)
                if cap > 0:
                    for species in Animal:
                        out.append(("cell", cell, species, cap))
        return out

    # -- reproduction ----------------------------------------------------
    def breed(self) -> None:
        """Chaque groupe avec >=2 animaux d'une meme espece et de la place
        produit 1 animal supplementaire (fin de chaque tour)."""
        for pasture in self.pastures.values():
            if pasture.animal is not None and pasture.count >= 2:
                cap = pasture.capacity()
                if pasture.count < cap:
                    pasture.count += 1
        for cell, (species, n) in list(self.animal_cells.items()):
            if n >= 2:
                cap = self.cell_capacity(cell)
                if n < cap:
                    self.animal_cells[cell] = (species, n + 1)
