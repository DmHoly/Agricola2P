"""Generation de donnees d'entrainement par self-play.

Fait jouer des parties completes avec des bots existants (RandomBot,
HeuristicBot, melanges avec de l'exploration aleatoire) et enregistre, a
chaque decision, (etat encode, retour final = score(moi) - score(adversaire)
en fin de partie). C'est une evaluation de politique par methode Monte-Carlo:
le reseau de valeur apprend a predire ce retour a partir de l'etat seul.
"""

from __future__ import annotations

import random

import numpy as np

from ..bots.base import Bot
from ..bots.heuristic_bot import HeuristicBot
from ..bots.random_bot import RandomBot
from ..engine.actions import Action
from ..engine.game import AgricolaGame
from .features import encode


class EpsilonGreedyWrapper(Bot):
    """Joue comme `bot`, sauf une fraction `epsilon` des coups tires au hasard
    -- diversifie les etats visites pendant le self-play (sans quoi 2 bots
    deterministes rejouent toujours des trajectoires tres similaires)."""

    name = "epsilon_wrapped"

    def __init__(self, bot: Bot, epsilon: float, seed: int | None = None):
        self.bot = bot
        self.epsilon = epsilon
        self.rng = random.Random(seed)

    def choose_action(self, game: AgricolaGame, player_idx: int) -> Action:
        if self.rng.random() < self.epsilon:
            return self.rng.choice(game.legal_actions())
        return self.bot.choose_action(game, player_idx)


def play_episode(bot0: Bot, bot1: Bot, seed: int) -> list[tuple[np.ndarray, float]]:
    """Joue 1 partie complete et retourne la liste (features, retour final)
    pour chaque decision prise par l'un ou l'autre joueur."""
    game = AgricolaGame.new_game(seed=seed)
    bots = [bot0, bot1]
    frames: list[tuple[np.ndarray, int]] = []

    while not game.is_terminal():
        idx = game.current_player_idx
        feats = encode(game.state, idx)
        action = bots[idx].choose_action(game, idx)
        frames.append((feats, idx))
        game.apply(action)

    scores = game.scores()
    return [(feats, scores[idx] - scores[1 - idx]) for feats, idx in frames]


def make_diverse_bot_pair(seed: int, epsilon: float = 0.15) -> tuple[Bot, Bot]:
    """Alterne quelques profils d'adversaires pour eviter que les parties de
    self-play se ressemblent toutes (memes ouvertures, memes plateaux)."""
    rng = random.Random(seed)
    choice = rng.random()
    if choice < 0.6:
        base0, base1 = HeuristicBot(seed=seed), HeuristicBot(seed=seed + 1)
    elif choice < 0.85:
        base0, base1 = HeuristicBot(seed=seed), RandomBot(seed=seed + 1)
    else:
        base0, base1 = RandomBot(seed=seed), RandomBot(seed=seed + 1)
    return (
        EpsilonGreedyWrapper(base0, epsilon, seed=seed * 2),
        EpsilonGreedyWrapper(base1, epsilon, seed=seed * 2 + 1),
    )


def make_rl_self_play_pair(seed: int, epsilon: float, net, opponent_mix: float = 0.25) -> tuple[Bot, Bot]:
    """Auto-jeu RLBot vs RLBot avec les poids courants (`net`, partage entre
    les 2 joueurs pour eviter de relire le fichier a chaque partie).

    Une fraction `opponent_mix` des parties oppose le RLBot courant a un
    sparring-partner fixe (Heuristic/Random) plutot qu'a lui-meme: le
    self-play pur tend a converger vers une strategie etroite que seul
    RLBot-contre-lui-meme sait "battre", et qui peut s'averer fragile face a
    un style de jeu different -- garder un peu de diversite d'adversaires
    limite ce risque de sur-specialisation.
    """
    from ..bots.rl_bot import RLBot

    rng = random.Random(seed)
    rl0 = RLBot(net=net, seed=seed)
    if rng.random() < opponent_mix:
        base1 = HeuristicBot(seed=seed + 1) if rng.random() < 0.5 else RandomBot(seed=seed + 1)
    else:
        base1 = RLBot(net=net, seed=seed + 1)
    return (
        EpsilonGreedyWrapper(rl0, epsilon, seed=seed * 2),
        EpsilonGreedyWrapper(base1, epsilon, seed=seed * 2 + 1),
    )


def collect_dataset(
    n_games: int, seed0: int = 0, epsilon: float = 0.15, bot_pair_factory=make_diverse_bot_pair
) -> tuple[np.ndarray, np.ndarray]:
    """`bot_pair_factory(seed, epsilon) -> (bot0, bot1)`. Par defaut,
    melange Heuristic/Random (cf make_diverse_bot_pair); passer par exemple
    `functools.partial(make_rl_self_play_pair, net=mon_reseau)` pour du
    self-play RLBot vs RLBot avec un reseau deja charge."""
    X: list[np.ndarray] = []
    y: list[float] = []
    for i in range(n_games):
        seed = seed0 + i
        bot0, bot1 = bot_pair_factory(seed, epsilon)
        for feats, target in play_episode(bot0, bot1, seed=seed):
            X.append(feats)
            y.append(target)
    return np.asarray(X), np.asarray(y)
