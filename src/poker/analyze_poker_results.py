"""
Script to analyze poker game results from Firebase.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import argparse
from src.firebase_manager import FirebaseManager
from src.logger import GameLogger, Color


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze poker game results from Firebase."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of games to retrieve",
    )
    return parser.parse_args()


def display_game_results(results, logger):
    """Display game results."""
    if not results:
        logger.print("No poker game results found in Firebase.", Color.YELLOW)
        return

    logger.header(f"FOUND {len(results)} POKER GAMES", Color.CYAN)

    for i, game in enumerate(results[:10]):  # Show only the first 10 games
        logger.header(f"GAME {i+1}", Color.GREEN)
        logger.print(f"Game ID: {game.get('game_id')}")
        logger.print(f"Winner: {game.get('winner')}")
        logger.print(f"Game Type: {game.get('game_type')}")
        logger.print(f"Language: {game.get('language')}")
        logger.print(f"Participants: {len(game.get('participants', {}))} players")

    if len(results) > 10:
        logger.print(f"... and {len(results) - 10} more games", Color.YELLOW)


def display_model_stats(stats, logger):
    """Display model statistics."""
    if not stats:
        logger.print("No model statistics found.", Color.YELLOW)
        return

    logger.header("MODEL STATISTICS", Color.CYAN)

    # Sort models by win rate
    sorted_models = sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True)

    for model, model_stats in sorted_models:
        win_rate = model_stats["win_rate"] * 100
        logger.print(f"{model}:", Color.GREEN)
        logger.print(f"  Games Played: {model_stats['games_played']}")
        logger.print(f"  Games Won: {model_stats['games_won']}")
        logger.print(f"  Win Rate: {win_rate:.2f}%")


def main():
    """Main function to analyze poker game results."""
    # Parse command line arguments
    args = parse_args()

    # Initialize logger
    logger = GameLogger()
    logger.header("POKER GAME ANALYSIS", Color.CYAN)

    # Initialize Firebase
    firebase = FirebaseManager()
    if not firebase.initialized:
        logger.print(
            "Failed to initialize Firebase. Cannot retrieve results.", Color.RED
        )
        return

    # Get poker game results
    results = firebase.get_poker_game_results(limit=args.limit)
    display_game_results(results, logger)

    # Get model statistics
    stats = firebase.get_poker_model_stats()
    display_model_stats(stats, logger)


if __name__ == "__main__":
    main()
