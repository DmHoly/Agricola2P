"""Entraine le reseau de valeur par self-play et sauve les poids.

Usage:
    python3 -m agricola2p.rl.train --games 3000 --epochs 60
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from .self_play import collect_dataset
from .value_net import DEFAULT_WEIGHTS_PATH, ValueNet


def train(
    n_games: int = 3000,
    epochs: int = 60,
    hidden_dim: int = 32,
    lr: float = 5e-3,
    batch_size: int = 256,
    val_fraction: float = 0.15,
    seed: int = 0,
    weights_path=DEFAULT_WEIGHTS_PATH,
) -> ValueNet:
    print(f"Self-play: generation de {n_games} parties...")
    t0 = time.time()
    X, y = collect_dataset(n_games=n_games, seed0=seed)
    print(f"  -> {len(X)} exemples en {time.time() - t0:.1f}s")

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(X))
    X, y = X[order], y[order]
    n_val = max(1, int(len(X) * val_fraction))
    X_val, y_val = X[:n_val], y[:n_val]
    X_train, y_train = X[n_val:], y[n_val:]

    net = ValueNet(input_dim=X.shape[1], hidden_dim=hidden_dim, seed=seed)
    net.set_normalization(X_train)

    print(f"Entrainement: {len(X_train)} exemples train / {len(X_val)} val, {epochs} epoques")
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
    parser.add_argument("--hidden", type=int, default=32)
    parser.add_argument("--lr", type=float, default=5e-3)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    train(
        n_games=args.games,
        epochs=args.epochs,
        hidden_dim=args.hidden,
        lr=args.lr,
        batch_size=args.batch_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
