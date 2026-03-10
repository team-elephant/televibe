"""Conversation memory management for the Remote Cursor Telegram Bot.

Manages conversation context per Telegram group and agent.
Allows agents to remember context across prompts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


# Default settings
DEFAULT_MAX_MESSAGES = 20  # Maximum messages to keep per agent conversation
MAX_CONTEXT_LENGTH = 8000  # Maximum characters for context string


def get_conversations_file(group_id: str) -> Path:
    """Get path to conversations file for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Path to the group's conversations JSON file.
    """
    # Sanitize group_id for use as filename (replace - with _)
    safe_id = str(group_id).replace("-", "_")
    return Path(__file__).parent / "memory" / f"{safe_id}_conversations.json"


def load_conversations(group_id: str) -> dict:
    """Load conversations for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Dict with conversations by agent.
    """
    conv_file = get_conversations_file(group_id)
    
    if not conv_file.exists():
        return {"conversations": {}}
    
    try:
        with open(conv_file, "r") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"[CONVERSATIONS] Failed to load for {group_id}: {e}")
        return {"conversations": {}}


def save_conversations(group_id: str, data: dict) -> None:
    """Save conversations for a group.
    
    Args:
        group_id: The Telegram group ID.
        data: Conversations dict.
    """
    conv_file = get_conversations_file(group_id)
    
    try:
        with open(conv_file, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.warning(f"[CONVERSATIONS] Failed to save for {group_id}: {e}")


def get_agent_conversation(group_id: str, agent: str) -> list:
    """Get conversation history for an agent in a group.
    
    Args:
        group_id: The Telegram group ID.
        agent: The agent name (cursor, claude, codex, grok).
        
    Returns:
        List of message dicts (role, content, timestamp).
    """
    data = load_conversations(group_id)
    conversations = data.get("conversations", {})
    return conversations.get(agent, [])


def add_message(
    group_id: str,
    agent: str,
    role: str,
    content: str
) -> None:
    """Add a message to the conversation history.
    
    Args:
        group_id: The Telegram group ID.
        agent: The agent name (cursor, claude, codex, grok).
        role: Message role ('user' or 'assistant').
        content: Message content.
    """
    data = load_conversations(group_id)
    
    if "conversations" not in data:
        data["conversations"] = {}
    
    if agent not in data["conversations"]:
        data["conversations"][agent] = []
    
    # Add message
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    data["conversations"][agent].append(message)
    
    # Trim to max messages
    if len(data["conversations"][agent]) > DEFAULT_MAX_MESSAGES:
        data["conversations"][agent] = data["conversations"][agent][-DEFAULT_MAX_MESSAGES:]
    
    # Update last_updated
    data["last_updated"] = datetime.now().isoformat()
    
    save_conversations(group_id, data)
    logger.info(f"[CONVERSATIONS] Added {role} message to {agent} in group {group_id}")


def clear_agent_conversation(group_id: str, agent: str) -> bool:
    """Clear conversation history for an agent.
    
    Args:
        group_id: The Telegram group ID.
        agent: The agent name (cursor, claude, codex, grok).
        
    Returns:
        True if cleared, False if no conversation existed.
    """
    data = load_conversations(group_id)
    
    if agent in data.get("conversations", {}):
        del data["conversations"][agent]
        data["last_updated"] = datetime.now().isoformat()
        save_conversations(group_id, data)
        logger.info(f"[CONVERSATIONS] Cleared conversation for {agent} in group {group_id}")
        return True
    
    return False


def clear_all_conversations(group_id: str) -> bool:
    """Clear all conversation history for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        True if cleared.
    """
    data = {"conversations": {}, "last_updated": datetime.now().isoformat()}
    save_conversations(group_id, data)
    logger.info(f"[CONVERSATIONS] Cleared all conversations for group {group_id}")
    return True


def get_context_for_agent(group_id: str, agent: str) -> str:
    """Get formatted context string for an agent.
    
    Args:
        group_id: The Telegram group ID.
        agent: The agent name (cursor, claude, codex, grok).
        
    Returns:
        Formatted context string to prepend to prompts.
    """
    messages = get_agent_conversation(group_id, agent)
    
    if not messages:
        return ""
    
    # Build context string
    context_parts = ["=== Previous Conversation Context ==="]
    
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        # Truncate long messages
        if len(content) > 1000:
            content = content[:1000] + "..."
        
        context_parts.append(f"\n{role.upper()}: {content}")
    
    context_parts.append("\n=== End Context ===\n")
    
    context = "".join(context_parts)
    
    # Truncate if too long
    if len(context) > MAX_CONTEXT_LENGTH:
        context = context[:MAX_CONTEXT_LENGTH] + "...(truncated)"
    
    return context


def format_conversation_summary(group_id: str, agent: Optional[str] = None) -> str:
    """Format conversation history as readable string.
    
    Args:
        group_id: The Telegram group ID.
        agent: Specific agent to show, or None for all.
        
    Returns:
        Formatted string.
    """
    data = load_conversations(group_id)
    conversations = data.get("conversations", {})
    
    if not conversations:
        return "🧠 *Conversation Memory*\n\nNo conversation history yet."
    
    lines = ["🧠 *Conversation Memory*", ""]
    
    # Filter by agent if specified
    if agent:
        agents = [agent] if agent in conversations else []
    else:
        agents = conversations.keys()
    
    for ag in agents:
        msgs = conversations.get(ag, [])
        if not msgs:
            continue
            
        lines.append(f"*@{ag}:* {len(msgs)} message(s)")
        
        # Show last 3 messages as preview
        for i, msg in enumerate(msgs[-3:]):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > 60:
                content = content[:60] + "..."
            lines.append(f"  {i+1}. {role}: {content}")
        
        lines.append("")
    
    return "\n".join(lines)
