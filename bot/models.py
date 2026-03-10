"""Model management for the Remote Cursor Telegram Bot.

Manages model preferences per agent per group.
Each agent can have different models configured.
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


# Fallback model configurations per agent type (used when CLI is unavailable)
# These match the actual naming conventions used by each CLI
FALLBACK_MODEL_CONFIGS = {
    "cursor": {
        "name": "Cursor",
        "current": "sonnet-4.6",
        "available": [
            # Anthropic models (using CLI naming with dots)
            "sonnet-4.6",
            "opus-4.6",
            "sonnet-4.5",
            "opus-4.5",
            "haiku-3.5",
            # Cursor models
            "composer-1.5",
            "composer-1",
            # Google models (using CLI naming with dots)
            "gemini-3.1-pro",
            "gemini-3-pro",
            "gemini-3-flash",
            "gemini-2.5-flash",
            # OpenAI models (using CLI naming with dots)
            "gpt-5.4",
            "gpt-5.4-xhigh",
            "gpt-5.4-high",
            "gpt-5.4-medium",
            "gpt-5.2",
            "gpt-5.1-codex-mini",
            "gpt-5.1-codex",
            "gpt-5.1-high",
            "gpt-5",
            # xAI
            "grok",
        ]
    },
    "claude": {
        "name": "Claude",
        "current": "sonnet",
        "available": [
            # Claude Code aliases (recommended)
            "default",
            "sonnet",
            "opus",
            "haiku",
            "sonnet[1m]",
            "opusplan",
            # Full model names (using CLI naming with dots)
            "sonnet-4.6",
            "opus-4.6",
            "sonnet-4.5",
            "opus-4.5",
            "haiku-3.5",
        ]
    },
    "codex": {
        "name": "Codex",
        "current": "gpt-5.4",
        "available": [
            # Recommended models (using CLI naming with dots)
            "gpt-5.4",
            "gpt-5.3-codex-spark-preview",
            # GPT-5 series
            "gpt-5.2",
            "gpt-5.1-codex-mini",
            "gpt-5.1-codex",
            "gpt-5.1-high",
            "gpt-5",
            # Legacy support
            "gpt-4o",
            "gpt-4o-mini",
        ]
    },
    "grok": {
        "name": "Grok",
        "current": "MiniMax-M2.5",
        "available": [
            # MiniMax models (used with @vibe-kit/grok-cli)
            "MiniMax-M2.5",
            "MiniMax-M2",
            "MiniMax-M1.8",
            "MiniMax-M1.5",
            "abab6.5s-chat",
        ]
    }
}

# Cache for dynamically fetched models
_cached_cursor_models: Optional[list] = None
_cached_claude_models: Optional[list] = None
_cached_codex_models: Optional[list] = None


def _fetch_cursor_models_from_cli() -> Optional[list]:
    """Fetch available models from Cursor CLI.
    
    Runs `agent --list-models` to get the list of available models.
    
    Returns:
        List of model names, or None if unavailable.
    """
    try:
        # Run the cursor agent command to list models
        result = subprocess.run(
            ["agent", "--list-models"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "PATH": f"{os.path.expanduser('~/.local/bin')}:{os.environ.get('PATH', '')}"}
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            
            # Parse the output - look for model names
            # The output format may vary, so we try to extract model identifiers
            models = []
            
            # Skip "No models available" message
            if "No models available" in output:
                logger.info("[MODELS] No models available from Cursor CLI (account may not have access)")
                return None
            
            # Split by lines and filter for actual model names
            # Model names typically contain letters, numbers, dots, hyphens
            # Skip lines with "Loading", "Tip:", "Available", etc.
            import re
            model_pattern = re.compile(r'^[a-zA-Z0-9.\-_]+$')
            
            for line in output.split('\n'):
                line = line.strip()
                
                # Skip empty lines and non-model lines
                if not line:
                    continue
                if any(x in line.lower() for x in ["loading", "tip:", "available", "select", "choose", "model"]):
                    continue
                # Skip lines that start with special characters
                if line.startswith('-') or line.startswith('*') or line.startswith('['):
                    continue
                    
                # Check if it looks like a valid model name
                # Model names should be alphanumeric with dots/hyphens
                if model_pattern.match(line):
                    if line not in models:
                        models.append(line)
            
            if models:
                logger.info(f"[MODELS] Fetched {len(models)} models from Cursor CLI: {models[:5]}...")
                return models
            
        logger.warning(f"[MODELS] Failed to parse Cursor CLI output: {result.stdout[:200]}")
        
    except subprocess.TimeoutExpired:
        logger.warning("[MODELS] Timeout while fetching Cursor models")
    except FileNotFoundError:
        logger.warning("[MODELS] Cursor agent command not found")
    except Exception as e:
        logger.warning(f"[MODELS] Error fetching Cursor models: {e}")
    
    return None


def _fetch_claude_models_from_cli() -> Optional[list]:
    """Fetch available models from Anthropic API for Claude Code.
    
    Uses the Anthropic API to list available models for the account.
    
    Returns:
        List of model names, or None if unavailable.
    """
    from bot.config import config
    
    api_key = config.anthropic_api_key
    if not api_key:
        logger.warning("[MODELS] No Anthropic API key available for Claude models")
        return None
    
    try:
        import urllib.request
        import urllib.error
        import urllib.parse
        
        url = "https://api.anthropic.com/v1/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            models = []
            
            for item in data.get("data", []):
                model_id = item.get("id", "")
                # Filter for Claude models
                if "claude" in model_id.lower():
                    if model_id not in models:
                        models.append(model_id)
            
            if models:
                logger.info(f"[MODELS] Fetched {len(models)} models from Anthropic API for Claude")
                return sorted(models)
                
    except ImportError:
        logger.warning("[MODELS] urllib not available, cannot fetch Claude models")
    except urllib.error.HTTPError as e:
        logger.warning(f"[MODELS] HTTP error fetching Claude models: {e.code}")
    except Exception as e:
        logger.warning(f"[MODELS] Error fetching Claude models: {e}")
    
    return None


def _fetch_codex_models_from_api() -> Optional[list]:
    """Fetch available models from OpenAI API for Codex.
    
    Queries the OpenAI API to get available models.
    
    Returns:
        List of model names, or None if unavailable.
    """
    from bot.config import config
    
    api_key = config.openai_api_key
    if not api_key:
        logger.warning("[MODELS] No OpenAI API key available for Codex models")
        return None
    
    try:
        import urllib.request
        import urllib.error
        
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            models = []
            
            for item in data.get("data", []):
                model_id = item.get("id", "")
                # Filter for relevant coding models (GPT-4, GPT-5, Codex)
                if any(x in model_id.lower() for x in ["gpt-4", "gpt-5", "codex", "o1", "o3", "o4"]):
                    if model_id not in models:
                        models.append(model_id)
            
            if models:
                logger.info(f"[MODELS] Fetched {len(models)} models from OpenAI API for Codex")
                return sorted(models)
                
    except ImportError:
        logger.warning("[MODELS] urllib not available, cannot fetch Codex models")
    except urllib.error.HTTPError as e:
        logger.warning(f"[MODELS] HTTP error fetching Codex models: {e.code}")
    except Exception as e:
        logger.warning(f"[MODELS] Error fetching Codex models: {e}")
    
    return None


def get_claude_models() -> list:
    """Get available Claude Code models, fetching dynamically if possible.
    
    First tries to fetch from CLI/API, falls back to hardcoded list.
    
    Returns:
        List of available Claude model identifiers.
    """
    global _cached_claude_models
    
    # Return cached models if available
    if _cached_claude_models is not None:
        return _cached_claude_models
    
    # Try to fetch from CLI
    cli_models = _fetch_claude_models_from_cli()
    
    if cli_models:
        _cached_claude_models = cli_models
        return cli_models
    
    # Fall back to hardcoded list
    _cached_claude_models = FALLBACK_MODEL_CONFIGS["claude"]["available"]
    return _cached_claude_models


def get_codex_models() -> list:
    """Get available Codex models, fetching dynamically if possible.
    
    First tries to fetch from API, falls back to hardcoded list.
    
    Returns:
        List of available Codex model identifiers.
    """
    global _cached_codex_models
    
    # Return cached models if available
    if _cached_codex_models is not None:
        return _cached_codex_models
    
    # Try to fetch from API
    api_models = _fetch_codex_models_from_api()
    
    if api_models:
        _cached_codex_models = api_models
        return api_models
    
    # Fall back to hardcoded list
    _cached_codex_models = FALLBACK_MODEL_CONFIGS["codex"]["available"]
    return _cached_codex_models


def refresh_claude_models() -> list:
    """Force refresh of Claude models cache.
    
    Returns:
        List of available Claude model identifiers.
    """
    global _cached_claude_models
    _cached_claude_models = None
    return get_claude_models()


def refresh_codex_models() -> list:
    """Force refresh of Codex models cache.
    
    Returns:
        List of available Codex model identifiers.
    """
    global _cached_codex_models
    _cached_codex_models = None
    return get_codex_models()


def get_cursor_models() -> list:
    """Get available Cursor models, fetching dynamically if possible.
    
    First tries to fetch from CLI, falls back to hardcoded list.
    
    Returns:
        List of available Cursor model identifiers.
    """
    global _cached_cursor_models
    
    # Return cached models if available
    if _cached_cursor_models is not None:
        return _cached_cursor_models
    
    # Try to fetch from CLI
    cli_models = _fetch_cursor_models_from_cli()
    
    if cli_models:
        _cached_cursor_models = cli_models
        return cli_models
    
    # Fall back to hardcoded list
    _cached_cursor_models = FALLBACK_MODEL_CONFIGS["cursor"]["available"]
    return _cached_cursor_models


def refresh_cursor_models() -> list:
    """Force refresh of Cursor models cache.
    
    Returns:
        List of available Cursor model identifiers.
    """
    global _cached_cursor_models
    _cached_cursor_models = None
    return get_cursor_models()


# Model configurations - dynamically fetched where possible
MODEL_CONFIGS = {
    "cursor": {
        "name": "Cursor",
        "current": "sonnet-4.6",
        "available": [],  # Populated dynamically
        "_fallback": FALLBACK_MODEL_CONFIGS["cursor"]["available"]
    },
    "claude": {
        "name": "Claude",
        "current": "sonnet",
        "available": FALLBACK_MODEL_CONFIGS["claude"]["available"]
    },
    "codex": {
        "name": "Codex",
        "current": "gpt-5.4",
        "available": FALLBACK_MODEL_CONFIGS["codex"]["available"]
    },
    "grok": {
        "name": "Grok",
        "current": "MiniMax-M2.5",
        "available": FALLBACK_MODEL_CONFIGS["grok"]["available"]
    }
}


def _get_cursor_available() -> list:
    """Get Cursor available models, initializing if needed."""
    if not MODEL_CONFIGS["cursor"]["available"]:
        MODEL_CONFIGS["cursor"]["available"] = get_cursor_models()
    return MODEL_CONFIGS["cursor"]["available"]


# Initialize models on module load
_get_cursor_available()
get_claude_models()
get_codex_models()


def get_models_file() -> Path:
    """Get path to models.json in bot directory."""
    return Path(__file__).parent / "models.json"


def load_models() -> dict:
    """Load model preferences from models.json."""
    models_file = get_models_file()
    
    if not models_file.exists():
        return {"models": {}}
    
    try:
        with open(models_file, "r") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError):
        return {"models": {}}


def save_models(data: dict) -> None:
    """Save model preferences to models.json."""
    models_file = get_models_file()
    
    with open(models_file, "w") as f:
        json.dump(data, f, indent=2)


def get_available_models(agent_type: str) -> list:
    """Get available models for an agent type.
    
    Args:
        agent_type: The agent type (cursor, claude, codex, grok).
        
    Returns:
        List of available model identifiers.
    """
    if agent_type == "cursor":
        return _get_cursor_available()
    elif agent_type == "claude":
        return get_claude_models()
    elif agent_type == "codex":
        return get_codex_models()
    
    config = MODEL_CONFIGS.get(agent_type)
    if config:
        return config["available"]
    return []


def get_model_display_name(agent_type: str, model: str) -> str:
    """Get display name for a model.
    
    Args:
        agent_type: The agent type.
        model: The model identifier.
        
    Returns:
        Human-readable model name.
    """
    # Add friendly names for common models
    friendly_names = {
        # Claude Code aliases
        "default": "Default (recommended)",
        "sonnet": "Claude Sonnet 4.6",
        "opus": "Claude Opus 4.6",
        "haiku": "Claude Haiku 3.5",
        "sonnet[1m]": "Claude Sonnet 1M",
        "opusplan": "Claude Opus Plan",
        # Cursor models
        "composer-1": "Composer 1",
        "composer-1.5": "Composer 1.5",
        # Anthropic models (using CLI naming with dots)
        "sonnet-4.6": "Claude Sonnet 4.6",
        "opus-4.6": "Claude Opus 4.6",
        "sonnet-4.5": "Claude Sonnet 4.5",
        "opus-4.5": "Claude Opus 4.5",
        "haiku-3.5": "Claude Haiku 3.5",
        # Google models (using CLI naming with dots)
        "gemini-3.1-pro": "Gemini 3.1 Pro",
        "gemini-3-pro": "Gemini 3 Pro",
        "gemini-3-flash": "Gemini 3 Flash",
        "gemini-2.5-flash": "Gemini 2.5 Flash",
        # OpenAI models (using CLI naming with dots)
        "gpt-5.4": "GPT-5.4",
        "gpt-5.4-xhigh": "GPT-5.4 XHigh",
        "gpt-5.4-high": "GPT-5.4 High",
        "gpt-5.4-medium": "GPT-5.4 Medium",
        "gpt-5.2": "GPT-5.2",
        "gpt-5.1-codex-mini": "GPT-5.1 Codex Mini",
        "gpt-5.1-codex": "GPT-5.1 Codex",
        "gpt-5.1-high": "GPT-5.1 High",
        "gpt-5": "GPT-5",
        # Legacy
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
        # Grok models (xAI)
        "grok-2": "Grok 2",
        "grok-2-vision-1212": "Grok 2 Vision",
        "grok-beta": "Grok Beta",
        "grok": "Grok",
        # MiniMax models (used with @vibe-kit/grok-cli)
        "MiniMax-M2.5": "MiniMax M2.5",
        "MiniMax-M2": "MiniMax M2",
        "MiniMax-M1.8": "MiniMax M1.8",
        "MiniMax-M1.5": "MiniMax M1.5",
        "abab6.5s-chat": "MiniMax ABAB 6.5s",
    }
    return friendly_names.get(model, model)


def is_valid_model(agent_type: str, model: str) -> bool:
    """Check if a model is valid for an agent type.
    
    Args:
        agent_type: The agent type (cursor, claude, codex, grok).
        model: The model identifier.
        
    Returns:
        True if model is valid for this agent type.
    """
    available = get_available_models(agent_type)
    return model in available


def get_current_model(group_id: str, agent_type: str) -> str:
    """Get the current model for an agent in a group.
    
    Args:
        group_id: The Telegram group ID.
        agent_type: The agent type (cursor, claude, codex, grok).
        
    Returns:
        Current model identifier, or default if not set.
    """
    data = load_models()
    models = data.get("models", {})
    
    group_models = models.get(group_id, {})
    agent_model = group_models.get(agent_type)
    
    if agent_model:
        return agent_model
    
    # Return default model for agent type
    config = MODEL_CONFIGS.get(agent_type)
    if config:
        return config["current"]
    
    return "unknown"


def set_model(group_id: str, agent_type: str, model: str) -> bool:
    """Set the model for an agent in a group.
    
    Args:
        group_id: The Telegram group ID.
        agent_type: The agent type (cursor, claude, codex, grok).
        model: The model identifier.
        
    Returns:
        True if model was set successfully, False if model is invalid.
    """
    # Validate model
    if not is_valid_model(agent_type, model):
        return False
    
    data = load_models()
    models = data.get("models", {})
    
    if group_id not in models:
        models[group_id] = {}
    
    models[group_id][agent_type] = model
    data["models"] = models
    
    save_models(data)
    return True


def get_group_models(group_id: str) -> dict:
    """Get all model preferences for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Dict of agent_type -> model.
    """
    data = load_models()
    models = data.get("models", {})
    
    group_models = models.get(group_id, {})
    
    # Fill in defaults for agents not yet configured
    result = {}
    for agent_type in MODEL_CONFIGS.keys():
        if agent_type in group_models:
            result[agent_type] = group_models[agent_type]
        else:
            result[agent_type] = MODEL_CONFIGS[agent_type]["current"]
    
    return result


def get_models_status(group_id: str) -> str:
    """Get status message showing all models for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Status message string with all models.
    """
    group_models = get_group_models(group_id)
    
    lines = ["📊 *Model Preferences*", ""]
    
    for agent_type, model in group_models.items():
        config = MODEL_CONFIGS.get(agent_type, {})
        agent_name = config.get("name", agent_type.capitalize())
        display_name = get_model_display_name(agent_type, model)
        available = get_available_models(agent_type)
        
        lines.append(f"*{agent_name}:* {display_name}")
        lines.append(f"  Available: {', '.join(available)}")
        lines.append("")
    
    return "\n".join(lines)
