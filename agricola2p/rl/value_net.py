"""Reseau de valeur minimal (MLP a 1 couche cachee), numpy pur.

V(s) estime score_player(moi) - score_player(adversaire) en fin de partie, a
partir de l'etat courant. Entraine par descente de gradient (MSE) sur des
retours Monte-Carlo issus de parties de self-play (cf self_play.py):
c'est la brique RL "evaluation de politique" -- on apprend a predire le
resultat final d'une politique de jeu donnee a partir d'un etat, sans
modele explicite des transitions.

Volontairement tres simple (pas de torch/autograd): quelques dizaines de
neurones suffisent pour ~60 features d'entree, et ca reste 100% numpy pour
ne pas alourdir les dependances du projet (cf pyproject.toml, extra "rl").
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

DEFAULT_WEIGHTS_PATH = Path(__file__).with_name("weights.npz")


class ValueNet:
    def __init__(self, input_dim: int, hidden_dim: int = 32, seed: int | None = None):
        rng = np.random.default_rng(seed)
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.W1 = rng.standard_normal((input_dim, hidden_dim)) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W2 = rng.standard_normal(hidden_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = 0.0
        # normalisation des features (moyenne/ecart-type), calculee sur le jeu d'entrainement
        self.mean = np.zeros(input_dim)
        self.std = np.ones(input_dim)

    def set_normalization(self, X: np.ndarray) -> None:
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)
        self.std[self.std < 1e-6] = 1.0

    def _forward(self, X: np.ndarray):
        Xn = (X - self.mean) / self.std
        Z1 = Xn @ self.W1 + self.b1
        A1 = np.maximum(Z1, 0.0)  # ReLU
        out = A1 @ self.W2 + self.b2
        return out, Xn, Z1, A1

    def predict(self, X: np.ndarray) -> np.ndarray:
        """X: (input_dim,) ou (N, input_dim) -> valeur(s) predite(s)."""
        single = X.ndim == 1
        out, *_ = self._forward(np.atleast_2d(X))
        return float(out[0]) if single else out

    def train_step(self, X: np.ndarray, y: np.ndarray, lr: float = 1e-3) -> float:
        """1 pas de descente de gradient (MSE) sur un batch (X, y). Retourne la loss."""
        out, Xn, Z1, A1 = self._forward(X)
        n = X.shape[0]
        err = out - y
        loss = float(np.mean(err ** 2))

        d_out = 2.0 * err / n
        dW2 = A1.T @ d_out
        db2 = float(d_out.sum())
        dA1 = np.outer(d_out, self.W2)
        dZ1 = dA1 * (Z1 > 0)
        dW1 = Xn.T @ dZ1
        db1 = dZ1.sum(axis=0)

        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        return loss

    def save(self, path: Path | str = DEFAULT_WEIGHTS_PATH) -> None:
        np.savez(
            path, W1=self.W1, b1=self.b1, W2=self.W2, b2=np.asarray(self.b2),
            mean=self.mean, std=self.std,
        )

    @classmethod
    def load(cls, path: Path | str = DEFAULT_WEIGHTS_PATH) -> "ValueNet":
        data = np.load(path)
        net = cls(input_dim=data["W1"].shape[0], hidden_dim=data["W1"].shape[1])
        net.W1 = data["W1"]
        net.b1 = data["b1"]
        net.W2 = data["W2"]
        net.b2 = float(data["b2"])
        net.mean = data["mean"]
        net.std = data["std"]
        return net
