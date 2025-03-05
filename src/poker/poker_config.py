"""
Configuration settings for the LLM Poker Game.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Game settings
MODELS = [
    "google/gemini-2.0-flash-001",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3.7-sonnet",
    "google/gemini-2.0-flash-lite-001",
]

# Free models for testing
FREE_MODELS = [
    "deepseek/deepseek-r1:free",
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

# Poker game configuration
NUM_GAMES = int(os.getenv("NUM_GAMES", 1))  # Number of games to simulate
PLAYERS_PER_GAME = int(
    os.getenv("PLAYERS_PER_GAME", 6)
)  # Number of players in each game
STARTING_CHIPS = int(
    os.getenv("STARTING_CHIPS", 1000)
)  # Starting chips for each player
SMALL_BLIND = int(os.getenv("SMALL_BLIND", 5))  # Small blind amount
BIG_BLIND = int(os.getenv("BIG_BLIND", 10))  # Big blind amount
MAX_ROUNDS = int(
    os.getenv("MAX_ROUNDS", 100)
)  # Maximum number of rounds before ending the game

# Game type
GAME_TYPE = "Texas Hold'em"  # Type of poker game to run

# Language setting
LANGUAGE = os.getenv(
    "GAME_LANGUAGE", "English"
)  # Language for game prompts and interactions

# Timeout for API calls (in seconds)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))

# Maximum output tokens for LLM responses
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 400))

# Random seed for reproducibility (set to None for random behavior)
RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)
