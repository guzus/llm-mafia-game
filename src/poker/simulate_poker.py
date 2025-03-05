"""
Script to simulate poker games between LLMs.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from src.poker.poker_game import PokerGame
import src.poker.poker_config as config
from src.logger import GameLogger, Color


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Simulate poker games between LLMs.")
    parser.add_argument(
        "--num_games",
        type=int,
        default=config.NUM_GAMES,
        help="Number of games to simulate",
    )
    parser.add_argument(
        "--players",
        type=int,
        default=config.PLAYERS_PER_GAME,
        help="Number of players per game",
    )
    parser.add_argument(
        "--starting_chips",
        type=int,
        default=config.STARTING_CHIPS,
        help="Starting chips for each player",
    )
    parser.add_argument(
        "--small_blind", type=int, default=config.SMALL_BLIND, help="Small blind amount"
    )
    parser.add_argument(
        "--big_blind", type=int, default=config.BIG_BLIND, help="Big blind amount"
    )
    parser.add_argument(
        "--max_rounds",
        type=int,
        default=config.MAX_ROUNDS,
        help="Maximum number of rounds",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=config.LANGUAGE,
        help="Language for game prompts",
    )
    parser.add_argument(
        "--free_models", action="store_true", help="Use free models for testing"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="poker_results.json",
        help="Output file for game results",
    )
    return parser.parse_args()


def update_config(args):
    """Update configuration with command line arguments."""
    config.NUM_GAMES = args.num_games
    config.PLAYERS_PER_GAME = args.players
    config.STARTING_CHIPS = args.starting_chips
    config.SMALL_BLIND = args.small_blind
    config.BIG_BLIND = args.big_blind
    config.MAX_ROUNDS = args.max_rounds
    config.LANGUAGE = args.language

    # Use free models if specified
    if args.free_models:
        config.MODELS = config.FREE_MODELS


def save_results(results, output_file):
    """Save game results to a file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)


def main():
    """Main function to run the simulation."""
    # Parse command line arguments
    args = parse_args()

    # Update configuration
    update_config(args)

    # Initialize logger
    logger = GameLogger()
    logger.header("POKER GAME SIMULATION", Color.CYAN)
    logger.print(f"Number of games: {config.NUM_GAMES}")
    logger.print(f"Players per game: {config.PLAYERS_PER_GAME}")
    logger.print(f"Starting chips: {config.STARTING_CHIPS}")
    logger.print(f"Small blind: {config.SMALL_BLIND}")
    logger.print(f"Big blind: {config.BIG_BLIND}")
    logger.print(f"Maximum rounds: {config.MAX_ROUNDS}")
    logger.print(f"Language: {config.LANGUAGE}")
    logger.print(
        f"Models: {', '.join(config.MODELS[:5])}{'...' if len(config.MODELS) > 5 else ''}"
    )

    # Run games
    all_results = []
    for i in range(config.NUM_GAMES):
        logger.header(f"GAME {i+1}/{config.NUM_GAMES}", Color.GREEN)

        # Create and run a poker game
        game = PokerGame(language=config.LANGUAGE)
        results = game.run_game()

        # Add timestamp to results
        results["timestamp"] = datetime.now().isoformat()

        # Add results to all_results
        all_results.append(results)

    # Save results
    save_results(all_results, args.output)
    logger.print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
