"""Modele de la ferme (farmyard) d'un joueur.

Simplifications assumees (voir README):
- Les enclos sont des rectangles axis-aligned (pas de formes quelconques).
  Une fois pose, un enclos n'est jamais deplace ni modifie (conforme aux
  regles: "un enclos pose ne peut plus etre deplace ni modifie").
- La ferme grandit uniquement par l'achat de tuiles d'extension
  (rules_data.EXTENSION_TILES); les cases non deverrouillees ne peuvent
  accueillir ni cloture, ni etable, ni animal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import rules_data as R
from .constants import Animal

Cell = tuple[int, int]


class FarmyardError(ValueError):
    """Tentative d'action illegale sur la ferme."""


@dataclass
class Pasture:
    pasture_id: int
    cells: frozenset[Cell]
    stables: int = 0
    animal: Animal | None = None
    count: int = 0

    @property
    def size(self) -> int:
        return len(self.cells)

    def capacity(self) -> int:
        # Chaque case cloturee loge 1 animal ; chaque etable ajoute
        # (STABLE_CAPACITY - 1) places supplementaires dans l'enclos.
        return self.size + self.stables * (R.STABLE_CAPACITY - 1)


@dataclass
class Farmyard:
    rows: int = R.GRID_ROWS
    cols: int = R.GRID_COLS
    house_cells: set[Cell] = field(default_factory=lambda: set(R.INITIAL_HOUSE_CELLS))
    unlocked_cells: set[Cell] = field(
        default_factory=lambda: set(R.INITIAL_HOUSE_CELLS) | set(R.INITIAL_OPEN_CELLS)
    )
    owned_tiles: set[str] = field(default_factory=set)
    pastures: dict[int, Pasture] = field(default_factory=dict)
    cell_pasture: dict[Cell, int] = field(default_factory=dict)
    stable_cells: set[Cell] = field(default_factory=set)  # etables hors enclos
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
        """Cases deverrouillees, hors maison, utilisables pour enclos/etable/animal."""
        return [c for c in self.unlocked_cells if c not in self.house_cells]

    def used_cells(self) -> set[Cell]:
        used = set(self.house_cells) | set(self.cell_pasture.keys())
        used |= self.stable_cells
        used |= self.animal_cells.keys()
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

    # -- enclos / clotures --------------------------------------------
    def rectangle_cells(self, r1: int, c1: int, r2: int, c2: int) -> list[Cell]:
        lo_r, hi_r = sorted((r1, r2))
        lo_c, hi_c = sorted((c1, c2))
        return [(r, c) for r in range(lo_r, hi_r + 1) for c in range(lo_c, hi_c + 1)]

    def fence_cost_for_rectangle(self, r1: int, c1: int, r2: int, c2: int) -> int:
        cells = set(self.rectangle_cells(r1, c1, r2, c2))
        edges = 0
        for (r, c) in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in cells:
                    continue
                if self.in_bounds(nb):
                    edges += 1  # frontiere interne: cloture necessaire
                # si hors grille: bord de ferme, pas besoin de cloture
        return edges

    def can_build_pasture(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        cells = self.rectangle_cells(r1, c1, r2, c2)
        if not all(self.is_unlocked(c) and c not in self.house_cells for c in cells):
            return False
        used = self.used_cells()
        return all(c not in used for c in cells)

    def build_pasture(self, r1: int, c1: int, r2: int, c2: int) -> Pasture:
        if not self.can_build_pasture(r1, c1, r2, c2):
            raise FarmyardError("Rectangle d'enclos invalide ou deja occupe")
        cells = frozenset(self.rectangle_cells(r1, c1, r2, c2))
        pasture = Pasture(pasture_id=self._next_pasture_id, cells=cells)
        self._next_pasture_id += 1
        self.pastures[pasture.pasture_id] = pasture
        for c in cells:
            self.cell_pasture[c] = pasture.pasture_id
        return pasture

    # -- etables ---------------------------------------------------------
    def can_build_stable(self, cell: Cell) -> bool:
        if not self.is_unlocked(cell) or self.is_house(cell):
            return False
        if cell in self.stable_cells:
            return False
        pid = self.cell_pasture.get(cell)
        if pid is not None:
            pasture = self.pastures[pid]
            return pasture.stables < pasture.size
        return True  # case libre ou avec un animal deja pose: l'etable peut s'y ajouter

    def build_stable(self, cell: Cell) -> None:
        if not self.can_build_stable(cell):
            raise FarmyardError("Impossible de construire une etable ici")
        pid = self.cell_pasture.get(cell)
        if pid is not None:
            self.pastures[pid].stables += 1
        else:
            self.stable_cells.add(cell)

    # -- animaux -----------------------------------------------------
    def cell_capacity(self, cell: Cell) -> int:
        if cell in self.stable_cells:
            return R.STABLE_CAPACITY
        return R.MAX_ANIMALS_UNFENCED_NO_STABLE

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
        for cell in self.stable_cells | set(self.free_cells()):
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
