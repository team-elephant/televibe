"""Execution history management for the Remote Cursor Telegram Bot.

Manages execution history per Telegram group.
Each execution record tracks agent prompts and their outcomes.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


# Default settings
DEFAULT_HISTORY_LIMIT = 10  # Number of recent executions to keep


def get_history_file(group_id: str) -> Path:
    """Get path to history file for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Path to the group's history JSON file.
    """
    # Sanitize group_id for use as filename (replace - with _)
    safe_id = str(group_id).replace("-", "_")
    return Path(__file__).parent / "memory" / f"{safe_id}_history.json"


def load_history(group_id: str) -> dict:
    """Load execution history for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Dict with 'executions' list.
    """
    history_file = get_history_file(group_id)
    
    if not history_file.exists():
        return {"executions": []}
    
    try:
        with open(history_file, "r") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"[HISTORY] Failed to load history for {group_id}: {e}")
        return {"executions": []}


def save_history(group_id: str, data: dict) -> None:
    """Save execution history for a group.
    
    Args:
        group_id: The Telegram group ID.
        data: History dict with 'executions' list.
    """
    history_file = get_history_file(group_id)
    
    try:
        with open(history_file, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.warning(f"[HISTORY] Failed to save history for {group_id}: {e}")


def add_execution(
    group_id: str,
    agent: str,
    prompt: str,
    model: Optional[str] = None,
    status: str = "started"
) -> str:
    """Add a new execution record.
    
    Args:
        group_id: The Telegram group ID.
        agent: The agent name (cursor, claude, codex, grok).
        prompt: The prompt that was executed.
        model: The model used (optional).
        status: Initial status (default: 'started').
        
    Returns:
        Execution ID.
    """
    history = load_history(group_id)
    
    execution = {
        "id": str(uuid.uuid4()),
        "agent": agent,
        "prompt": prompt,
        "model": model,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "completed_at": None,
        "files_modified": [],
        "error": None
    }
    
    history["executions"].insert(0, execution)  # Add to beginning
    
    # Keep only the last N executions
    if len(history["executions"]) > DEFAULT_HISTORY_LIMIT:
        history["executions"] = history["executions"][:DEFAULT_HISTORY_LIMIT]
    
    save_history(group_id, history)
    
    logger.info(f"[HISTORY] Added execution {execution['id']} for {agent} in group {group_id}")
    return execution["id"]


def update_execution(
    group_id: str,
    execution_id: str,
    status: Optional[str] = None,
    files_modified: Optional[list] = None,
    error: Optional[str] = None
) -> bool:
    """Update an execution record.
    
    Args:
        group_id: The Telegram group ID.
        execution_id: The execution ID.
        status: New status (optional).
        files_modified: List of modified files (optional).
        error: Error message (optional).
        
    Returns:
        True if updated successfully, False if not found.
    """
    history = load_history(group_id)
    
    for execution in history["executions"]:
        if execution["id"] == execution_id:
            if status:
                execution["status"] = status
                if status in ["completed", "failed", "cancelled"]:
                    execution["completed_at"] = datetime.now().isoformat()
            
            if files_modified is not None:
                execution["files_modified"] = files_modified
            
            if error:
                execution["error"] = error
            
            save_history(group_id, history)
            logger.info(f"[HISTORY] Updated execution {execution_id} to status {status}")
            return True
    
    logger.warning(f"[HISTORY] Execution {execution_id} not found in group {group_id}")
    return False


def get_recent_executions(group_id: str, limit: int = DEFAULT_HISTORY_LIMIT) -> list:
    """Get recent executions for a group.
    
    Args:
        group_id: The Telegram group ID.
        limit: Maximum number of executions to return.
        
    Returns:
        List of execution records.
    """
    history = load_history(group_id)
    return history["executions"][:limit]


def get_execution(group_id: str, execution_id: str) -> Optional[dict]:
    """Get a specific execution by ID.
    
    Args:
        group_id: The Telegram group ID.
        execution_id: The execution ID.
        
    Returns:
        Execution dict or None if not found.
    """
    history = load_history(group_id)
    
    for execution in history["executions"]:
        if execution["id"] == execution_id:
            return execution
    
    return None


def clear_history(group_id: str) -> bool:
    """Clear all history for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        True if cleared successfully.
    """
    save_history(group_id, {"executions": []})
    logger.info(f"[HISTORY] Cleared history for group {group_id}")
    return True


def format_execution_summary(execution: dict, index: int = 0) -> str:
    """Format an execution as a readable summary string.
    
    Args:
        execution: Execution dict.
        index: Index number for display.
        
    Returns:
        Formatted string.
    """
    agent = execution.get("agent", "unknown")
    status = execution.get("status", "unknown")
    timestamp = execution.get("timestamp", "")
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%Y-%m-%d %H:%M")
    except:
        time_str = timestamp[:16] if timestamp else "unknown"
    
    # Get status emoji
    if status == "completed":
        status_emoji = "✅"
    elif status == "failed":
        status_emoji = "❌"
    elif status == "started":
        status_emoji = "⏳"
    else:
        status_emoji = "⚪"
    
    # Truncate prompt if too long
    prompt = execution.get("prompt", "")
    if len(prompt) > 50:
        prompt = prompt[:50] + "..."
    
    # Format files modified
    files = execution.get("files_modified", [])
    if files:
        files_str = f" ({len(files)} file(s))"
    else:
        files_str = ""
    
    return f"{index + 1}. {status_emoji} @{agent}: \"{prompt}\"{files_str} - {time_str}"


def get_history_status(group_id: str) -> str:
    """Get status message showing execution history for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Status message string.
    """
    executions = get_recent_executions(group_id)
    
    if not executions:
        return "📋 *Execution History*\n\nNo executions yet in this group."
    
    lines = ["📋 *Execution History*", ""]
    
    for i, execution in enumerate(executions):
        summary = format_execution_summary(execution, i)
        lines.append(summary)
    
    return "\n".join(lines)
