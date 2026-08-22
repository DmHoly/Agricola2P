"""CLI simple: fait jouer deux bots l'un contre l'autre et affiche le resultat.

Usage:
    python -m agricola2p.cli --p1 heuristic --p2 mcts --iterations 200 --seed 1
"""

from __future__ import annotations

import argparse

from .bots.base import Bot
from .bots.heuristic_bot import HeuristicBot
from .bots.mcts_bot import MCTSBot
from .bots.random_bot import RandomBot
from .engine.game import AgricolaGame

def _make_rl_bot(seed, iterations):
    from .bots.rl_bot import RLBot

    return RLBot(seed=seed)


def _make_mcts_rl_bot(seed, iterations):
    from .rl.mcts_value_fn import load_value_fn

    return MCTSBot(iterations=iterations, seed=seed, value_fn=load_value_fn())


BOT_FACTORIES = {
    "random": lambda seed, iterations: RandomBot(seed=seed),
    "heuristic": lambda seed, iterations: HeuristicBot(seed=seed),
    "mcts": lambda seed, iterations: MCTSBot(iterations=iterations, seed=seed),
    "rl": _make_rl_bot,
    "mcts_rl": _make_mcts_rl_bot,
}


def make_bot(name: str, seed: int | None, iterations: int) -> Bot:
    if name not in BOT_FACTORIES:
        raise SystemExit(f"Bot inconnu: {name!r}. Choix possibles: {list(BOT_FACTORIES)}")
    return BOT_FACTORIES[name](seed, iterations)


def play_game(bot0: Bot, bot1: Bot, seed: int | None = None, verbose: bool = True) -> list[int]:
    game = AgricolaGame.new_game(("P1", "P2"), seed=seed)
    bots = [bot0, bot1]
    while not game.is_terminal():
        idx = game.current_player_idx
        action = bots[idx].choose_action(game, idx)
        if verbose:
            print(f"Round {game.state.round_no:2d} | {game.state.players[idx].name} ({bots[idx].name}) -> {action}")
        game.apply(action)

    scores = game.scores()
    if verbose:
        print("\n=== Partie terminee ===")
        for player, score in zip(game.state.players, scores):
            print(f"{player.name}: {score} points")
        winner = game.winner()
        if winner is None:
            print("Egalite !")
        else:
            print(f"Vainqueur: {game.state.players[winner].name}")
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Fait jouer deux bots l'un contre l'autre.")
    parser.add_argument("--p1", default="heuristic", choices=list(BOT_FACTORIES))
    parser.add_argument("--p2", default="mcts", choices=list(BOT_FACTORIES))
    parser.add_argument("--iterations", type=int, default=200, help="Iterations MCTS")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    bot0 = make_bot(args.p1, args.seed, args.iterations)
    bot1 = make_bot(args.p2, args.seed, args.iterations)
    play_game(bot0, bot1, seed=args.seed)


if __name__ == "__main__":
    main()
