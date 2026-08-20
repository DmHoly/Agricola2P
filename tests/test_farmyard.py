import pytest

from agricola2p.engine.constants import Animal
from agricola2p.engine.farmyard import Farmyard, FarmyardError
from agricola2p.engine import rules_data as R


def test_initial_free_cells():
    fy = Farmyard()
    assert fy.empty_cells_count() == fy.rows * fy.cols - len(R.INITIAL_HOUSE_CELLS)


def test_fence_cost_single_cell():
    fy = Farmyard()
    assert fy.fence_cost_for_rectangle(0, 2, 0, 2) == 2  # bord grille a droite/haut, voisins bas+gauche a clore


def test_cannot_build_pasture_on_house():
    fy = Farmyard()
    assert not fy.can_build_pasture(0, 0, 0, 0)
    with pytest.raises(FarmyardError):
        fy.build_pasture(0, 0, 0, 0)


def test_pasture_capacity_and_overfill():
    fy = Farmyard()
    pasture = fy.build_pasture(2, 0, 3, 0)  # 2 cases
    assert pasture.size == 2
    assert pasture.capacity(Animal.SHEEP) == 2
    assert pasture.capacity(Animal.RABBIT) == 4

    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 1)


def test_unfenced_cell_capacity_one():
    fy = Farmyard()
    cell = (1, 0)
    fy.add_animals_to_cell(cell, Animal.BOAR, 1)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_cell(cell, Animal.BOAR, 1)


def test_stable_increases_capacity():
    fy = Farmyard()
    cell = (1, 0)
    fy.build_stable(cell)
    assert fy.cell_capacity(cell, Animal.RABBIT) == R.ANIMAL_SPACE_FACTOR[Animal.RABBIT]
    fy.add_animals_to_cell(cell, Animal.RABBIT, 2)


def test_breed_increases_count_within_capacity():
    fy = Farmyard()
    pasture = fy.build_pasture(2, 0, 3, 1)  # 4 cases -> capacite mouton = 4
    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)
    fy.breed()
    assert pasture.count == 3
    fy.breed()
    fy.breed()
    assert pasture.count == 4  # plafonne a la capacite
