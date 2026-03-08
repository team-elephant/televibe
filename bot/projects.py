"""Project management for the Remote Cursor bot."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_projects_file() -> Path:
    """Get path to projects.json in bot directory."""
    return Path(__file__).parent / "projects.json"


def load_projects() -> list:
    """Load managed project paths."""
    projects_file = get_projects_file()
    
    if not projects_file.exists():
        return []
    
    try:
        with open(projects_file, "r") as f:
            data = json.load(f)
            return data.get("projects", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_projects(projects: list) -> None:
    """Save managed project paths."""
    projects_file = get_projects_file()
    
    data = {"projects": projects}
    
    with open(projects_file, "w") as f:
        json.dump(data, f, indent=2)


def add_project(path: str) -> bool:
    """Add a project to managed list.
    
    Returns:
        True if added successfully, False if already exists or invalid.
    """
    path = os.path.expanduser(path)
    
    # Validate path exists and is a directory
    if not os.path.isdir(path):
        return False
    
    projects = load_projects()
    
    # Check if already exists
    if path in projects:
        return False
    
    projects.append(path)
    save_projects(projects)
    
    return True


def remove_project(path: str) -> bool:
    """Remove a project from managed list.
    
    Returns:
        True if removed successfully, False if not found.
    """
    projects = load_projects()
    
    if path not in projects:
        return False
    
    projects.remove(path)
    save_projects(projects)
    
    return True


def get_projects() -> list:
    """Get list of managed projects."""
    return load_projects()


def is_valid_project(path: str) -> bool:
    """Check if a path is a valid project directory."""
    path = os.path.expanduser(path)
    return os.path.isdir(path) and os.access(path, os.R_OK)


def discover_projects_from_folder(folder_path: str) -> list:
    """Discover projects in a folder by finding git repositories.
    
    Args:
        folder_path: Path to folder to scan.
        
    Returns:
        List of project paths that contain .git directories.
    """
    folder_path = os.path.expanduser(folder_path)
    
    if not os.path.isdir(folder_path):
        return []
    
    discovered = []
    
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            
            # Check if it's a directory with .git (git repo)
            git_path = os.path.join(item_path, ".git")
            if os.path.isdir(item_path) and os.path.isdir(git_path):
                if os.access(item_path, os.R_OK):
                    discovered.append(item_path)
    except PermissionError:
        pass
    
    return discovered


def get_or_create_default_project() -> Optional[str]:
    """Get or create a default project from config.
    
    Returns:
        Path to default project or None.
    """
    from bot.config import config
    
    default = config.get_default_project_dir()
    
    if default and is_valid_project(default):
        # Add to managed projects if not already there
        projects = load_projects()
        if default not in projects:
            add_project(default)
        return default
    
    # Return first managed project if available
    projects = load_projects()
    if projects:
        return projects[0]
    
    return None
