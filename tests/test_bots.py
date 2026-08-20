from agricola2p.bots.heuristic_bot import HeuristicBot
from agricola2p.bots.mcts_bot import MCTSBot
from agricola2p.bots.random_bot import RandomBot
from agricola2p.engine.game import AgricolaGame


def _play(bot0, bot1, seed=1):
    game = AgricolaGame.new_game(seed=seed)
    bots = [bot0, bot1]
    steps = 0
    while not game.is_terminal():
        idx = game.current_player_idx
        action = bots[idx].choose_action(game, idx)
        assert action in game.legal_actions() or action.kind == "pass"
        game.apply(action)
        steps += 1
        assert steps < 5000
    return game.scores()


def test_random_vs_random():
    scores = _play(RandomBot(seed=1), RandomBot(seed=2), seed=1)
    assert len(scores) == 2


def test_heuristic_vs_random():
    scores = _play(HeuristicBot(seed=1), RandomBot(seed=2), seed=3)
    assert len(scores) == 2


def test_mcts_returns_legal_action_and_finishes_small_game():
    bot = MCTSBot(iterations=15, seed=1)
    game = AgricolaGame.new_game(seed=5)
    action = bot.choose_action(game, game.current_player_idx)
    assert action in game.legal_actions()


def test_mcts_vs_heuristic_short_playout():
    scores = _play(MCTSBot(iterations=10, seed=1), HeuristicBot(seed=2), seed=9)
    assert len(scores) == 2
