import pytest

from agricola2p.engine.game import AgricolaGame

np = pytest.importorskip("numpy")

from agricola2p.rl.features import FEATURE_DIM, encode  # noqa: E402
from agricola2p.rl.self_play import collect_dataset, play_episode  # noqa: E402
from agricola2p.rl.value_net import ValueNet  # noqa: E402
from agricola2p.bots.random_bot import RandomBot  # noqa: E402


def test_encode_shape_and_finite():
    game = AgricolaGame.new_game(seed=1)
    v = encode(game.state, 0)
    assert v.shape == (FEATURE_DIM,)
    assert np.all(np.isfinite(v))


def test_encode_is_perspective_dependent():
    game = AgricolaGame.new_game(seed=2)
    game.apply(game.legal_actions()[0])
    v0 = encode(game.state, 0)
    v1 = encode(game.state, 1)
    assert not np.array_equal(v0, v1)


def test_play_episode_returns_features_and_targets():
    data = play_episode(RandomBot(seed=1), RandomBot(seed=2), seed=3)
    assert len(data) > 0
    for feats, target in data:
        assert feats.shape == (FEATURE_DIM,)
        assert isinstance(target, float)


def test_collect_dataset_shapes():
    X, y = collect_dataset(n_games=2, seed0=10)
    assert X.shape[1] == FEATURE_DIM
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] > 0


def test_value_net_training_reduces_loss():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((100, 8))
    y = X @ rng.standard_normal(8)

    net = ValueNet(input_dim=8, hidden_dim=8, seed=0)
    net.set_normalization(X)
    first_loss = net.train_step(X, y, lr=0.05)
    for _ in range(50):
        last_loss = net.train_step(X, y, lr=0.05)
    assert last_loss < first_loss


def test_value_net_save_load_round_trip(tmp_path):
    net = ValueNet(input_dim=FEATURE_DIM, hidden_dim=4, seed=0)
    X = np.zeros((5, FEATURE_DIM))
    net.set_normalization(X + 1.0)
    path = tmp_path / "weights.npz"
    net.save(path)
    loaded = ValueNet.load(path)
    sample = np.random.default_rng(0).standard_normal(FEATURE_DIM)
    assert net.predict(sample) == pytest.approx(loaded.predict(sample))


def test_rl_bot_plays_legal_actions(tmp_path):
    from agricola2p.bots.rl_bot import RLBot

    net = ValueNet(input_dim=FEATURE_DIM, hidden_dim=4, seed=0)
    X, y = collect_dataset(n_games=2, seed0=20)
    net.set_normalization(X)
    net.train_step(X, y, lr=1e-3)
    weights_path = tmp_path / "weights.npz"
    net.save(weights_path)

    bot = RLBot(weights_path=weights_path, seed=1)
    game = AgricolaGame.new_game(seed=5)
    for _ in range(5):
        if game.is_terminal():
            break
        idx = game.current_player_idx
        action = bot.choose_action(game, idx)
        assert action in game.legal_actions() or action.kind == "pass"
        game.apply(action)


def test_rl_bot_missing_weights_raises(tmp_path):
    from agricola2p.bots.rl_bot import RLBot

    with pytest.raises(FileNotFoundError):
        RLBot(weights_path=tmp_path / "does_not_exist.npz")


def test_mcts_bot_with_value_fn_bootstrap_no_rollout_policy():
    from agricola2p.bots.mcts_bot import MCTSBot

    net = ValueNet(input_dim=FEATURE_DIM, hidden_dim=4, seed=0)
    X, y = collect_dataset(n_games=1, seed0=30)
    net.set_normalization(X)

    def value_fn(state, player_idx):
        return float(net.predict(encode(state, player_idx)))

    bot = MCTSBot(iterations=10, seed=1, value_fn=value_fn)
    game = AgricolaGame.new_game(seed=6)
    action = bot.choose_action(game, 0)
    assert action in game.legal_actions()
