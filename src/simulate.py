"""
Simulation script for the LLM Mafia Game Competition.
"""

import time
import random
import concurrent.futures
from collections import defaultdict
import argparse
import config
from game import MafiaGame
from firebase_manager import FirebaseManager
from logger import GameLogger, Color


def run_single_game(game_number, language=None, models=None):
    """
    Run a single Mafia game.

    Args:
        game_number (int): The game number.
        language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.
        models (list, optional): List of model names to use as players. Defaults to config.MODELS.

    Returns:
        tuple: (game_number, winner, rounds_data, participants, game_id, language, critic_review)
    """
    game = MafiaGame(models=models, language=language)
    winner, rounds_data, participants, language, critic_review = game.run_game()
    return (
        game_number,
        winner,
        rounds_data,
        participants,
        game.game_id,
        language,
        critic_review,
    )


def run_simulation(
    num_games=config.NUM_GAMES, parallel=False, max_workers=4, language=None, models=None
):
    """
    Run multiple Mafia games and store results.

    Args:
        num_games (int, optional): Number of games to run.
        parallel (bool, optional): Whether to run games in parallel.
        max_workers (int, optional): Maximum number of worker threads.
        language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.
        models (list, optional): List of model names to use as players. Defaults to config.MODELS.

    Returns:
        dict: Statistics about the games.
    """
    # Initialize logger
    logger = GameLogger()
    logger.header(f"STARTING SIMULATION WITH {num_games} GAMES", Color.BRIGHT_MAGENTA)

    start_time = time.time()

    # Initialize Firebase
    firebase = FirebaseManager()

    # Initialize statistics
    stats = {
        "total_games": num_games,
        "completed_games": 0,
        "mafia_wins": 0,
        "villager_wins": 0,
        "model_stats": defaultdict(
            lambda: {
                "games": 0,
                "wins": 0,
                "mafia_games": 0,
                "mafia_wins": 0,
                "villager_games": 0,
                "villager_wins": 0,
                "doctor_games": 0,
                "doctor_wins": 0,
            }
        ),
    }

    # Use the provided language or default from config
    game_language = language if language is not None else config.LANGUAGE

    if parallel and num_games > 1:
        # Run games in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all games
            future_to_game = {
                executor.submit(run_single_game, i, game_language, models): i
                for i in range(1, num_games + 1)
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_game):
                game_number = future_to_game[future]
                try:
                    (
                        game_number,
                        winner,
                        rounds_data,
                        participants,
                        game_id,
                        language,
                        critic_review,
                    ) = future.result()

                    # Store results in Firebase
                    if firebase.initialized:
                        firebase.store_game_result(
                            game_id, winner, participants, language=language
                        )
                        firebase.store_game_log(
                            game_id,
                            rounds_data,
                            participants,
                            language=language,
                            critic_review=critic_review,
                        )

                    # Update statistics
                    stats["completed_games"] += 1
                    if winner == "Mafia":
                        stats["mafia_wins"] += 1
                    else:
                        stats["villager_wins"] += 1

                    # Update model statistics
                    for player_name, role_data in participants.items():
                        # Handle both old and new format
                        if isinstance(role_data, dict):
                            role = role_data.get("role")
                            model = role_data.get(
                                "model_name", player_name
                            )  # Use player_name as fallback
                        else:
                            # Legacy format where role_data is just the role string
                            role = role_data
                            model = player_name  # In legacy format, the key was the model name

                        stats["model_stats"][model]["games"] += 1

                        if role == "Mafia":
                            stats["model_stats"][model]["mafia_games"] += 1
                            if winner == "Mafia":
                                stats["model_stats"][model]["mafia_wins"] += 1
                                stats["model_stats"][model]["wins"] += 1
                        elif role == "Doctor":
                            stats["model_stats"][model]["doctor_games"] += 1
                            if winner == "Villagers":
                                stats["model_stats"][model]["doctor_wins"] += 1
                                stats["model_stats"][model]["wins"] += 1
                        else:  # Villager
                            stats["model_stats"][model]["villager_games"] += 1
                            if winner == "Villagers":
                                stats["model_stats"][model]["villager_wins"] += 1
                                stats["model_stats"][model]["wins"] += 1

                    # Log game completion
                    win_color = Color.RED if winner == "Mafia" else Color.GREEN
                    logger.print(
                        f"Game {game_number} completed. Winner: {winner}",
                        win_color,
                        bold=True,
                    )

                except Exception as e:
                    logger.error(f"Game {game_number} generated an exception: {e}")
    else:
        # Run games sequentially
        for i in range(1, num_games + 1):
            game_number = i  # Define game_number at the start of each iteration
            try:
                (
                    game_number,
                    winner,
                    rounds_data,
                    participants,
                    game_id,
                    language,
                    critic_review,
                ) = run_single_game(i, game_language, models)

                # Store results in Firebase
                if firebase.initialized:
                    firebase.store_game_result(
                        game_id, winner, participants, language=language
                    )
                    firebase.store_game_log(
                        game_id,
                        rounds_data,
                        participants,
                        language=language,
                        critic_review=critic_review,
                    )

                # Update statistics
                stats["completed_games"] += 1
                if winner == "Mafia":
                    stats["mafia_wins"] += 1
                else:
                    stats["villager_wins"] += 1

                # Update model statistics
                for player_name, role_data in participants.items():
                    # Handle both old and new format
                    if isinstance(role_data, dict):
                        role = role_data.get("role")
                        model = role_data.get(
                            "model_name", player_name
                        )  # Use player_name as fallback
                    else:
                        # Legacy format where role_data is just the role string
                        role = role_data
                        model = (
                            player_name  # In legacy format, the key was the model name
                        )

                    stats["model_stats"][model]["games"] += 1

                    if role == "Mafia":
                        stats["model_stats"][model]["mafia_games"] += 1
                        if winner == "Mafia":
                            stats["model_stats"][model]["mafia_wins"] += 1
                            stats["model_stats"][model]["wins"] += 1
                    elif role == "Doctor":
                        stats["model_stats"][model]["doctor_games"] += 1
                        if winner == "Villagers":
                            stats["model_stats"][model]["doctor_wins"] += 1
                            stats["model_stats"][model]["wins"] += 1
                    else:  # Villager
                        stats["model_stats"][model]["villager_games"] += 1
                        if winner == "Villagers":
                            stats["model_stats"][model]["villager_wins"] += 1
                            stats["model_stats"][model]["wins"] += 1

                # Log game completion
                win_color = Color.RED if winner == "Mafia" else Color.GREEN
                logger.print(
                    f"Game {game_number} completed. Winner: {winner}",
                    win_color,
                    bold=True,
                )

            except Exception as e:
                logger.error(f"Game {game_number} generated an exception: {e}")

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    stats["elapsed_time"] = elapsed_time

    # Log statistics using our logger
    logger.stats(stats)

    return stats


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LLM Mafia Game Simulation")
    parser.add_argument(
        "--free-models",
        action="store_true",
        help="Use only free OpenRouter models for the simulation"
    )
    parser.add_argument(
        "--ollama",
        action="store_true",
        help="Use Ollama models for the simulation"
    )
    parser.add_argument(
        "--num-games",
        type=int,
        default=config.NUM_GAMES,
        help=f"Number of games to simulate (default: {config.NUM_GAMES})"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run games in parallel for faster execution"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of worker threads for parallel execution (default: 4)"
    )
    
    args = parser.parse_args()
    
    # Set random seed if specified
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)

    # Validate arguments
    if args.free_models and args.ollama:
        print("Error: Cannot use both --free-models and --ollama flags together")
        exit(1)
    
    # Select models based on arguments
    if args.free_models:
        models = config.FREE_MODELS
    elif args.ollama:
        models = config.OLLAMA_MODELS
    else:
        models = None
    
    # Log which models are being used
    logger = GameLogger()
    if args.free_models:
        logger.print(f"Using free OpenRouter models only: {len(config.FREE_MODELS)} models available", Color.CYAN, bold=True)
    elif args.ollama:
        logger.print(f"Using Ollama models only: {len(config.OLLAMA_MODELS)} models available", Color.CYAN, bold=True)
    else:
        logger.print(f"Using all OpenRouter models: {len(config.MODELS)} models available", Color.CYAN, bold=True)

    # Run simulation
    run_simulation(
        num_games=args.num_games,
        parallel=args.parallel,
        max_workers=args.max_workers,
        models=models
    )
