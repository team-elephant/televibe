"""Agent management for the Remote Cursor bot."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_agents_file(project_dir: str) -> Path:
    """Get path to agents.json for a project."""
    return Path(project_dir) / "agents.json"


def get_conversations_file(project_dir: str) -> Path:
    """Get path to conversations.json for a project."""
    return Path(project_dir) / "conversations.json"


def load_agents(project_dir: str) -> list:
    """Load agents from project's agents.json."""
    agents_file = get_agents_file(project_dir)
    
    if not agents_file.exists():
        return []
    
    try:
        with open(agents_file, "r") as f:
            data = json.load(f)
            return data.get("agents", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_agents(project_dir: str, agents: list) -> None:
    """Save agents to project's agents.json."""
    agents_file = get_agents_file(project_dir)
    
    data = {"agents": agents}
    
    with open(agents_file, "w") as f:
        json.dump(data, f, indent=2)


def create_agent(project_dir: str, name: str, model: str, provider: str = "cursor", llm_id: str = None) -> dict:
    """Create a new agent.
    
    Args:
        project_dir: Path to the project
        name: Agent name
        model: Model identifier
        provider: Provider type (cursor, openai, anthropic, custom)
        llm_id: Custom LLM ID (if provider is custom)
    """
    agents = load_agents(project_dir)
    
    agent = {
        "id": str(uuid.uuid4()),
        "name": name,
        "model": model,
        "provider": provider,
        "llm_id": llm_id,
        "created_at": datetime.now().isoformat()
    }
    
    agents.append(agent)
    save_agents(project_dir, agents)
    
    # Initialize conversation history for this agent
    init_conversation(project_dir, agent["id"])
    
    return agent


def delete_agent(project_dir: str, agent_id: str) -> bool:
    """Delete an agent by ID."""
    agents = load_agents(project_dir)
    
    original_count = len(agents)
    agents = [a for a in agents if a["id"] != agent_id]
    
    # Check if an agent was actually removed
    if len(agents) == original_count:
        return False  # Agent not found
    
    save_agents(project_dir, agents)
    return True


def get_agent(project_dir: str, agent_id: str) -> Optional[dict]:
    """Get an agent by ID."""
    agents = load_agents(project_dir)
    return next((a for a in agents if a["id"] == agent_id), None)


def update_agent(project_dir: str, agent_id: str, updates: dict) -> bool:
    """Update an agent's properties."""
    agents = load_agents(project_dir)
    
    for agent in agents:
        if agent["id"] == agent_id:
            agent.update(updates)
            save_agents(project_dir, agents)
            return True
    
    return False


# Conversation history management

def load_conversations(project_dir: str) -> dict:
    """Load conversations from project's conversations.json."""
    conv_file = get_conversations_file(project_dir)
    
    if not conv_file.exists():
        return {}
    
    try:
        with open(conv_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_conversations(project_dir: str, conversations: dict) -> None:
    """Save conversations to project's conversations.json."""
    conv_file = get_conversations_file(project_dir)
    
    with open(conv_file, "w") as f:
        json.dump(conversations, f, indent=2)


def init_conversation(project_dir: str, agent_id: str) -> None:
    """Initialize conversation history for a new agent."""
    conversations = load_conversations(project_dir)
    
    if agent_id not in conversations:
        conversations[agent_id] = {
            "messages": [],
            "last_updated": datetime.now().isoformat()
        }
        save_conversations(project_dir, conversations)


def add_message(project_dir: str, agent_id: str, role: str, content: str) -> None:
    """Add a message to the agent's conversation history."""
    conversations = load_conversations(project_dir)
    
    if agent_id not in conversations:
        init_conversation(project_dir, agent_id)
    
    message = {
        "role": role,  # "user" or "assistant"
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    conversations[agent_id]["messages"].append(message)
    conversations[agent_id]["last_updated"] = datetime.now().isoformat()
    
    # Keep only last 100 messages per agent to prevent file bloat
    if len(conversations[agent_id]["messages"]) > 100:
        conversations[agent_id]["messages"] = conversations[agent_id]["messages"][-100:]
    
    save_conversations(project_dir, conversations)


def get_conversation_summary(project_dir: str, agent_id: str, max_chars: int = 200) -> str:
    """Get a summary of the agent's conversation history."""
    conversations = load_conversations(project_dir)
    
    if agent_id not in conversations:
        return "No conversation history."
    
    messages = conversations[agent_id].get("messages", [])
    
    if not messages:
        return "No messages yet."
    
    # Build a summary
    user_count = sum(1 for m in messages if m.get("role") == "user")
    assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
    
    summary = f"{len(messages)} messages ({user_count} user, {assistant_count} assistant)"
    
    # Add last message preview if available
    if messages:
        last_msg = messages[-1]
        preview = last_msg.get("content", "")[:50]
        if len(last_msg.get("content", "")) > 50:
            preview += "..."
        summary += f"\nLast: {preview}"
    
    return summary


def clear_conversation(project_dir: str, agent_id: str) -> None:
    """Clear conversation history for an agent."""
    conversations = load_conversations(project_dir)
    
    if agent_id in conversations:
        conversations[agent_id] = {
            "messages": [],
            "last_updated": datetime.now().isoformat()
        }
        save_conversations(project_dir, conversations)
