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

    real_turns = R.TOTAL_ROUNDS * 2 * R.WORKERS_PER_PLAYER
    assert game.is_terminal()
    assert game.state.round_no == R.TOTAL_ROUNDS + 1
    # "moves" compte aussi les redeplacements gratuits d'animaux (kind
    # "reorganize"), qui ne font pas avancer le tour: au plus 1 par tour
    # d'ouvrier, donc au plus real_turns de plus que le nombre de tours reels.
    assert real_turns <= moves <= 2 * real_turns
    scores = game.scores()
    assert len(scores) == 2
    assert all(isinstance(s, (int, float)) for s in scores)


def test_tie_break_favours_non_first_mover():
    game = AgricolaGame.new_game(seed=1)
    # Aucun coup joue: fermes identiques (vides) -> scores egaux.
    assert game.scores()[0] == game.scores()[1]
    assert game.state.first_mover_idx == 0
    assert game.winner() == 1


def test_reorganize_is_free_and_capped_once_per_turn():
    from agricola2p.engine.constants import Animal

    game = AgricolaGame.new_game(seed=5)
    player = game.state.players[game.current_player_idx]
    fy = player.farmyard
    pasture_a = fy.build_pasture(1, 0, 1, 0)
    pasture_b = fy.build_pasture(1, 1, 1, 1)
    fy.add_animals_to_pasture(pasture_a.pasture_id, Animal.SHEEP, 2)

    def find_move():
        return next(
            (
                a
                for a in game.legal_actions()
                if a.kind == "reorganize"
                and a.payload["from_ref"] == pasture_a.pasture_id
                and a.payload["to_ref"] == pasture_b.pasture_id
            ),
            None,
        )

    turn_before = game.state.turn_index
    move = find_move()
    assert move is not None
    game.apply(move)
    assert game.state.turn_index == turn_before  # ne consomme pas le tour
    assert game.state.reorg_used_this_turn is True
    assert find_move() is None  # plafonne a 1 par tour d'ouvrier

    # une vraie action fait bien avancer le tour et reinitialise le plafond
    real_action = next(a for a in game.legal_actions() if a.kind != "reorganize" and a.kind != "pass")
    game.apply(real_action)
    assert game.state.turn_index == turn_before + 1
    assert game.state.reorg_used_this_turn is False
