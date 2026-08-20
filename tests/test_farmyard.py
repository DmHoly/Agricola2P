import pytest

from agricola2p.engine.constants import Animal
from agricola2p.engine.farmyard import Farmyard, FarmyardError
from agricola2p.engine import rules_data as R


def test_initial_free_cells():
    fy = Farmyard()
    assert set(fy.free_cells()) == set(R.INITIAL_OPEN_CELLS)


def test_fence_cost_two_cells():
    fy = Farmyard()
    assert fy.fence_cost_for_rectangle(1, 0, 1, 1) == 5


def test_cannot_build_pasture_on_house():
    fy = Farmyard()
    assert not fy.can_build_pasture(0, 0, 0, 0)
    with pytest.raises(FarmyardError):
        fy.build_pasture(0, 0, 0, 0)


def test_cannot_build_pasture_on_locked_cell():
    fy = Farmyard()
    assert not fy.can_build_pasture(2, 0, 2, 0)  # appartient a tile_b, pas encore achetee


def test_buying_tile_unlocks_cells():
    fy = Farmyard()
    assert not fy.can_build_pasture(1, 2, 1, 3)
    fy.buy_tile("tile_a", [(1, 2), (1, 3)])
    assert fy.can_build_pasture(1, 2, 1, 3)


def test_pasture_capacity_and_overfill():
    fy = Farmyard()
    pasture = fy.build_pasture(1, 0, 1, 1)  # 2 cases
    assert pasture.size == 2
    assert pasture.capacity() == 2

    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 1)


def test_unfenced_cell_capacity_one():
    fy = Farmyard()
    cell = (0, 2)
    fy.add_animals_to_cell(cell, Animal.BOAR, 1)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_cell(cell, Animal.BOAR, 1)


def test_stable_increases_capacity():
    fy = Farmyard()
    cell = (0, 3)
    fy.build_stable(cell)
    assert fy.cell_capacity(cell) == R.STABLE_CAPACITY
    fy.add_animals_to_cell(cell, Animal.HORSE, 2)


def test_breed_increases_count_within_capacity():
    fy = Farmyard()
    fy.buy_tile("tile_a", [(1, 2), (1, 3)])
    pasture = fy.build_pasture(1, 0, 1, 3)  # 4 cases
    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)
    fy.breed()
    assert pasture.count == 3
    fy.breed()
    fy.breed()
    assert pasture.count == 4  # plafonne a la capacite


def test_tile_fully_used():
    fy = Farmyard()
    fy.buy_tile("tile_a", [(1, 2), (1, 3)])
    assert not fy.tile_fully_used([(1, 2), (1, 3)])
    fy.add_animals_to_cell((1, 2), Animal.HORSE, 1)
    fy.add_animals_to_cell((1, 3), Animal.HORSE, 1)
    assert fy.tile_fully_used([(1, 2), (1, 3)])
