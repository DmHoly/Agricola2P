"""Modele de la ferme (farmyard) d'un joueur.

Simplification assumee (voir README): les patures sont des rectangles
axis-aligned (pas de formes quelconques). C'est une simplification courante
pour les implementations numeriques de jeux type Agricola; le cout en bois
d'une pature est le nombre de segments de son perimetre qui ne sont pas deja
sur le bord de la grille.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import rules_data as R
from .constants import Animal, HouseMaterial

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

    def capacity(self, species: Animal) -> int:
        units = self.size * (1 + self.stables)
        return units * R.ANIMAL_SPACE_FACTOR[species]


@dataclass
class Farmyard:
    rows: int = R.GRID_ROWS
    cols: int = R.GRID_COLS
    house_cells: set[Cell] = field(default_factory=lambda: set(R.INITIAL_HOUSE_CELLS))
    house_material: HouseMaterial = HouseMaterial.WOOD
    pastures: dict[int, Pasture] = field(default_factory=dict)
    cell_pasture: dict[Cell, int] = field(default_factory=dict)
    stable_cells: set[Cell] = field(default_factory=set)  # standalone stables
    animal_cells: dict[Cell, tuple[Animal, int]] = field(default_factory=dict)
    wagons: int = 0
    _next_pasture_id: int = 1

    # -- cases -------------------------------------------------------
    def all_cells(self) -> list[Cell]:
        return [(r, c) for r in range(self.rows) for c in range(self.cols)]

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_house(self, cell: Cell) -> bool:
        return cell in self.house_cells

    def used_cells(self) -> set[Cell]:
        used = set(self.house_cells) | set(self.cell_pasture.keys())
        used |= self.stable_cells
        used |= self.animal_cells.keys()
        return used

    def free_cells(self) -> list[Cell]:
        used = self.used_cells()
        return [c for c in self.all_cells() if c not in used]

    def empty_cells_count(self) -> int:
        """Cases ne faisant rien: ni maison, ni pature, ni etable, ni animal."""
        return len(self.free_cells())

    # -- patures / clotures --------------------------------------------
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
        if not all(self.in_bounds(c) for c in cells):
            return False
        used = self.used_cells()
        return all(c not in used for c in cells)

    def build_pasture(self, r1: int, c1: int, r2: int, c2: int) -> Pasture:
        if not self.can_build_pasture(r1, c1, r2, c2):
            raise FarmyardError("Rectangle de pature invalide ou deja occupe")
        cells = frozenset(self.rectangle_cells(r1, c1, r2, c2))
        pasture = Pasture(pasture_id=self._next_pasture_id, cells=cells)
        self._next_pasture_id += 1
        self.pastures[pasture.pasture_id] = pasture
        for c in cells:
            self.cell_pasture[c] = pasture.pasture_id
        return pasture

    # -- etables ---------------------------------------------------------
    def can_build_stable(self, cell: Cell) -> bool:
        if not self.in_bounds(cell) or self.is_house(cell):
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
    def cell_capacity(self, cell: Cell, species: Animal) -> int:
        if cell in self.stable_cells:
            return R.ANIMAL_SPACE_FACTOR[species]
        return R.MAX_ANIMALS_UNFENCED_NO_STABLE

    def total_animals(self) -> dict[Animal, int]:
        totals = {a: 0 for a in Animal}
        for pasture in self.pastures.values():
            if pasture.animal is not None:
                totals[pasture.animal] += pasture.count
        for animal, count in self.animal_cells.values():
            totals[animal] += count
        return totals

    def add_animals_to_pasture(self, pasture_id: int, species: Animal, n: int) -> None:
        pasture = self.pastures[pasture_id]
        if pasture.animal is not None and pasture.animal != species and pasture.count > 0:
            raise FarmyardError("La pature contient deja une autre espece")
        cap = pasture.capacity(species)
        new_count = pasture.count + n if pasture.animal == species else n
        if new_count > cap:
            raise FarmyardError("Capacite de la pature depassee")
        pasture.animal = species
        pasture.count = new_count

    def add_animals_to_cell(self, cell: Cell, species: Animal, n: int) -> None:
        cap = self.cell_capacity(cell, species)
        existing_species, existing_n = self.animal_cells.get(cell, (species, 0))
        if existing_n > 0 and existing_species != species:
            raise FarmyardError("La case contient deja une autre espece")
        new_n = existing_n + n
        if new_n > cap:
            raise FarmyardError("Capacite de la case depassee")
        self.animal_cells[cell] = (species, new_n)

    def available_capacity(self) -> list[tuple[str, Cell | int, Animal, int]]:
        """Liste des emplacements avec de la place: (kind, ref, espece_ou_None, place_libre).

        kind == "pasture" -> ref est pasture_id ; kind == "cell" -> ref est Cell.
        Pour un emplacement vide (aucun animal encore), une entree par espece
        possible est retournee.
        """
        out: list[tuple[str, Cell | int, Animal, int]] = []
        for pasture in self.pastures.values():
            if pasture.animal is not None:
                free = pasture.capacity(pasture.animal) - pasture.count
                if free > 0:
                    out.append(("pasture", pasture.pasture_id, pasture.animal, free))
            else:
                for species in Animal:
                    cap = pasture.capacity(species)
                    if cap > 0:
                        out.append(("pasture", pasture.pasture_id, species, cap))
        for cell in self.stable_cells | set(self.free_cells()):
            existing = self.animal_cells.get(cell)
            if existing and existing[1] > 0:
                species, n = existing
                cap = self.cell_capacity(cell, species)
                free = cap - n
                if free > 0:
                    out.append(("cell", cell, species, free))
            else:
                for species in Animal:
                    cap = self.cell_capacity(cell, species)
                    if cap > 0:
                        out.append(("cell", cell, species, cap))
        return out

    # -- maison --------------------------------------------------------
    def add_room(self, cell: Cell) -> None:
        if not self.in_bounds(cell) or cell in self.used_cells():
            raise FarmyardError("Case invalide pour agrandir la maison")
        adjacent = any(
            (cell[0] + dr, cell[1] + dc) in self.house_cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        if not adjacent:
            raise FarmyardError("Une piece doit etre adjacente a la maison existante")
        self.house_cells.add(cell)

    def renovate(self, new_material: HouseMaterial) -> None:
        if self.house_material.next != new_material:
            raise FarmyardError("Renovation invalide (ordre bois->argile->pierre)")
        self.house_material = new_material

    # -- reproduction ----------------------------------------------------
    def breed(self) -> None:
        """Chaque groupe avec >=2 animaux d'une meme espece et de la place
        produit 1 animal supplementaire (phase de reproduction de fin de stade).
        """
        for pasture in self.pastures.values():
            if pasture.animal is not None and pasture.count >= 2:
                cap = pasture.capacity(pasture.animal)
                if pasture.count < cap:
                    pasture.count += 1
        for cell, (species, n) in list(self.animal_cells.items()):
            if n >= 2:
                cap = self.cell_capacity(cell, species)
                if n < cap:
                    self.animal_cells[cell] = (species, n + 1)
