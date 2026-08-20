import random

from agricola2p.engine.game import AgricolaGame
from agricola2p.engine import rules_data as R


def test_new_game_has_legal_actions():
    game = AgricolaGame.new_game(seed=1)
    actions = game.legal_actions()
    assert len(actions) > 0


def test_turn_order_alternates_and_round_advances():
    game = AgricolaGame.new_game(seed=2)
    start = game.current_player_idx
    movers = []
    for _ in range(2 * R.WORKERS_PER_PLAYER):
        movers.append(game.current_player_idx)
        action = game.legal_actions()[0]
        game.apply(action)
    assert movers == [start, 1 - start] * R.WORKERS_PER_PLAYER
    assert game.state.round_no == 2


def test_accumulation_grows_when_space_unused():
    game = AgricolaGame.new_game(seed=3)
    initial = game.state.accumulators["stone_space"]
    for _ in range(2 * R.WORKERS_PER_PLAYER):
        actions = [a for a in game.legal_actions() if a.space_id != "stone_space"]
        game.apply(actions[0] if actions else game.legal_actions()[0])
    assert game.state.accumulators["stone_space"] == initial * 2


def test_random_playthrough_terminates():
    game = AgricolaGame.new_game(seed=42)
    rng = random.Random(42)
    moves = 0
    max_moves = 10_000
    while not game.is_terminal() and moves < max_moves:
        action = rng.choice(game.legal_actions())
        game.apply(action)
        moves += 1

    assert game.is_terminal()
    assert game.state.round_no == R.TOTAL_ROUNDS + 1
    assert moves == R.TOTAL_ROUNDS * 2 * R.WORKERS_PER_PLAYER
    scores = game.scores()
    assert len(scores) == 2
    assert all(isinstance(s, int) for s in scores)
