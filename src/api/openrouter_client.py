"""OpenRouter API client for LLM communication."""

import json
import requests
import config
from utils.logger import GameLogger

# Create a logger instance for API issues
api_logger = GameLogger(log_to_file=True)


def get_llm_response(model_name: str, prompt: str) -> str:
    """Get a response from an LLM model using OpenRouter API."""
    model_config = config.MODEL_CONFIGS.get(model_name, {})
    timeout = model_config.get("timeout", config.API_TIMEOUT)

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": config.MAX_OUTPUT_TOKENS,
    }

    try:
        response = requests.post(
            config.OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=timeout,
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        response_text = "No response received"
        try:
            if "response" in locals():
                response_text = response.text
        except:
            pass

        print(f"Error getting response from {model_name}: error: {e}, response: {response_text}")
        return "ERROR: Could not get response"