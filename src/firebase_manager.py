"""
Firebase manager for the LLM Mafia Game Competition.
"""

import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

# Add flexible import handling
try:
    import src.config as config
except ImportError:
    # When running the script directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config


class FirebaseManager:
    """Manages Firebase database operations for the Mafia game."""

    def __init__(self):
        """Initialize the Firebase manager."""
        try:
            cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.initialized = True
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            self.initialized = False

    def store_game_result(
        self,
        game_id,
        winner,
        participants,
        game_type=config.GAME_TYPE,
        language=config.LANGUAGE,
    ):
        """
        Store the result of a game in Firebase.

        Args:
            game_id (str): Unique identifier for the game.
            winner (str): The winning team ("Mafia" or "Villagers").
            participants (dict): Dictionary mapping model names to roles.
            game_type (str, optional): Type of Mafia game played.
            language (str, optional): Language used for the game.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot store game result.")
            return False

        try:
            # Create game result data
            game_data = {
                "game_id": game_id,
                "timestamp": int(time.time()),
                "game_type": game_type,
                "language": language,
                "participant_count": len(participants),
                "winner": winner,
                "participants": participants,
            }

            # Store in Firebase
            self.db.collection("mafia_games").document(game_id).set(game_data)
            return True
        except Exception as e:
            print(f"Error storing game result: {e}")
            return False

    def store_game_log(
        self,
        game_id,
        rounds,
        participants,
        game_type=config.GAME_TYPE,
        language=config.LANGUAGE,
        critic_review=None,
    ):
        """
        Store the log of a game in Firebase.

        Args:
            game_id (str): Unique identifier for the game.
            rounds (list): List of round data.
            participants (dict): Dictionary mapping model names to roles.
            game_type (str, optional): Type of Mafia game played.
            language (str, optional): Language used for the game.
            critic_review (dict, optional): Game critic review with title and content.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot store game log.")
            return False

        try:
            # Create game log data
            log_data = {
                "game_id": game_id,
                "timestamp": int(time.time()),
                "game_type": game_type,
                "language": language,
                "participant_count": len(participants),
                "rounds": rounds,
            }

            # Add critic review if available
            if critic_review:
                log_data["critic_review"] = critic_review

            # Store in Firebase
            self.db.collection("game_logs").document(game_id).set(log_data)
            return True
        except Exception as e:
            print(f"Error storing game log: {e}")
            return False

    def get_game_results(self, limit=100):
        """
        Get the results of games from Firebase.

        Args:
            limit (int, optional): Maximum number of results to retrieve.

        Returns:
            list: List of game results.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get game results.")
            return []

        try:
            # Query Firestore for game results, ordered by timestamp
            results = (
                self.db.collection("mafia_games")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )

            # Convert to list
            return [doc.to_dict() for doc in results]
        except Exception as e:
            print(f"Error getting game results: {e}")
            return []

    def get_model_stats(self):
        """
        Get statistics for each model from Firebase.

        Returns:
            dict: Dictionary mapping model names to statistics.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get model stats.")
            return {}

        try:
            # Get all game results
            results = self.get_game_results(limit=1000)

            # Initialize stats
            stats = {}

            # Process each game
            for game in results:
                winner = game.get("winner")
                participants = game.get("participants", {})

                for model, role in participants.items():
                    # Initialize model stats if not exists
                    if model not in stats:
                        stats[model] = {
                            "games_played": 0,
                            "games_won": 0,
                            "mafia_games": 0,
                            "mafia_wins": 0,
                            "villager_games": 0,
                            "villager_wins": 0,
                            "doctor_games": 0,
                            "doctor_wins": 0,
                        }

                    # Update games played
                    stats[model]["games_played"] += 1

                    # Update role-specific stats
                    if role == "Mafia":
                        stats[model]["mafia_games"] += 1
                        if winner == "Mafia":
                            stats[model]["mafia_wins"] += 1
                            stats[model]["games_won"] += 1
                    elif role == "Doctor":
                        stats[model]["doctor_games"] += 1
                        if winner == "Villagers":
                            stats[model]["doctor_wins"] += 1
                            stats[model]["games_won"] += 1
                    elif role == "Villager":
                        stats[model]["villager_games"] += 1
                        if winner == "Villagers":
                            stats[model]["villager_wins"] += 1
                            stats[model]["games_won"] += 1

            # Calculate win rates
            for model in stats:
                stats[model]["win_rate"] = (
                    stats[model]["games_won"] / stats[model]["games_played"]
                    if stats[model]["games_played"] > 0
                    else 0
                )
                stats[model]["mafia_win_rate"] = (
                    stats[model]["mafia_wins"] / stats[model]["mafia_games"]
                    if stats[model]["mafia_games"] > 0
                    else 0
                )
                stats[model]["villager_win_rate"] = (
                    stats[model]["villager_wins"] / stats[model]["villager_games"]
                    if stats[model]["villager_games"] > 0
                    else 0
                )
                stats[model]["doctor_win_rate"] = (
                    stats[model]["doctor_wins"] / stats[model]["doctor_games"]
                    if stats[model]["doctor_games"] > 0
                    else 0
                )

            return stats
        except Exception as e:
            print(f"Error getting model stats: {e}")
            return {}

    def get_game_log(self, game_id):
        """
        Get the log of a specific game from Firebase.

        Args:
            game_id (str): Unique identifier for the game.

        Returns:
            dict: Game log data including rounds and participant information.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get game log.")
            return None

        try:
            # Get game log from Firestore
            log_doc = self.db.collection("game_logs").document(game_id).get()

            if not log_doc.exists:
                print(f"Game log not found for game ID: {game_id}")
                return None

            log_data = log_doc.to_dict()

            # Get game result to include participant roles
            result_doc = self.db.collection("mafia_games").document(game_id).get()

            if result_doc.exists:
                result_data = result_doc.to_dict()
                log_data["participants"] = result_data.get("participants", {})
                log_data["winner"] = result_data.get("winner", "Unknown")

            return log_data
        except Exception as e:
            print(f"Error getting game log: {e}")
            return None
