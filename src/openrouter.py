"""
Unified LLM API client for the LLM Mafia Game Competition.
This module handles interactions with both OpenRouter and Ollama APIs.
"""

import json
import requests
import config
import time
import random
from logger import GameLogger

# Create a logger instance for model-specific issues
model_logger = GameLogger(log_to_file=True)


def is_ollama_model(model_name):
    """
    Check if a model name corresponds to an Ollama model.
    
    Args:
        model_name (str): The model name to check.
        
    Returns:
        bool: True if it's an Ollama model, False otherwise.
    """
    return model_name in config.OLLAMA_MODELS or model_name.startswith("ollama:")


def get_ollama_response(model_name, prompt):
    """
    Get a response from an LLM model using Ollama API.

    Args:
        model_name (str): The name of the LLM model to use.
        prompt (str): The prompt to send to the model.

    Returns:
        str: The response from the model.
    """
    # Get model-specific configuration if available
    model_config = config.MODEL_CONFIGS.get(model_name, {})
    
    # Set timeout based on model config or defaults
    timeout = model_config.get("timeout", config.API_TIMEOUT)

    headers = {
        "Content-Type": "application/json",
    }

    # Remove "ollama:" prefix if present
    clean_model_name = model_name.replace("ollama:", "")

    data = {
        "model": clean_model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": config.MAX_OUTPUT_TOKENS,
        }
    }

    try:
        response = requests.post(
            config.OLLAMA_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=timeout,
        )
        response.raise_for_status()

        result = response.json()
        return result["response"]

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
            f"Error getting response from Ollama model {model_name}: error: {e}, response: {response_text}"
        )
        return "ERROR: Could not get response from Ollama"


def get_openrouter_response(model_name, prompt):
    """
    Get a response from an LLM model using OpenRouter API.

    Args:
        model_name (str): The name of the LLM model to use.
        prompt (str): The prompt to send to the model.

    Returns:
        str: The response from the model.
    """
    # Get model-specific configuration if available
    model_config = config.MODEL_CONFIGS.get(model_name, {})

    # Set timeout, max_retries, and backoff_factor based on model config or defaults
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
            timeout=timeout,  # Use model-specific timeout
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
            f"Error getting response from OpenRouter model {model_name}: error: {e}, response: {response_text}"
        )
        return "ERROR: Could not get response from OpenRouter"


def get_llm_response(model_name, prompt):
    """
    Get a response from an LLM model using the appropriate API (OpenRouter or Ollama).

    Args:
        model_name (str): The name of the LLM model to use.
        prompt (str): The prompt to send to the model.

    Returns:
        str: The response from the model.
    """
    if is_ollama_model(model_name):
        return get_ollama_response(model_name, prompt)
    else:
        return get_openrouter_response(model_name, prompt)
