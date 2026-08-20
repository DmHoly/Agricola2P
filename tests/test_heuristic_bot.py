from agricola2p.bots.heuristic_bot import _breeding_heuristic_bonus, AVERAGE_HEAD_VALUE
from agricola2p.engine.constants import Animal
from agricola2p.engine.farmyard import Farmyard


def test_penalises_breeding_group_stuck_at_capacity():
    fy = Farmyard()
    pasture = fy.build_pasture(1, 0, 1, 0)  # 1 case, capacite 2 sans auge
    fy.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)  # deja a pleine capacite

    bonus = _breeding_heuristic_bonus(fy_before=fy, fy_after=fy, rounds_remaining=5)
    assert bonus == -AVERAGE_HEAD_VALUE


def test_rewards_first_time_crossing_breeding_threshold():
    fy_before = Farmyard()
    fy_after = Farmyard()
    pasture = fy_after.build_pasture(1, 0, 1, 1)  # capacite 4, largement assez
    fy_after.add_animals_to_pasture(pasture.pasture_id, Animal.SHEEP, 2)

    bonus = _breeding_heuristic_bonus(fy_before, fy_after, rounds_remaining=6)
    assert bonus == AVERAGE_HEAD_VALUE * 6


def test_no_bonus_when_already_breeding_before_and_after():
    fy_before = Farmyard()
    p_before = fy_before.build_pasture(1, 0, 1, 1)
    fy_before.add_animals_to_pasture(p_before.pasture_id, Animal.SHEEP, 2)

    fy_after = Farmyard()
    p_after = fy_after.build_pasture(1, 0, 1, 1)
    fy_after.add_animals_to_pasture(p_after.pasture_id, Animal.SHEEP, 3)  # deja >=2 avant

    bonus = _breeding_heuristic_bonus(fy_before, fy_after, rounds_remaining=4)
    assert bonus == 0.0
