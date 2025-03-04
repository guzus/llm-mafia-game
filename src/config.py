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

# Game settings

# MODELS = FREE_MODELS
MODELS = [
    "google/gemini-2.0-flash-001",
    "google/gemini-flash-1.5",
    "google/gemini-flash-1.5-8b",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "google/gemini-2.0-flash-lite-001",
    "meta-llama/llama-3.1-70b-instruct",
    "deepseek/deepseek-r1",
    "gryphe/mythomax-l2-13b",
    "microsoft/wizardlm-2-8x22b",
    "mistralai/mistral-small-24b-instruct-2501",
    "nousresearch/hermes-3-llama-3.1-405b",
    "minimax/minimax-01",
    "sao10k/l3-euryale-70b",
    "deepseek/deepseek-chat",
    "openai/gpt-4o",
    "anthropic/claude-3.5-sonnet",
    "deepseek/deepseek-r1-distill-llama-70b",
]

FREE_MODELS = [
    "deepseek/deepseek-r1:free",
    "google/gemini-2.0-pro-exp-02-05:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "google/gemini-exp-1206:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
]

# Game configuration
NUM_GAMES = int(os.getenv("NUM_GAMES", 1))  # Number of games to simulate
PLAYERS_PER_GAME = int(
    os.getenv("PLAYERS_PER_GAME", 8)
)  # Number of players in each game
MAFIA_COUNT = int(os.getenv("MAFIA_COUNT", 2))  # Number of Mafia players
DOCTOR_COUNT = int(os.getenv("DOCTOR_COUNT", 1))  # Number of Doctor players
# Villagers will be: PLAYERS_PER_GAME - MAFIA_COUNT - DOCTOR_COUNT

# Game type
GAME_TYPE = "Classic Mafia"  # Type of Mafia game to run

# Language setting
LANGUAGE = os.getenv(
    "GAME_LANGUAGE", "English"
)  # Language for game prompts and interactions (supported: English, Spanish, French, Korean)

# Maximum number of rounds before declaring a draw
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", 20))

# Timeout for API calls (in seconds)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))

# Random seed for reproducibility (set to None for random behavior)
RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)
