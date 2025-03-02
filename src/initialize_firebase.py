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
            "participants": {
                "openai/gpt-4-turbo": "Mafia",
                "anthropic/claude-3-opus": "Villager",
                "anthropic/claude-3-sonnet": "Villager",
                "google/gemini-pro": "Villager",
                "mistralai/mistral-large": "Doctor",
                "meta-llama/llama-3-70b-instruct": "Villager",
                "anthropic/claude-3-haiku": "Villager",
            },
        },
        {
            "game_id": str(uuid.uuid4()),
            "winner": "Villagers",
            "participants": {
                "openai/gpt-4-turbo": "Villager",
                "anthropic/claude-3-opus": "Mafia",
                "anthropic/claude-3-sonnet": "Doctor",
                "google/gemini-pro": "Villager",
                "mistralai/mistral-large": "Villager",
                "meta-llama/llama-3-70b-instruct": "Mafia",
                "anthropic/claude-3-haiku": "Villager",
            },
        },
        {
            "game_id": str(uuid.uuid4()),
            "winner": "Villagers",
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
            game["game_id"], game["winner"], game["participants"]
        ):
            success_count += 1
            print(f"Successfully stored game {game['game_id']}")
            # Add a small delay to ensure different timestamps
            time.sleep(1)

    print(f"Successfully initialized database with {success_count} sample games.")
    return success_count == len(sample_games)


if __name__ == "__main__":
    initialize_database()
