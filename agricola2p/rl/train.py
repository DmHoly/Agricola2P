"""Entraine le reseau de valeur par self-play et sauve les poids.

Usage:
    # gen 1: self-play avec les bots existants (Heuristic/Random)
    python3 -m agricola2p.rl.train --games 3000 --epochs 60

    # gen 2+: auto-jeu RLBot vs RLBot avec les poids actuels, reseau plus
    # profond (2 couches cachees ici)
    python3 -m agricola2p.rl.train --self-play rl --hidden 64 32 --games 3000 --epochs 80
"""

from __future__ import annotations

import argparse
import functools
import time

import numpy as np

from .self_play import collect_dataset, make_diverse_bot_pair, make_rl_self_play_pair
from .value_net import DEFAULT_WEIGHTS_PATH, ValueNet


def _bot_pair_factory(self_play: str, source_weights):
    if self_play == "baseline":
        return make_diverse_bot_pair
    if self_play == "rl":
        net = ValueNet.load(source_weights)
        print(f"Self-play RL: reseau source charge depuis {source_weights} "
              f"(n_layers={net.n_layers}, hidden_dims={net.hidden_dims})")
        return functools.partial(make_rl_self_play_pair, net=net)
    raise ValueError(f"self_play inconnu: {self_play!r}")


def train(
    n_games: int = 3000,
    epochs: int = 60,
    hidden_dim: int | tuple[int, ...] = 32,
    lr: float = 5e-3,
    batch_size: int = 256,
    val_fraction: float = 0.15,
    seed: int = 0,
    weights_path=DEFAULT_WEIGHTS_PATH,
    self_play: str = "baseline",
    source_weights=DEFAULT_WEIGHTS_PATH,
) -> ValueNet:
    bot_pair_factory = _bot_pair_factory(self_play, source_weights)

    print(f"Self-play ({self_play}): generation de {n_games} parties...")
    t0 = time.time()
    X, y = collect_dataset(n_games=n_games, seed0=seed, bot_pair_factory=bot_pair_factory)
    print(f"  -> {len(X)} exemples en {time.time() - t0:.1f}s")

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(X))
    X, y = X[order], y[order]
    n_val = max(1, int(len(X) * val_fraction))
    X_val, y_val = X[:n_val], y[:n_val]
    X_train, y_train = X[n_val:], y[n_val:]

    net = ValueNet(input_dim=X.shape[1], hidden_dim=hidden_dim, seed=seed)
    net.set_normalization(X_train)

    print(
        f"Entrainement: {len(X_train)} exemples train / {len(X_val)} val, {epochs} epoques, "
        f"hidden_dims={net.hidden_dims}"
    )
    for epoch in range(epochs):
        perm = rng.permutation(len(X_train))
        epoch_loss = 0.0
        n_batches = 0
        for start in range(0, len(X_train), batch_size):
            idx = perm[start : start + batch_size]
            epoch_loss += net.train_step(X_train[idx], y_train[idx], lr=lr)
            n_batches += 1
        val_pred = net.predict(X_val)
        val_mse = float(np.mean((val_pred - y_val) ** 2))
        val_mae = float(np.mean(np.abs(val_pred - y_val)))
        if epoch % 5 == 0 or epoch == epochs - 1:
            print(
                f"  epoque {epoch:3d}  train_loss={epoch_loss / n_batches:7.3f}  "
                f"val_mse={val_mse:7.3f}  val_mae={val_mae:6.3f}"
            )

    net.save(weights_path)
    print(f"Poids sauvegardes dans {weights_path}")
    return net


def main() -> None:
    parser = argparse.ArgumentParser(description="Entraine le reseau de valeur RL par self-play.")
    parser.add_argument("--games", type=int, default=3000)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--hidden", type=int, nargs="+", default=[32], help="tailles des couches cachees, ex: --hidden 64 32")
    parser.add_argument("--lr", type=float, default=5e-3)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--self-play", choices=["baseline", "rl"], default="baseline",
        help="'baseline': Heuristic/Random. 'rl': auto-jeu RLBot vs RLBot avec --source-weights.",
    )
    parser.add_argument(
        "--source-weights", type=str, default=str(DEFAULT_WEIGHTS_PATH),
        help="poids RLBot a utiliser pour generer les parties quand --self-play rl",
    )
    args = parser.parse_args()
    train(
        n_games=args.games,
        epochs=args.epochs,
        hidden_dim=tuple(args.hidden),
        lr=args.lr,
        batch_size=args.batch_size,
        seed=args.seed,
        self_play=args.self_play,
        source_weights=args.source_weights,
    )


if __name__ == "__main__":
    main()
