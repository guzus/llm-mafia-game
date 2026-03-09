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

# Ollama API settings
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODELS = [
    "llama3.2:latest",
    "llama3.1:latest",
    "llama3:latest",
    "mistral:latest",
    "codellama:latest",
    "gemma2:latest",
    "qwen2.5:latest",
    "phi3:latest",
]

# Database settings (Neon PostgreSQL-compatible)
DATABASE_URL = os.getenv("DATABASE_URL", "")
MIN_GAMES_FOR_TOP_DISPLAY = int(os.getenv("MIN_GAMES_FOR_TOP_DISPLAY", 5))

# Game settings

CRITIC_MODEL = "anthropic/claude-sonnet-4.6"
# Backward-compatible alias used by older code paths.
CLAUDE_SONNET_4 = CRITIC_MODEL

LATEST_FRONTIER_MODELS = [
    "openai/gpt-5.4",
    "google/gemini-3.1-pro-preview",
    "anthropic/claude-sonnet-4.6",
    "x-ai/grok-4.1-fast",
    "deepseek/deepseek-v3.2",
    "qwen/qwen3-max",
    "moonshotai/kimi-k2.5",
    "meta-llama/llama-4-maverick",
]

BUDGET_MODELS = [
    "openai/gpt-4.1-mini",
    "google/gemini-3.1-flash-lite-preview",
    "anthropic/claude-3.7-sonnet",
    "x-ai/grok-4-fast",
    "deepseek/deepseek-chat",
    "qwen/qwen3-coder",
    "mistralai/mistral-small-3.2-24b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
]

MODELS = [
    # OpenAI
    "openai/gpt-5.4",
    "openai/gpt-5",
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    # Google
    "google/gemini-3.1-pro-preview",
    "google/gemini-3.1-flash-lite-preview",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    # Anthropic
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3.7-sonnet",
    # xAI
    "x-ai/grok-4.1-fast",
    "x-ai/grok-4-fast",
    "x-ai/grok-4",
    # DeepSeek
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-chat",
    # Qwen
    "qwen/qwen3-max",
    "qwen/qwen3-coder",
    # Meta
    "meta-llama/llama-4-maverick",
    "meta-llama/llama-3.3-70b-instruct",
    # Mistral / Moonshot
    "mistralai/mistral-small-3.2-24b-instruct",
    "moonshotai/kimi-k2.5",
    "moonshotai/kimi-k2",
]

FREE_MODELS = [
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
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
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))

# Maximum output tokens for LLM responses
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 400))

# Model-specific configurations
MODEL_CONFIGS = {
    "deepseek/deepseek-v3.2": {
        "timeout": 90,
    },
    "deepseek/deepseek-r1": {
        "timeout": 90,  # Longer timeout for DeepSeek-R1
    },
    "deepseek/deepseek-r1-distill-llama-70b": {
        "timeout": 90,
    },
    "deepseek/deepseek-chat": {
        "timeout": 60,
    },
}

# Random seed for reproducibility (set to None for random behavior)
RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)

UNIQUE_MODELS = os.getenv("UNIQUE_MODELS", "true") == "true"
