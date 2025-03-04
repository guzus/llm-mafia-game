"""
OpenRouter API client for the LLM Mafia Game Competition.
This module handles all interactions with the OpenRouter API.
"""

import json
import requests
import config


def get_llm_response(model_name, prompt):
    """
    Get a response from an LLM model using OpenRouter API.

    Args:
        model_name (str): The name of the LLM model to use.
        prompt (str): The prompt to send to the model.

    Returns:
        str: The response from the model.
    """
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
            timeout=config.API_TIMEOUT,
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
