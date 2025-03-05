"""
OpenRouter API client for the LLM Poker Game.
This module handles all interactions with the OpenRouter API.
"""

import json
import requests
import os
from poker_config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    MAX_OUTPUT_TOKENS,
    API_TIMEOUT,
)
from mock_llm import get_mock_response

# Flag to use mock responses instead of real API calls
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


def get_llm_response(model_name, prompt):
    """
    Get a response from an LLM model using OpenRouter API.

    Args:
        model_name (str): The name of the LLM model to use.
        prompt (str): The prompt to send to the model.

    Returns:
        str: The response from the model.
    """
    # Use mock responses for testing
    if USE_MOCK:
        return get_mock_response(model_name, prompt)

    # Use real API for production
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_OUTPUT_TOKENS,
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        # Initialize response_text to handle cases where response is not defined
        response_text = "No response received"

        # Only try to access response.text if response is defined
        try:
            if "response" in locals():
                response_text = response.text
        except:
            pass

        print(
            f"Error getting response from {model_name}: error: {e}, response: {response_text}"
        )
        return "ERROR: Could not get response"
