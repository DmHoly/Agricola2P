import random

from agricola2p.engine.game import AgricolaGame
from agricola2p.engine import rules_data as R


def test_new_game_has_legal_actions():
    game = AgricolaGame.new_game(seed=1)
    actions = game.legal_actions()
    assert len(actions) > 0


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
    scores = game.scores()
    assert len(scores) == 2
    assert all(isinstance(s, int) for s in scores)


def test_stage_unlocks_progress():
    game = AgricolaGame.new_game(seed=7)
    assert game.state.stage == 1
    rng = random.Random(7)
    while game.state.round_no <= R.STAGE_END_ROUNDS[0] and not game.is_terminal():
        game.apply(rng.choice(game.legal_actions()))
    assert game.state.stage >= 2
    assert "boar_market" in game.state.unlocked_spaces
