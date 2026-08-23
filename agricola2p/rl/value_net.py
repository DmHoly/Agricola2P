"""Reseau de valeur (MLP a N couches cachees), numpy pur.

V(s) estime score_player(moi) - score_player(adversaire) en fin de partie, a
partir de l'etat courant. Entraine par descente de gradient (MSE) sur des
retours Monte-Carlo issus de parties de self-play (cf self_play.py):
c'est la brique RL "evaluation de politique" -- on apprend a predire le
resultat final d'une politique de jeu donnee a partir d'un etat, sans
modele explicite des transitions.

Volontairement tres simple (pas de torch/autograd): une poignee de couches
de quelques dizaines de neurones suffit pour ~60 features d'entree, et ca
reste 100% numpy pour ne pas alourdir les dependances du projet (cf
pyproject.toml, extra "rl").
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

DEFAULT_WEIGHTS_PATH = Path(__file__).with_name("weights.npz")


class ValueNet:
    def __init__(self, input_dim: int, hidden_dim: int | tuple[int, ...] = 32, seed: int | None = None):
        """`hidden_dim`: taille d'une seule couche cachee (int) ou tuple des
        tailles de plusieurs couches cachees successives, ex. (64, 32) pour
        un reseau plus profond que le defaut a 1 couche.
        """
        self.input_dim = input_dim
        self.hidden_dims: tuple[int, ...] = (hidden_dim,) if isinstance(hidden_dim, int) else tuple(hidden_dim)

        dims = [input_dim, *self.hidden_dims, 1]
        rng = np.random.default_rng(seed)
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        for d_in, d_out in zip(dims[:-1], dims[1:]):
            self.weights.append(rng.standard_normal((d_in, d_out)) * np.sqrt(2.0 / d_in))
            self.biases.append(np.zeros(d_out))

        # normalisation des features (moyenne/ecart-type), calculee sur le jeu d'entrainement
        self.mean = np.zeros(input_dim)
        self.std = np.ones(input_dim)

    @property
    def n_layers(self) -> int:
        return len(self.weights)

    def set_normalization(self, X: np.ndarray) -> None:
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)
        self.std[self.std < 1e-6] = 1.0

    def _forward(self, X: np.ndarray):
        Xn = (X - self.mean) / self.std
        activations = [Xn]  # activations[i] = entree de la couche i
        zs = []  # zs[i] = pre-activation de la couche i
        A = Xn
        last = self.n_layers - 1
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            Z = A @ W + b
            zs.append(Z)
            A = Z if i == last else np.maximum(Z, 0.0)  # lineaire en sortie, ReLU ailleurs
            activations.append(A)
        out = A[:, 0]
        return out, activations, zs

    def predict(self, X: np.ndarray) -> np.ndarray | float:
        """X: (input_dim,) ou (N, input_dim) -> valeur(s) predite(s)."""
        single = X.ndim == 1
        out, *_ = self._forward(np.atleast_2d(X))
        return float(out[0]) if single else out

    def train_step(self, X: np.ndarray, y: np.ndarray, lr: float = 1e-3) -> float:
        """1 pas de descente de gradient (MSE) sur un batch (X, y). Retourne la loss."""
        out, activations, zs = self._forward(X)
        n = X.shape[0]
        err = out - y
        loss = float(np.mean(err ** 2))

        last = self.n_layers - 1
        dA = (2.0 * err / n).reshape(-1, 1)
        grads_W: list[np.ndarray | None] = [None] * self.n_layers
        grads_b: list[np.ndarray | None] = [None] * self.n_layers

        for i in reversed(range(self.n_layers)):
            dZ = dA if i == last else dA * (zs[i] > 0)
            A_prev = activations[i]
            grads_W[i] = A_prev.T @ dZ
            grads_b[i] = dZ.sum(axis=0)
            if i > 0:
                dA = dZ @ self.weights[i].T

        for i in range(self.n_layers):
            self.weights[i] -= lr * grads_W[i]
            self.biases[i] -= lr * grads_b[i]

        return loss

    def save(self, path: Path | str = DEFAULT_WEIGHTS_PATH) -> None:
        data = {"n_layers": np.asarray(self.n_layers), "mean": self.mean, "std": self.std}
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            data[f"W{i}"] = W
            data[f"b{i}"] = b
        np.savez(path, **data)

    @classmethod
    def load(cls, path: Path | str = DEFAULT_WEIGHTS_PATH) -> "ValueNet":
        data = np.load(path)
        n_layers = int(data["n_layers"])
        weights = [data[f"W{i}"] for i in range(n_layers)]
        biases = [data[f"b{i}"] for i in range(n_layers)]
        hidden_dims = tuple(w.shape[1] for w in weights[:-1])
        net = cls(input_dim=weights[0].shape[0], hidden_dim=hidden_dims or (weights[0].shape[1],), seed=0)
        net.weights = weights
        net.biases = biases
        net.mean = data["mean"]
        net.std = data["std"]
        return net
