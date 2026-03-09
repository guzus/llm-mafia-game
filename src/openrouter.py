"""
Unified LLM API client for the LLM Mafia Game Competition.
This module handles interactions with both OpenRouter and Ollama APIs.
"""

import json
from typing import Any

import requests
import config
from logger import GameLogger

# Create a logger instance for model-specific issues
model_logger = GameLogger(log_to_file=True)
OPENROUTER_API_ROOT = "https://openrouter.ai/api/v1"


def _configured_openrouter_key(api_key: str | None = None) -> str | None:
    """Return a usable OpenRouter API key or None when configuration is missing."""
    candidate = api_key or config.OPENROUTER_API_KEY
    if not candidate or candidate == "your_openrouter_api_key_here":
        return None
    return candidate


def _openrouter_headers(api_key: str | None = None) -> dict[str, str]:
    """Build OpenRouter request headers."""
    key = _configured_openrouter_key(api_key)
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


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

    headers = _openrouter_headers()

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


def get_openrouter_key_info(api_key: str | None = None) -> dict[str, Any]:
    """Fetch metadata about the configured OpenRouter key."""
    response = requests.get(
        f"{OPENROUTER_API_ROOT}/key",
        headers=_openrouter_headers(api_key),
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", {})


def get_openrouter_credits(api_key: str | None = None) -> dict[str, Any]:
    """Fetch aggregate OpenRouter credit and usage data."""
    response = requests.get(
        f"{OPENROUTER_API_ROOT}/credits",
        headers=_openrouter_headers(api_key),
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", {})


def get_openrouter_account_state(api_key: str | None = None) -> dict[str, Any]:
    """Return a merged view of the key metadata and credit balance."""
    configured_key = _configured_openrouter_key(api_key)
    if not configured_key:
        return {
            "configured": False,
            "status": "missing_api_key",
            "error": "OPENROUTER_API_KEY is not configured",
        }

    try:
        key_info = get_openrouter_key_info(configured_key)
        credits = get_openrouter_credits(configured_key)

        total_credits = credits.get("total_credits")
        total_usage = credits.get("total_usage")
        remaining_credits = None
        if total_credits is not None and total_usage is not None:
            remaining_credits = float(total_credits) - float(total_usage)

        return {
            "configured": True,
            "status": "ok",
            "key_info": key_info,
            "credits": credits,
            "total_credits": total_credits,
            "total_usage": total_usage,
            "remaining_credits": remaining_credits,
            "limit_remaining": key_info.get("limit_remaining"),
            "usage_daily": key_info.get("usage_daily"),
            "usage_weekly": key_info.get("usage_weekly"),
            "usage_monthly": key_info.get("usage_monthly"),
            "is_free_tier": key_info.get("is_free_tier"),
            "label": key_info.get("label"),
        }
    except Exception as exc:
        return {
            "configured": True,
            "status": "error",
            "error": str(exc),
        }


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
