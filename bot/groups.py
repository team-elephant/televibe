"""Group management for the Remote Cursor Telegram Bot.

Manages Telegram group chat to project directory mappings.
Each group can be linked to a specific project directory.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_groups_file() -> Path:
    """Get path to groups.json in bot directory."""
    return Path(__file__).parent / "groups.json"


def load_groups() -> list:
    """Load group mappings from groups.json."""
    groups_file = get_groups_file()
    
    if not groups_file.exists():
        return []
    
    try:
        with open(groups_file, "r") as f:
            data = json.load(f)
            return data.get("groups", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_groups(groups: list) -> None:
    """Save group mappings to groups.json."""
    groups_file = get_groups_file()
    
    data = {"groups": groups}
    
    with open(groups_file, "w") as f:
        json.dump(data, f, indent=2)


def link_group(group_id: str, project_path: str) -> bool:
    """Link a Telegram group to a project directory.
    
    Args:
        group_id: The Telegram group ID.
        project_path: Path to the project directory.
        
    Returns:
        True if linked successfully, False if project path is invalid.
    """
    # Validate project path
    project_path = os.path.expanduser(project_path)
    if not os.path.isdir(project_path):
        return False
    
    if not os.access(project_path, os.R_OK):
        return False
    
    groups = load_groups()
    
    # Check if group already exists
    for group in groups:
        if group["group_id"] == group_id:
            # Update existing group
            group["project_path"] = project_path
            group["project_name"] = os.path.basename(project_path)
            group["linked_at"] = datetime.now().isoformat()
            save_groups(groups)
            return True
    
    # Create new group entry
    new_group = {
        "group_id": group_id,
        "project_path": project_path,
        "project_name": os.path.basename(project_path),
        "linked_at": datetime.now().isoformat()
    }
    
    groups.append(new_group)
    save_groups(groups)
    
    return True


def unlink_group(group_id: str) -> bool:
    """Unlink a Telegram group from its project.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        True if unlinked successfully, False if group not found.
    """
    groups = load_groups()
    
    # Find and remove group
    original_count = len(groups)
    groups = [g for g in groups if g["group_id"] != group_id]
    
    if len(groups) == original_count:
        return False  # Group not found
    
    save_groups(groups)
    return True


def get_group(group_id: str) -> Optional[dict]:
    """Get group info by group ID.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Group info dict or None if not found.
    """
    groups = load_groups()
    return next((g for g in groups if g["group_id"] == group_id), None)


def get_project_for_group(group_id: str) -> Optional[str]:
    """Get the project path for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Project path or None if not linked.
    """
    group = get_group(group_id)
    if group:
        return group.get("project_path")
    return None


def is_group_linked(group_id: str) -> bool:
    """Check if a group is linked to a project.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        True if linked, False otherwise.
    """
    return get_group(group_id) is not None


def list_groups() -> list:
    """List all linked groups.
    
    Returns:
        List of group info dicts.
    """
    return load_groups()


def get_group_status(group_id: str) -> str:
    """Get status message for a group.
    
    Args:
        group_id: The Telegram group ID.
        
    Returns:
        Status message string.
    """
    group = get_group(group_id)
    
    if not group:
        return "This group is not linked to any project.\n\nUse /link /path/to/project to link a project."
    
    return (
        f"📁 *Project:* `{group['project_path']}`\n"
        f"📅 *Linked:* {group['linked_at']}"
    )
