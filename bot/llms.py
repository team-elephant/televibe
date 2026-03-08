"""LLM management for the Remote Cursor bot."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_llms_file() -> Path:
    """Get path to llms.json in bot directory."""
    return Path(__file__).parent / "llms.json"


def load_llms() -> list:
    """Load custom LLM configurations."""
    llms_file = get_llms_file()
    
    if not llms_file.exists():
        return []
    
    try:
        with open(llms_file, "r") as f:
            data = json.load(f)
            return data.get("llms", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_llms(llms: list) -> None:
    """Save custom LLM configurations."""
    llms_file = get_llms_file()
    
    data = {"llms": llms}
    
    with open(llms_file, "w") as f:
        json.dump(data, f, indent=2)


def create_llm(name: str, endpoint: str, api_key: str) -> dict:
    """Create a new custom LLM configuration."""
    llms = load_llms()
    
    llm = {
        "id": str(uuid.uuid4()),
        "name": name,
        "endpoint": endpoint,
        "api_key": api_key,
        "created_at": datetime.now().isoformat()
    }
    
    llms.append(llm)
    save_llms(llms)
    
    return llm


def delete_llm(llm_id: str) -> bool:
    """Delete a custom LLM by ID."""
    llms = load_llms()
    
    original_count = len(llms)
    llms = [l for l in llms if l["id"] != llm_id]
    
    # Check if an LLM was actually removed
    if len(llms) == original_count:
        return False  # LLM not found
    
    save_llms(llms)
    return True


def get_llm(llm_id: str) -> Optional[dict]:
    """Get an LLM by ID."""
    llms = load_llms()
    return next((l for l in llms if l["id"] == llm_id), None)


def get_llm_by_name(name: str) -> Optional[dict]:
    """Get an LLM by name."""
    llms = load_llms()
    return next((l for l in llms if l["name"].lower() == name.lower()), None)
