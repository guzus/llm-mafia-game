"""
Configuration settings for the LLM Mafia Game Competition.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Firebase settings
FIREBASE_CREDENTIALS_PATH = (
    "firebase_credentials.json"  # Path to your Firebase credentials file
)
FIREBASE_DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL", "https://your-project-id.firebaseio.com/"
)

# Game settings
MODELS = [
    "openai/gpt-4-turbo",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "google/gemini-pro",
    "mistralai/mistral-large",
    "meta-llama/llama-3-70b-instruct",
]

# Game configuration
NUM_GAMES = int(os.getenv("NUM_GAMES", 100))  # Number of games to simulate
PLAYERS_PER_GAME = int(
    os.getenv("PLAYERS_PER_GAME", 7)
)  # Number of players in each game
MAFIA_COUNT = int(os.getenv("MAFIA_COUNT", 2))  # Number of Mafia players
DOCTOR_COUNT = int(os.getenv("DOCTOR_COUNT", 1))  # Number of Doctor players
# Villagers will be: PLAYERS_PER_GAME - MAFIA_COUNT - DOCTOR_COUNT

# Game type
GAME_TYPE = "Classic Mafia"  # Type of Mafia game to run

# Maximum number of rounds before declaring a draw
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", 20))

# Timeout for API calls (in seconds)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))

# Random seed for reproducibility (set to None for random behavior)
RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)
