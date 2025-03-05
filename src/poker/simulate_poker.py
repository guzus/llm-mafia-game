"""
Script to simulate poker games between LLMs.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import argparse
from datetime import datetime
from poker_game import PokerGame
import poker_config as config
from src.logger import GameLogger, Color
from src.firebase_manager import FirebaseManager


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


def save_to_firebase(game_result, firebase):
    """
    Save poker game results to Firebase.

    Args:
        game_result (dict): The poker game result data
        firebase (FirebaseManager): Initialized Firebase manager

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        game_id = game_result["game_id"]

        # Create participants dictionary mapping model names to their role (in poker, just "Player")
        participants = {model: "Player" for model in game_result["player_chips"].keys()}

        # Store game result in Firebase using poker-specific methods
        firebase.store_poker_game_result(
            game_id=game_id,
            winner=game_result["overall_winner"],
            participants=participants,
            game_type=config.GAME_TYPE,
            language=config.LANGUAGE,
        )

        # Store game log (hand results) in Firebase using poker-specific methods
        firebase.store_poker_game_log(
            game_id=game_id,
            hands=game_result["hand_results"],
            participants=participants,
            game_type=config.GAME_TYPE,
            language=config.LANGUAGE,
        )

        return True
    except Exception as e:
        print(f"Error storing game result in Firebase: {e}")
        return False


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

    # Initialize Firebase if saving to Firebase
    firebase = FirebaseManager()
    if firebase.initialized:
        logger.print(
            "Firebase initialized successfully for storing results", Color.GREEN
        )
    else:
        logger.print(
            "Failed to initialize Firebase. Results will only be saved locally.",
            Color.RED,
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

        # Save to Firebase if enabled
        if save_to_firebase(results, firebase):
            logger.print(f"Game {i+1} results saved to Firebase", Color.GREEN)
        else:
            logger.print(f"Failed to save game {i+1} results to Firebase", Color.RED)

    # Save results locally
    save_results(all_results, args.output)
    logger.print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
