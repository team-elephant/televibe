"""Telegram command and message handlers for the Remote Cursor bot."""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import config
from bot.cursor_cli import CursorCLI, CursorCLIError
from bot.cli_claude import ClaudeCLIError
from bot.cli_codex import CodexCLIError
from bot.cli_grok import GrokCLIError
from bot import keyboard
from bot import callbacks
from bot import groups as groups_module
from bot import models as models_module
from bot import history as history_module
from bot import conversations as conversations_module

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096

# User session data keys (shared with callbacks.py)
KEY_SELECTED_PROJECT = "selected_project"
KEY_SELECTED_AGENT = "selected_agent"
KEY_PROMPT_MODE = "prompt_mode"
KEY_AGENT_NAME_BUFFER = "agent_name_buffer"
KEY_AWAITING_PROMPT = "awaiting_prompt"
KEY_LLM_NAME_BUFFER = "llm_name_buffer"
KEY_LLM_ENDPOINT_BUFFER = "llm_endpoint_buffer"
KEY_PROJECT_PATH_BUFFER = "project_path_buffer"

# Supported agent tags
AGENT_TAGS = {
    "@cursor": "cursor",
    "@claude": "claude", 
    "@codex": "codex",
    "@grok": "grok",
}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show usage instructions."""
    if not _is_allowed_user(update):
        return

    welcome_text = """🎯 *Remote Cursor Bot*

Control AI coding agents (Cursor, Claude, Codex, Grok) from Telegram.

*How to use:*

1. *Link a project to a group:*
   `/link /path/to/project`

2. *Use agents in group chat:*
   • `@cursor your prompt` - Use Cursor AI
   • `@claude your prompt` - Use Claude AI  
   • `@codex your prompt` - Use Codex AI
   • `@grok your prompt` - Use Grok AI (MiniMax)

3. *Commands:*
   • `/status` - Show project status
   • `/unlink` - Unlink project from group
   • `/cancel` - Cancel current operation

*Note:* The bot must be added to your Telegram group with privacy mode disabled."""

    await update.message.reply_text(
        welcome_text, 
        parse_mode="Markdown"
    )


async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt command - execute read-only prompt."""
    if not _is_allowed_user(update):
        return

    project_dir, prompt_text = _extract_project_and_prompt(update.message.text, "/prompt")
    if not prompt_text:
        await update.message.reply_text(
            "Usage: `/prompt <your prompt>` or `/prompt /path/to/project <your prompt>`",
            parse_mode="Markdown"
        )
        return

    if project_dir and not _validate_project_path(update, project_dir):
        return

    await _execute_prompt(update, prompt_text, force=False, project_dir=project_dir)


async def yolo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /yolo command - execute prompt with file modifications allowed."""
    if not _is_allowed_user(update):
        return

    project_dir, prompt_text = _extract_project_and_prompt(update.message.text, "/yolo")
    if not prompt_text:
        await update.message.reply_text(
            "Usage: `/yolo <your prompt>` or `/yolo /path/to/project <your prompt>`",
            parse_mode="Markdown"
        )
        return

    if project_dir and not _validate_project_path(update, project_dir):
        return

    await _execute_prompt(update, prompt_text, force=True, project_dir=project_dir)


async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /project command - show or set default project."""
    if not _is_allowed_user(update):
        return

    text = update.message.text.strip()
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        # Show current default
        current = config.get_default_project_dir()
        runtime = config._runtime_default_project

        if runtime:
            msg = f"Current default: `{runtime}`\n(Configured: `{current}`)"
        elif current:
            msg = f"Current default: `{current}`"
        else:
            msg = "No default project set. Specify a project path in your command."

        await update.message.reply_text(msg, parse_mode="Markdown")

    elif parts[1] == "reset":
        # Reset to configured default
        config.reset_default_project_dir()
        default = config.cursor_default_project_dir or "(none)"
        await update.message.reply_text(f"Reset to configured default: `{default}`", parse_mode="Markdown")

    else:
        # Set new default
        path = parts[1].strip()
        if config.set_default_project_dir(path):
            await update.message.reply_text(f"✅ Default project set to: `{path}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Invalid directory: `{path}`", parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - check Cursor CLI availability."""
    if not _is_allowed_user(update):
        return

    await update.message.reply_text("Checking Cursor CLI status...")

    cli = CursorCLI()
    is_available, status_message = await cli.check_status()

    if is_available:
        await update.message.reply_text(f"✅ {status_message}")
    else:
        await update.message.reply_text(f"❌ {status_message}")


# ============================================================================
# Group Commands (for Telegram group chats)
# ============================================================================

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /link command - link a group to a project directory.
    
    Usage: /link /path/to/project
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    text = update.message.text.strip()
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        await update.message.reply_text(
            "Usage: `/link /path/to/project`\n\nExample: `/link /Users/admin/Projects/my-app`",
            parse_mode="Markdown"
        )
        return

    project_path = parts[1].strip()
    
    # Expand user path (e.g., ~/Projects -> /Users/admin/Projects)
    project_path = os.path.expanduser(project_path)

    if not _validate_project_path(update, project_path):
        await update.message.reply_text(
            f"❌ Invalid directory: `{project_path}`\n\nThe directory does not exist or is not accessible.",
            parse_mode="Markdown"
        )
        return

    # Link the group to the project
    if groups_module.link_group(group_id, project_path):
        await update.message.reply_text(
            f"✅ *Group Linked!*\n\n📁 Project: `{project_path}`\n\n"
            "You can now use agent tags like `@cursor`, `@claude`, `@codex`, `@grok` in this group.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to link project: `{project_path}`",
            parse_mode="Markdown"
        )


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unlink command - unlink a group from its project.
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    if groups_module.unlink_group(group_id):
        await update.message.reply_text(
            "✅ *Group Unlinked!*\n\nThis group is no longer linked to any project.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ This group is not linked to any project.",
            parse_mode="Markdown"
        )


async def group_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command in group chat - show group status.
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    status_msg = groups_module.get_group_status(group_id)
    
    # Add CLI status
    cli = CursorCLI()
    is_available, cli_status = await cli.check_status()
    
    if is_available:
        status_msg += f"\n\n✅ *CLI Status:* {cli_status}"
    else:
        status_msg += f"\n\n❌ *CLI Status:* {cli_status}"
    
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def group_models_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /models command in group chat - show model preferences.
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    models_msg = models_module.get_models_status(group_id)
    
    await update.message.reply_text(models_msg, parse_mode="Markdown")


async def group_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command in group chat - show execution history.
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    history_msg = history_module.get_history_status(group_id)
    
    await update.message.reply_text(history_msg, parse_mode="Markdown")


async def group_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /memory command in group chat - show conversation memory.
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    # Check for optional agent argument
    agent = None
    if context.args:
        agent_arg = context.args[0].lower().replace("@", "")
        if agent_arg in ["cursor", "claude", "codex", "grok"]:
            agent = agent_arg

    memory_msg = conversations_module.format_conversation_summary(group_id, agent)
    
    await update.message.reply_text(memory_msg, parse_mode="Markdown")


async def group_clear_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clearmemory command in group chat - clear conversation memory.
    """
    if not _is_owner(update):
        return

    # Get group ID
    group_id = _get_group_id(update)
    if not group_id:
        await update.message.reply_text("❌ This command must be used in a group chat.")
        return

    # Check for optional agent argument
    if context.args:
        agent_arg = context.args[0].lower().replace("@", "")
        if agent_arg in ["cursor", "claude", "codex", "grok"]:
            # Clear specific agent memory
            success = conversations_module.clear_agent_conversation(group_id, agent_arg)
            if success:
                await update.message.reply_text(
                    f"🧠 Cleared conversation memory for @{agent_arg}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"ℹ️ No conversation memory to clear for @{agent_arg}",
                    parse_mode="Markdown"
                )
            return
    
    # Clear all agent memories
    conversations_module.clear_all_conversations(group_id)
    await update.message.reply_text(
        "🧠 Cleared all conversation memory for this group",
        parse_mode="Markdown"
    )


# ============================================================================
# Tag-based Message Handling
# ============================================================================

def detect_agent_tag(text: str) -> Tuple[Optional[str], str]:
    """Detect agent tag in message and extract prompt.
    
    Args:
        text: The message text.
        
    Returns:
        Tuple of (agent_name, prompt). agent_name is None if no tag found.
    """
    text = text.strip()
    
    for tag, agent_name in AGENT_TAGS.items():
        if text.startswith(tag):
            # Remove the tag and get the prompt
            prompt = text[len(tag):].strip()
            return agent_name, prompt
    
    return None, text


def detect_change_model_command(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect /change-model command in tagged message.
    
    Syntax: @agent /change-model <model-id>
    
    Args:
        text: The message text.
        
    Returns:
        Tuple of (agent_name, model). Both None if no change-model command found.
    """
    text = text.strip()
    
    for tag, agent_name in AGENT_TAGS.items():
        if text.startswith(tag):
            # Check for /change-model command after the tag
            remaining = text[len(tag):].strip()
            if remaining.startswith("/change-model"):
                # Extract model id
                model = remaining[len("/change-model"):].strip()
                if model:
                    return agent_name, model
    
    return None, None


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages in group chats - detect agent tags.
    
    This handler processes tagged messages like:
    - @cursor analyze the code
    - @claude create a test file
    - @codex fix the bug
    - @grok explain this function
    - @claude /change-model opus-4-6
    """
    logger.info(f"[GROUP] Received message: {update.message.text if update.message else 'No message'}")
    
    if not update.message or not update.message.text:
        logger.info("[GROUP] No message or text, returning")
        return
    
    # Must be from owner
    if not _is_owner(update):
        logger.info(f"[GROUP] Not owner (user_id={update.effective_user.id}, owner_id={config.telegram_owner_id})")
        return
    
    # Get group ID
    group_id = _get_group_id(update)
    logger.info(f"[GROUP] group_id={group_id}")
    if not group_id:
        return  # Not a group chat
    
    message_text = update.message.text
    
    # First check for /change-model command
    change_agent, change_model = detect_change_model_command(message_text)
    if change_agent and change_model:
        # Handle model change request
        await _handle_change_model(update, group_id, change_agent, change_model)
        return
    
    # Check if group is linked to a project
    project_dir = groups_module.get_project_for_group(group_id)
    logger.info(f"[GROUP] project_dir={project_dir} for group {group_id}")
    if not project_dir:
        return  # Group not linked
    
    # Detect agent tag for regular prompts
    agent_name, prompt = detect_agent_tag(message_text)
    logger.info(f"[GROUP] agent_name={agent_name}, prompt={prompt[:50] if prompt else 'empty'}")
    if not agent_name or not prompt:
        return  # No valid tag found
    
    # Log the tagged message
    user_id = update.effective_user.id
    logger.info(f"[GROUP] Tagged message from user {user_id}: @{agent_name} {prompt[:50]}...")
    
    # Get the current model for this agent in this group
    model = models_module.get_current_model(group_id, agent_name)
    
    # Execute the prompt with the specified agent
    await _execute_agent_prompt(update, agent_name, prompt, project_dir, model=model, group_id=group_id)


async def _execute_agent_prompt(
    update: Update,
    agent_name: str,
    prompt: str,
    project_dir: str,
    model: Optional[str] = None,
    group_id: Optional[str] = None
) -> None:
    """Execute a prompt with a specific agent.
    
    Args:
        update: Telegram update object.
        agent_name: Name of the agent (cursor, claude, codex, grok).
        prompt: The prompt to execute.
        project_dir: The project directory to work in.
        model: The model to use (optional).
        group_id: The Telegram group ID (optional, for history tracking).
    """
    user_id = update.effective_user.id
    logger.info(f"[GROUP] Executing @{agent_name} prompt in {project_dir} with model={model}")
    
    # Track execution in history if group_id provided
    execution_id = None
    if group_id:
        execution_id = history_module.add_execution(
            group_id=group_id,
            agent=agent_name,
            prompt=prompt,
            model=model,
            status="started"
        )
        
        # Load conversation context and prepend to prompt
        context = conversations_module.get_context_for_agent(group_id, agent_name)
        if context:
            prompt = f"{context}\n\nCurrent Request: {prompt}"
            logger.info(f"[GROUP] Added conversation context ({len(context)} chars) to prompt")
    
    status_msg = await update.message.reply_text(
        f"⏳ @{agent_name} is processing your request...",
        parse_mode="Markdown"
    )
    
    try:
        # Build the CLI based on agent type, passing the model
        cli = _build_agent_cli(agent_name, project_dir, model=model)
        
        output_parts = []
        async for line in cli.execute(prompt, force=False):
            output_parts.append(line)
        
        full_output = "\n".join(output_parts)
        
        if not full_output.strip():
            full_output = "(No output)"
        
        # Send response to group
        await _send_long_message(update, status_msg, full_output, project_dir, agent_name=agent_name)
        
        # Post completion status to group
        await update.message.reply_text(
            f"✅ @{agent_name} completed.",
            parse_mode="Markdown"
        )
        
        # Save conversation to memory if group_id provided
        if group_id:
            # Add user message
            original_prompt = prompt
            if context:
                # Extract original prompt from the full prompt
                if "Current Request:" in prompt:
                    original_prompt = prompt.split("Current Request:")[1].strip()
            
            conversations_module.add_message(
                group_id=group_id,
                agent=agent_name,
                role="user",
                content=original_prompt
            )
            
            # Add assistant response (truncated if too long)
            response_content = full_output
            if len(response_content) > 4000:
                response_content = response_content[:4000] + "...(truncated)"
            
            conversations_module.add_message(
                group_id=group_id,
                agent=agent_name,
                role="assistant",
                content=response_content
            )
        
        # Update history with completion
        if group_id and execution_id:
            # Try to extract modified files from output
            files_modified = _extract_modified_files(full_output)
            history_module.update_execution(
                group_id=group_id,
                execution_id=execution_id,
                status="completed",
                files_modified=files_modified
            )
        
    except (CursorCLIError, GrokCLIError, ClaudeCLIError, CodexCLIError) as e:
        logger.error(f"[GROUP] @{agent_name} error: {str(e)}")
        await status_msg.edit_text(f"❌ @{agent_name} error: {str(e)}")
        
        # Update history with failure
        if group_id and execution_id:
            history_module.update_execution(
                group_id=group_id,
                execution_id=execution_id,
                status="failed",
                error=str(e)
            )
        
    except Exception as e:
        logger.error(f"[GROUP] Unexpected error: {str(e)}")
        await status_msg.edit_text(f"❌ Unexpected error: {str(e)}")
        
        # Update history with failure
        if group_id and execution_id:
            history_module.update_execution(
                group_id=group_id,
                execution_id=execution_id,
                status="failed",
                error=str(e)
            )


async def _handle_change_model(
    update: Update,
    group_id: str,
    agent_name: str,
    model: str
) -> None:
    """Handle /change-model command for an agent.
    
    Args:
        update: Telegram update object.
        group_id: The Telegram group ID.
        agent_name: Name of the agent (cursor, claude, codex, grok).
        model: The model identifier to change to.
    """
    logger.info(f"[GROUP] @{agent_name} /change-model {model} in group {group_id}")
    
    # Validate model is valid for this agent type
    if not models_module.is_valid_model(agent_name, model):
        available = models_module.get_available_models(agent_name)
        available_str = ", ".join(available) if available else "none"
        await update.message.reply_text(
            f"❌ Invalid model '{model}' for @{agent_name}.\n\n"
            f"Available models: {available_str}",
            parse_mode="Markdown"
        )
        return
    
    # Set the new model
    success = models_module.set_model(group_id, agent_name, model)
    
    if success:
        display_name = models_module.get_model_display_name(agent_name, model)
        await update.message.reply_text(
            f"✅ @{agent_name} model changed to {display_name}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to change @{agent_name} model",
            parse_mode="Markdown"
        )


def _build_agent_cli(agent_name: str, project_dir: str, model: Optional[str] = None):
    """Build the appropriate CLI instance for the specified agent.
    
    Args:
        agent_name: Name of the agent (cursor, claude, codex, grok).
        project_dir: The project directory.
        model: The model to use (optional).
        
    Returns:
        CLI instance (CursorCLI, ClaudeCLI, CodexCLI, or GrokCLI).
    """
    from bot.cursor_cli import CursorCLI
    from bot.cli_claude import ClaudeCLI
    from bot.cli_codex import CodexCLI
    from bot.cli_grok import GrokCLI
    
    if agent_name == "cursor":
        # Use Cursor CLI wrapper
        return CursorCLI(project_dir=project_dir, model=model)
    
    elif agent_name == "claude":
        # Use Claude CLI wrapper
        return ClaudeCLI(project_dir=project_dir, model=model)
    
    elif agent_name == "codex":
        # Use Codex CLI wrapper
        return CodexCLI(project_dir=project_dir, model=model)
    
    elif agent_name == "grok":
        # Use Grok CLI wrapper (defaults to API)
        return GrokCLI(project_dir=project_dir, model=model)
    
    else:
        # Default to cursor
        return CursorCLI(project_dir=project_dir, model=model)


# ============================================================================
# Helper Functions
# ============================================================================

def _get_group_id(update: Update) -> Optional[str]:
    """Get the group ID from a message.
    
    Args:
        update: Telegram update object.
        
    Returns:
        Group ID string or None if not in a group.
    """
    if not update.message:
        return None
    
    chat = update.message.chat
    
    # Check if this is a group chat
    if chat.type in ["group", "supergroup"]:
        return str(chat.id)
    
    return None


def _is_owner(update: Update) -> bool:
    """Check if the message is from the owner.
    
    Args:
        update: Telegram update object.
        
    Returns:
        True if sender is the owner.
    """
    if not update.message or not update.message.from_user:
        return False
    
    user_id = str(update.message.from_user.id)
    return config.is_owner(user_id)


def _extract_modified_files(output: str) -> list:
    """Extract modified file paths from CLI output.
    
    This is a best-effort extraction that looks for common patterns
    in CLI output indicating file modifications.
    
    Args:
        output: The CLI output text.
        
    Returns:
        List of file paths that may have been modified.
    """
    import re
    
    files = []
    
    # Common patterns for file modifications
    patterns = [
        # "Modified: /path/to/file"
        r'[Mm]odified:\s*([^\s\n]+)',
        # "Created: /path/to/file"  
        r'[Cc]reated:\s*([^\s\n]+)',
        # "Edited: /path/to/file"
        r'[Ee]dited:\s*([^\s\n]+)',
        # "Writing to /path/to/file"
        r'[Ww]riting to\s+([^\s\n]+)',
        # "File: /path/to/file"
        r'[Ff]ile:\s*([^\s\n]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, output)
        for match in matches:
            # Clean up the path
            path = match.strip()
            if path and path not in files:
                files.append(path)
    
    return files


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle direct text messages - prompts or agent creation flow."""
    from bot import llms as llms_module
    from bot import projects as projects_module
    
    if not _is_allowed_user(update):
        return

    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    logger.info(f"[TELEGRAM] Received message from user {user_id}")

    # Ignore commands (but handle special cases)
    if update.message.text.startswith("/"):
        if update.message.text.strip() == "/cancel":
            await handle_cancel(update, context)
        return

    user_data = context.user_data
    text = update.message.text.strip()
    
    # Check if we're in agent creation flow
    awaiting = user_data.get(KEY_AWAITING_PROMPT)
    
    if awaiting == "agent_name":
        # Store the agent name and ask for model family (simplified 2-step flow)
        user_data[KEY_AGENT_NAME_BUFFER] = text
        user_data[KEY_AWAITING_PROMPT] = "agent_model"
        
        await update.message.reply_text(
            f"📝 *Agent Name:* {text}\n\nSelect a model family:",
            parse_mode="Markdown",
            reply_markup=keyboard.model_family_keyboard()
        )
        return
    
    # Handle LLM creation flow
    if awaiting == "llm_name":
        # Store the LLM name and ask for endpoint
        user_data[KEY_LLM_NAME_BUFFER] = text
        user_data[KEY_AWAITING_PROMPT] = "llm_endpoint"
        
        await update.message.reply_text(
            f"📝 *LLM Name:* {text}\n\nEnter the API endpoint URL:",
            parse_mode="Markdown"
        )
        return
    
    if awaiting == "llm_endpoint":
        # Validate URL format properly
        endpoint = text.strip()
        
        # Check basic prefix
        if not endpoint.startswith(("http://", "https://")):
            await update.message.reply_text(
                "❌ Invalid endpoint. Must start with http:// or https://",
                reply_markup=keyboard.back_keyboard("menu:custom_llm")
            )
            return
        
        # Check if it's a valid URL format
        try:
            from urllib.parse import urlparse
            parsed = urlparse(endpoint)
            if not parsed.scheme or not parsed.netloc:
                await update.message.reply_text(
                    "❌ Invalid endpoint URL format.",
                    reply_markup=keyboard.back_keyboard("menu:custom_llm")
                )
                return
        except Exception:
            await update.message.reply_text(
                "❌ Invalid endpoint URL format.",
                reply_markup=keyboard.back_keyboard("menu:custom_llm")
            )
            return
        
        # Store the endpoint and ask for API key
        user_data[KEY_LLM_ENDPOINT_BUFFER] = endpoint
        user_data[KEY_AWAITING_PROMPT] = "llm_api_key"
        
        await update.message.reply_text(
            f"🔗 *Endpoint:* {endpoint}\n\nEnter the API key:",
            parse_mode="Markdown"
        )
        return
    
    if awaiting == "llm_api_key":
        # Create the LLM
        llm_name = user_data.get(KEY_LLM_NAME_BUFFER)
        llm_endpoint = user_data.get(KEY_LLM_ENDPOINT_BUFFER)
        
        if not llm_name or not llm_endpoint:
            await update.message.reply_text(
                "❌ Error: Missing LLM information. Please start over.",
                reply_markup=keyboard.main_menu_keyboard()
            )
            return
        
        llm = llms_module.create_llm(llm_name, llm_endpoint, text)
        
        # Clear buffers
        user_data.pop(KEY_LLM_NAME_BUFFER, None)
        user_data.pop(KEY_LLM_ENDPOINT_BUFFER, None)
        user_data.pop(KEY_AWAITING_PROMPT, None)
        
        await update.message.reply_text(
            f"✅ *LLM Created!*\n\n*Name:* {llm['name']}\n*Endpoint:* {llm['endpoint']}",
            parse_mode="Markdown",
            reply_markup=keyboard.custom_llm_menu_keyboard()
        )
        return
    
    # Handle project path input
    if awaiting == "project_path":
        project_path = text.strip()
        
        # Expand user path
        project_path = os.path.expanduser(project_path)
        
        # Validate and add project
        if not os.path.isdir(project_path):
            await update.message.reply_text(
                f"❌ Invalid path: `{project_path}`\n\nThe directory does not exist.",
                parse_mode="Markdown",
                reply_markup=keyboard.back_keyboard("menu:default_project")
            )
            return
        
        if not os.access(project_path, os.R_OK):
            await update.message.reply_text(
                f"❌ Cannot access: `{project_path}`\n\nPermission denied.",
                parse_mode="Markdown",
                reply_markup=keyboard.back_keyboard("menu:default_project")
            )
            return
        
        # Add project
        if projects_module.add_project(project_path):
            await update.message.reply_text(
                f"✅ *Project Added!*\n\n*Path:* `{project_path}`",
                parse_mode="Markdown",
                reply_markup=keyboard.back_keyboard("menu:default_project")
            )
        else:
            await update.message.reply_text(
                f"⚠️ *Project Already Exists*\n\n`{project_path}` is already in your list.",
                parse_mode="Markdown",
                reply_markup=keyboard.back_keyboard("menu:default_project")
            )
        
        user_data.pop(KEY_AWAITING_PROMPT, None)
        return
    
    # Check if user has selected an agent - execute prompt
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    agent_id = user_data.get(KEY_SELECTED_AGENT)
    
    if not project_dir:
        await update.message.reply_text(
            "❌ No project selected. Use the menu to select a default project first.",
            reply_markup=keyboard.main_menu_keyboard()
        )
        return
    
    if not agent_id:
        await update.message.reply_text(
            "❌ No agent selected. Use Vibe Code → Pick Agent to select an agent first.",
            reply_markup=keyboard.vibe_code_menu_keyboard()
        )
        return
    
    # Execute prompt with selected agent
    force = user_data.get(KEY_PROMPT_MODE, False)
    await _execute_prompt_with_agent(update, text, project_dir, agent_id, force)


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command during conversation flows."""
    if not _is_allowed_user(update):
        return
    
    user_data = context.user_data
    
    # Clear any awaiting state
    user_data.pop(KEY_AWAITING_PROMPT, None)
    user_data.pop(KEY_AGENT_NAME_BUFFER, None)
    
    await update.message.reply_text(
        "❌ Cancelled.",
        reply_markup=keyboard.main_menu_keyboard()
    )


async def _execute_prompt_with_agent(
    update: Update,
    prompt: str,
    project_dir: str,
    agent_id: str,
    force: bool
) -> None:
    """Execute a prompt using a specific agent."""
    from bot import agents as agents_module
    from bot import llms as llms_module
    from bot import projects as projects_module
    
    user_id = update.effective_user.id
    logger.info(f"[TELEGRAM] Executing prompt from user {user_id} (project: {project_dir}, agent: {agent_id}, force: {force})")
    
    status_msg = await update.message.reply_text(
        "⏳ Processing your prompt...",
        parse_mode=None
    )
    
    # Load agents to get the model
    agents = agents_module.load_agents(project_dir)
    agent = next((a for a in agents if a["id"] == agent_id), None)
    
    if not agent:
        await status_msg.edit_text("❌ Agent not found.")
        return
    
    cli = CursorCLI(
        project_dir=project_dir, 
        model=agent["model"],
        provider=agent.get("provider", "cursor"),
        llm_id=agent.get("llm_id")
    )

    try:
        output_parts = []
        async for line in cli.execute(prompt, force=force):
            output_parts.append(line)

        full_output = "\n".join(output_parts)

        if not full_output.strip():
            full_output = "(No output)"

        logger.info(f"[TELEGRAM] Sending response to user {user_id} ({len(full_output)} chars)")
        
        await _send_long_message(update, status_msg, full_output, project_dir, agent_name=agent["name"])

    except CursorCLIError as e:
        logger.error(f"[TELEGRAM] Cursor CLI error: {str(e)}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

    except Exception as e:
        logger.error(f"[TELEGRAM] Unexpected error: {str(e)}")
        await status_msg.edit_text(f"❌ Unexpected error: {str(e)}")


async def _execute_prompt(
    update: Update,
    prompt: str,
    force: bool,
    project_dir: Optional[str]
) -> None:
    """Execute a prompt and send response back to Telegram.

    Args:
        update: Telegram update object.
        prompt: The prompt to execute.
        force: Whether to allow file modifications.
        project_dir: Optional project directory to run in.
    """
    user_id = update.effective_user.id
    logger.info(f"[TELEGRAM] Executing prompt from user {user_id} (project: {project_dir}, force: {force})")
    
    status_msg = await update.message.reply_text(
        "⏳ Processing your prompt...",
        parse_mode=None
    )

    # Use specified project, or fall back to default
    effective_project_dir = project_dir or config.get_default_project_dir()

    if not effective_project_dir:
        await status_msg.edit_text(
            "❌ No project directory specified. Use `/project <path>` to set a default,\n"
            "or specify a project in your command: `/prompt /path/to/project <prompt>`",
            parse_mode="Markdown"
        )
        return

    cli = CursorCLI(project_dir=effective_project_dir)

    try:
        output_parts = []
        async for line in cli.execute(prompt, force=force):
            output_parts.append(line)

        full_output = "\n".join(output_parts)

        if not full_output.strip():
            full_output = "(No output)"

        logger.info(f"[TELEGRAM] Sending response to user {user_id} ({len(full_output)} chars)")
        
        await _send_long_message(update, status_msg, full_output, effective_project_dir)

    except CursorCLIError as e:
        logger.error(f"[TELEGRAM] Cursor CLI error: {str(e)}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

    except Exception as e:
        logger.error(f"[TELEGRAM] Unexpected error: {str(e)}")
        await status_msg.edit_text(f"❌ Unexpected error: {str(e)}")


async def _send_long_message(
    update: Update,
    status_msg,
    text: str,
    project_dir: Optional[str] = None,
    agent_name: Optional[str] = None
) -> None:
    """Send a message, splitting if it exceeds Telegram's length limit.

    Args:
        update: Telegram update object.
        status_msg: The status message to edit or reply to.
        text: The text to send.
        project_dir: The project directory used (for context).
        agent_name: The agent name used (for context).
    """
    # Change status to show agent is thinking
    thinking_text = f"@{agent_name} thinking..." if agent_name else "thinking..."
    await status_msg.edit_text(thinking_text, parse_mode="Markdown")

    if len(text) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text)
    else:
        # Split into chunks
        chunks = _split_message(text)
        for i, chunk in enumerate(chunks):
            if i == 0:
                await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(f"[{i + 1}/{len(chunks)}]\n{chunk}")


def _split_message(text: str) -> list[str]:
    """Split a message into chunks that fit Telegram's limit.

    Args:
        text: The text to split.

    Returns:
        List of text chunks.
    """
    chunks = []
    current_chunk = ""

    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH - 10:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _extract_project_and_prompt(text: str, command: str) -> tuple[Optional[str], str]:
    """Extract optional project path and prompt text from a command.

    Args:
        text: The full message text.
        command: The command prefix (e.g., '/prompt').

    Returns:
        Tuple of (project_dir, prompt_text). project_dir is None if not specified.
    """
    # Pattern: /command /path/to/project <prompt>
    # The project path must start with / and be a valid-looking path
    pattern = rf"^{re.escape(command)}\s+(/\S+)\s+(.+)$"
    match = re.match(pattern, text, re.DOTALL)

    if match:
        project_path = match.group(1).strip()
        prompt = match.group(2).strip()
        return project_path, prompt

    # Fallback: just extract prompt (no project path)
    prompt = _extract_prompt_simple(text, command)
    return None, prompt


def _extract_prompt_simple(text: str, command: str) -> str:
    """Extract prompt text from a command message (simple version).

    Args:
        text: The full message text.
        command: The command prefix.

    Returns:
        The extracted prompt, or empty string if not found.
    """
    pattern = rf"^{re.escape(command)}\s*`?(.+?)`?\s*$"
    match = re.match(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    pattern = rf"^{re.escape(command)}\s*(.+)$"
    match = re.match(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    return ""


def _validate_project_path(update: Update, path: str) -> bool:
    """Validate that a project path exists and is a directory.

    Args:
        update: Telegram update object.
        path: The path to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not Path(path).is_dir():
        return False

    if not os.access(path, os.R_OK):
        return False

    return True


def _is_allowed_user(update: Update) -> bool:
    """Check if the user is allowed to use the bot.

    Args:
        update: Telegram update object.

    Returns:
        True if user is allowed, False otherwise.
    """
    if not update.message or not update.message.from_user:
        return False

    user_id = str(update.message.from_user.id)
    return config.is_user_allowed(user_id)
