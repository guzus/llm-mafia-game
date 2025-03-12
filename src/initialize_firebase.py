"""
Initialize Firebase database with sample game data.
"""

import time
import uuid
from firebase_manager import FirebaseManager


def initialize_database():
    """Initialize the Firebase database with sample game data."""
    firebase = FirebaseManager()

    if not firebase.initialized:
        print("Firebase not initialized. Cannot initialize database.")
        return False

    # Create sample game data
    sample_games = [
        {
            "game_id": str(uuid.uuid4()),
            "winner": "Mafia",
            "language": "English",
            "participants": {
                "Alex": {
                    "role": "Mafia",
                    "model_name": "openai/gpt-4-turbo",
                    "player_name": "Alex",
                },
                "Bailey": {
                    "role": "Villager",
                    "model_name": "anthropic/claude-3-opus",
                    "player_name": "Bailey",
                },
                "Casey": {
                    "role": "Villager",
                    "model_name": "anthropic/claude-3-sonnet",
                    "player_name": "Casey",
                },
                "Dana": {
                    "role": "Villager",
                    "model_name": "google/gemini-pro",
                    "player_name": "Dana",
                },
                "Ellis": {
                    "role": "Doctor",
                    "model_name": "mistralai/mistral-large",
                    "player_name": "Ellis",
                },
                "Finley": {
                    "role": "Villager",
                    "model_name": "meta-llama/llama-3-70b-instruct",
                    "player_name": "Finley",
                },
                "Gray": {
                    "role": "Villager",
                    "model_name": "anthropic/claude-3-haiku",
                    "player_name": "Gray",
                },
            },
        },
        {
            "game_id": str(uuid.uuid4()),
            "winner": "Villagers",
            "language": "English",
            "participants": {
                "Harper": {
                    "role": "Villager",
                    "model_name": "openai/gpt-4-turbo",
                    "player_name": "Harper",
                },
                "Indigo": {
                    "role": "Mafia",
                    "model_name": "anthropic/claude-3-opus",
                    "player_name": "Indigo",
                },
                "Jordan": {
                    "role": "Doctor",
                    "model_name": "anthropic/claude-3-sonnet",
                    "player_name": "Jordan",
                },
                "Kennedy": {
                    "role": "Villager",
                    "model_name": "google/gemini-pro",
                    "player_name": "Kennedy",
                },
                "Logan": {
                    "role": "Villager",
                    "model_name": "mistralai/mistral-large",
                    "player_name": "Logan",
                },
                "Morgan": {
                    "role": "Mafia",
                    "model_name": "meta-llama/llama-3-70b-instruct",
                    "player_name": "Morgan",
                },
                "Nico": {
                    "role": "Villager",
                    "model_name": "anthropic/claude-3-haiku",
                    "player_name": "Nico",
                },
            },
        },
        {
            "game_id": str(uuid.uuid4()),
            "winner": "Villagers",
            "language": "English",
            "participants": {
                "openai/gpt-4-turbo": "Doctor",
                "anthropic/claude-3-opus": "Villager",
                "anthropic/claude-3-sonnet": "Mafia",
                "google/gemini-pro": "Mafia",
                "mistralai/mistral-large": "Villager",
                "meta-llama/llama-3-70b-instruct": "Villager",
                "anthropic/claude-3-haiku": "Villager",
            },
        },
    ]

    # Store sample games in Firebase
    success_count = 0
    for game in sample_games:
        if firebase.store_game_result(
            game["game_id"],
            game["winner"],
            game["participants"],
            language=game["language"],
        ):
            success_count += 1
            print(f"Successfully stored game {game['game_id']}")
            # Add a small delay to ensure different timestamps
            time.sleep(1)

    print(f"Successfully initialized database with {success_count} sample games.")
    return success_count == len(sample_games)


if __name__ == "__main__":
    initialize_database()
