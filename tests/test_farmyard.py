import pytest

from agricola2p.engine.constants import Animal
from agricola2p.engine.farmyard import Farmyard, FarmyardError
from agricola2p.engine import rules_data as R


def test_initial_free_cells():
    fy = Farmyard()
    assert set(fy.free_cells()) == set(R.INITIAL_OPEN_CELLS)


def test_fence_cost_is_free_along_house_natural_wall():
    fy = Farmyard()
    # (1,0)-(1,1) sont sous la maison (0,0)-(0,1): ces 2 aretes sont gratuites
    # (mur naturel). Restent: dessous de (1,0), dessous+droite de (1,1).
    assert fy.fence_cost_for_rectangle(1, 0, 1, 1) == 3


def test_neighbouring_pastures_mutualise_shared_fence():
    fy = Farmyard()
    fy.build_pasture(1, 0, 1, 0)  # cloture la case (1,0) seule
    # Une pature voisine sur (1,1) partage l'arete avec (1,0): deja payee.
    cost_alone = fy.fence_cost_for_rectangle(1, 1, 1, 1)
    fy2 = Farmyard()
    cost_without_neighbour = fy2.fence_cost_for_rectangle(1, 1, 1, 1)
    assert cost_alone == cost_without_neighbour - 1


def test_building_acts_as_natural_wall_for_adjacent_pasture():
    fy = Farmyard()
    fy.build_building((1, 0))
    cost_with_building = fy.fence_cost_for_rectangle(1, 1, 1, 1)
    fy2 = Farmyard()
    cost_without_building = fy2.fence_cost_for_rectangle(1, 1, 1, 1)
    assert cost_with_building == cost_without_building - 1


def test_cannot_build_pasture_on_house():
    fy = Farmyard()
    assert not fy.can_build_pasture(0, 0, 0, 0)
    with pytest.raises(FarmyardError):
        fy.build_pasture(0, 0, 0, 0)


def test_cannot_build_pasture_on_locked_cell():
    fy = Farmyard()
    assert not fy.can_build_pasture(2, 0, 2, 0)  # appartient a tile_a, pas encore achetee


def test_buying_tile_unlocks_cells():
    fy = Farmyard()
    assert not fy.can_build_pasture(2, 0, 2, 2)
    fy.buy_tile("tile_a", [(2, 0), (2, 1), (2, 2)])
    assert fy.can_build_pasture(2, 0, 2, 2)


def test_pasture_capacity_doubles_per_trough():
    fy = Farmyard()
    pasture = fy.build_pasture(1, 0, 1, 1)  # 2 cases
    assert pasture.capacity() == 4  # 2 * 2 * 2**0
    fy.build_trough_on_pasture(pasture.pasture_id)
    assert pasture.capacity() == 8  # 2 * 2 * 2**1
    fy.build_trough_on_pasture(pasture.pasture_id)
    assert pasture.capacity() == 16
    fy.build_trough_on_pasture(pasture.pasture_id)
    assert pasture.capacity() == 32  # plafond a 3 auges
    with pytest.raises(FarmyardError):
        fy.build_trough_on_pasture(pasture.pasture_id)


def test_pasture_overfill_raises():
    fy = Farmyard()
    pasture = fy.build_pasture(1, 0, 1, 1)  # capacite 4
    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 4)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 1)


def test_yard_cell_needs_trough_to_house_animal():
    fy = Farmyard()
    cell = (0, 2)
    assert fy.cell_capacity(cell) == 0
    with pytest.raises(FarmyardError):
        fy.add_animals_to_cell(cell, Animal.BOAR, 1)
    fy.build_trough_on_yard(cell)
    assert fy.cell_capacity(cell) == 1
    fy.add_animals_to_cell(cell, Animal.BOAR, 1)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_cell(cell, Animal.BOAR, 1)


def test_stalle_upgrade_to_etable():
    fy = Farmyard()
    cell = (1, 0)
    fy.build_building(cell)
    assert fy.cell_capacity(cell) == 4
    assert fy.building_cells[cell].points() == 1

    fy.add_animals_to_cell(cell, Animal.HORSE, 4)
    with pytest.raises(FarmyardError):
        fy.add_animals_to_cell(cell, Animal.HORSE, 1)

    assert not fy.can_upgrade_building((1, 1))  # pas de batiment ici
    fy.upgrade_building(cell, "etable")
    assert fy.cell_capacity(cell) == 5
    assert fy.building_cells[cell].points() == 2
    fy.add_animals_to_cell(cell, Animal.HORSE, 1)  # la 5e place est dispo

    with pytest.raises(FarmyardError):
        fy.upgrade_building(cell, "etable_ouverte")  # deja amelioree


def test_building_trough_bonus():
    fy = Farmyard()
    cell = (1, 0)
    fy.build_building(cell)
    fy.build_trough_on_building(cell)
    assert fy.cell_capacity(cell) == 5  # stalle(4) + auge(1)


def test_house_upgrade():
    fy = Farmyard()
    assert not fy.house_upgraded
    fy.upgrade_house()
    assert fy.house_upgraded
    with pytest.raises(FarmyardError):
        fy.upgrade_house()


def test_breed_increases_count_within_capacity():
    fy = Farmyard()
    pasture = fy.build_pasture(1, 0, 1, 1)  # capacite 4
    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)
    fy.breed()
    assert pasture.count == 3
    fy.breed()
    fy.breed()
    assert pasture.count == 4  # plafonne a la capacite


def test_tile_fully_used():
    fy = Farmyard()
    fy.buy_tile("tile_a", [(2, 0), (2, 1), (2, 2)])
    assert not fy.tile_fully_used([(2, 0), (2, 1), (2, 2)])
    fy.build_building((2, 0))
    fy.build_trough_on_yard((2, 1))
    fy.build_pasture(2, 2, 2, 2)
    assert fy.tile_fully_used([(2, 0), (2, 1), (2, 2)])
