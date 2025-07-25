"""
Simulation script for the LLM Mafia Game Competition.
"""

import time
import random
import concurrent.futures
from collections import defaultdict
import config
from core.game import MafiaGame
from firebase_manager import FirebaseManager
from utils.logger import GameLogger
from models.enums import Color


def run_single_game(game_number, language=None):
    """
    Run a single Mafia game.

    Args:
        game_number (int): The game number.
        language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.

    Returns:
        tuple: (game_number, winner, rounds_data, participants, game_id, language, critic_review)
    """
    game = MafiaGame(language=language)
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
    num_games=config.NUM_GAMES, parallel=False, max_workers=4, language=None
):
    """
    Run multiple Mafia games and store results.

    Args:
        num_games (int, optional): Number of games to run.
        parallel (bool, optional): Whether to run games in parallel.
        max_workers (int, optional): Maximum number of worker threads.
        language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.

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
                executor.submit(run_single_game, i, game_language): i
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
                ) = run_single_game(i, game_language)

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
    # Set random seed if specified
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)

    # Run simulation
    run_simulation(num_games=config.NUM_GAMES)
