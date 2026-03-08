"""Callback query handlers for inline keyboard interactions."""

import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from bot.config import config
from bot import keyboard
from bot import agents as agents_module
from bot import llms as llms_module
from bot import projects as projects_module
from bot.cursor_cli import CursorCLI, CursorCLIError

# Conversation states for multi-step flows
(AGENT_NAME, AGENT_MODEL) = range(2)

# User session data keys
KEY_SELECTED_PROJECT = "selected_project"
KEY_SELECTED_AGENT = "selected_agent"
KEY_PROMPT_MODE = "prompt_mode"  # False = read-only, True = yolo
KEY_AGENT_NAME_BUFFER = "agent_name_buffer"
KEY_AWAITING_PROMPT = "awaiting_prompt"


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = str(update.effective_user.id)
    
    # Get user context
    user_data = context.user_data
    
    # Route to appropriate handler
    if callback_data == "menu:main":
        await show_main_menu(update, query)
    elif callback_data == "menu:vibe_code":
        await show_vibe_code_menu(update, query)
    elif callback_data == "menu:pick_agent":
        await show_pick_agent_menu(update, query, user_data)
    elif callback_data == "menu:create_agent":
        await show_model_family_selection(update, query, user_data)
    elif callback_data == "menu:default_project":
        await show_default_project_menu(update, query, user_data)
    elif callback_data == "menu:status":
        await show_status_menu(update, query, user_data)
    elif callback_data == "menu:help":
        await show_help_menu(update, query)
    elif callback_data == "menu:custom_llm":
        await show_custom_llm_menu(update, query)
    elif callback_data == "menu:quick_prompt":
        await start_quick_prompt(update, query, user_data)
    elif callback_data == "llm:list":
        await show_llm_list(update, query)
    elif callback_data == "llm:add":
        await start_add_llm(update, query, user_data)
    elif callback_data == "llm:remove":
        await show_remove_llm_menu(update, query)
    elif callback_data.startswith("llm:delete:"):
        llm_id = callback_data.split(":", 2)[2]
        await show_remove_llm_confirm(update, query, llm_id)
    elif callback_data.startswith("llm:confirm_remove:"):
        llm_id = callback_data.split(":", 1)[1]
        await confirm_remove_llm(update, query, llm_id)
    elif callback_data == "menu:delete_agent":
        await show_delete_agent_menu(update, query, user_data)
    elif callback_data.startswith("agent:select:"):
        agent_id = callback_data.split(":", 2)[2]
        await select_agent(update, query, user_data, agent_id)
    elif callback_data.startswith("agent:delete:"):
        agent_id = callback_data.split(":", 2)[2]
        await show_delete_agent_confirm(update, query, user_data, agent_id)
    elif callback_data.startswith("agent:confirm_delete:"):
        agent_id = callback_data.split(":", 1)[1]
        await confirm_delete_agent(update, query, user_data, agent_id)
    elif callback_data.startswith("agent:prompt:"):
        agent_id = callback_data.split(":", 2)[2]
        await start_prompt_mode(update, query, user_data, agent_id)
    elif callback_data.startswith("agent:status:"):
        agent_id = callback_data.split(":", 2)[2]
        await show_agent_status_detail(update, query, user_data, agent_id)
    elif callback_data.startswith("model:"):
        model_id = callback_data.split(":", 1)[1]
        await select_model(update, query, user_data, model_id)
    elif callback_data.startswith("model_family:"):
        family = callback_data.split(":", 1)[1]
        await show_model_versions(update, query, user_data, family)
    elif callback_data.startswith("project:select:"):
        project_path = callback_data.split(":", 2)[2]
        await select_project(update, query, user_data, project_path)
    elif callback_data == "project:add":
        await start_add_project(update, query, user_data)
    elif callback_data == "project:remove":
        await show_remove_project_menu(update, query)
    elif callback_data == "project:discover":
        await discover_projects(update, query)
    elif callback_data.startswith("project:add_discovered:"):
        project_path = callback_data.split(":", 1)[1]
        await add_discovered_project(update, query, project_path)
    elif callback_data.startswith("project:delete:"):
        project_path = callback_data.split(":", 2)[2]
        await confirm_remove_project(update, query, project_path)
    elif callback_data.startswith("prompt:mode:"):
        mode = callback_data.split(":", 2)[2] == "true"
        await set_prompt_mode(update, query, user_data, mode)
    else:
        await query.edit_message_text(f"Unknown action: {callback_data}")


async def show_main_menu(update: Update, query) -> None:
    """Show the main menu."""
    text = """🎯 *Remote Cursor Bot*

Control Cursor on your MacBook remotely from Telegram.

Select an option below:"""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.main_menu_keyboard())


async def show_vibe_code_menu(update: Update, query) -> None:
    """Show the Vibe Code submenu."""
    text = """🎯 *Vibe Code*

Choose an action:"""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.vibe_code_menu_keyboard())


async def show_pick_agent_menu(update: Update, query, user_data: dict) -> None:
    """Show the Pick Agent menu with available agents_module."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Load agents for this project
    agents = agents_module.load_agents(project_dir)
    selected_agent_id = user_data.get(KEY_SELECTED_AGENT)
    
    if not agents:
        text = """👤 *No Agents*

No agents found for this project. Create one first!"""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    text = """👤 *Pick Agent*

Select an agent:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.agents_keyboard(agents, selected_agent_id)
    )


async def start_create_agent(update: Update, query, user_data: dict) -> None:
    """Start the Create Agent flow - show model family selection."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Ask for agent name first
    text = """➕ *Create Agent*

Please enter a name for your new agent.

Send /cancel to go back."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
    
    # Set flag indicating we're awaiting agent name
    user_data[KEY_AWAITING_PROMPT] = "agent_name"


async def show_model_family_selection(update: Update, query, user_data: dict) -> None:
    """Show model family selection for Create Agent flow."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Check if we have an agent name
    agent_name = user_data.get(KEY_AGENT_NAME_BUFFER)
    
    if not agent_name:
        # No agent name yet, ask for it first
        text = """➕ *Create Agent*

Please enter a name for your new agent first.

Send /cancel to go back."""
        
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    text = """🔹 *Select Model Family*

Choose a model family for your agent:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.model_family_keyboard()
    )


async def select_agent(update: Update, query, user_data: dict, agent_id: str) -> None:
    """Handle agent selection."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Load agents and find selected
    agents = agents_module.load_agents(project_dir)
    agent = next((a for a in agents if a["id"] == agent_id), None)
    
    if not agent:
        await query.edit_message_text("❌ Agent not found.", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    # Store selected agent
    user_data[KEY_SELECTED_AGENT] = agent_id
    
    text = f"""✅ *Agent Selected*

*Name:* {agent['name']}
*Model:* {agent['model']}

Choose an action:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.selected_agent_keyboard(agent_id)
    )


async def show_model_versions(update: Update, query, user_data: dict, family: str) -> None:
    """Show model versions for a specific family."""
    custom_llms = llms_module.load_llms()
    
    text = f"""🔹 *{family.title()}*

Select a model version:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.model_versions_keyboard(family, custom_llms)
    )


async def select_model(update: Update, query, user_data: dict, model_id: str) -> None:
    """Handle model selection during Create Agent flow."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    agent_name = user_data.get(KEY_AGENT_NAME_BUFFER)
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    if not agent_name:
        await query.edit_message_text("❌ No agent name found. Please start over.", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    # Parse model_id (format: provider:model or custom:llm_id)
    provider = "cursor"
    actual_model = model_id
    llm_id = None
    
    if model_id.startswith("custom:"):
        # Custom LLM
        provider = "custom"
        llm_id = model_id.replace("custom:", "")
        # Get the custom LLM to find its details
        custom_llm = llms_module.get_llm(llm_id)
        if custom_llm:
            actual_model = f"{custom_llm['name']}"
        else:
            actual_model = "custom"
    elif ":" in model_id:
        # OpenAI, Anthropic, etc.
        parts = model_id.split(":", 1)
        provider = parts[0]
        actual_model = parts[1]
    
    # Create the agent
    agent = agents_module.create_agent(project_dir, agent_name, actual_model, provider, llm_id)
    
    # Clear buffer
    user_data.pop(KEY_AGENT_NAME_BUFFER, None)
    user_data.pop(KEY_AWAITING_PROMPT, None)
    
    # Auto-select this agent
    user_data[KEY_SELECTED_AGENT] = agent["id"]
    
    text = f"""✅ *Agent Created!*

*Name:* {agent['name']}
*Model:* {agent['model']}

This agent is now selected! You can start prompting."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.selected_agent_keyboard(agent["id"]))


async def show_default_project_menu(update: Update, query, user_data: dict) -> None:
    """Show the Projects selection menu."""
    # Get managed projects
    projects = projects_module.load_projects()
    
    # Add configured default if not in list
    configured = config.get_default_project_dir()
    if configured and configured not in projects:
        projects.insert(0, configured)
    
    # Get current selection
    current = user_data.get(KEY_SELECTED_PROJECT) or configured
    
    if not projects:
        text = """📁 *No Projects*

Add a project using the "➕ Add Project" button."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.projects_keyboard([], current))
        return
    
    text = """📁 *Projects*

Select a project:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.projects_keyboard(projects, current)
    )


async def select_project(update: Update, query, user_data: dict, project_path: str) -> None:
    """Handle project selection."""
    # Validate the path exists
    if not Path(project_path).is_dir():
        await query.edit_message_text(f"❌ Directory not found: {project_path}", reply_markup=keyboard.back_keyboard("menu:default_project"))
        return
    
    if not os.access(project_path, os.R_OK):
        await query.edit_message_text(f"❌ Cannot access: {project_path}", reply_markup=keyboard.back_keyboard("menu:default_project"))
        return
    
    # Store selected project
    user_data[KEY_SELECTED_PROJECT] = project_path
    
    text = f"""✅ *Project Selected*

Default project set to:
`{project_path}`"""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))


async def show_status_menu(update: Update, query, user_data: dict) -> None:
    """Show status of agents in the project."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Check Cursor CLI status
    cli = CursorCLI(project_dir=project_dir)
    is_available, status_message = await cli.check_status()
    
    # Load agents
    agents = agents_module.load_agents(project_dir)
    selected_agent_id = user_data.get(KEY_SELECTED_AGENT)
    
    if not is_available:
        text = f"""📊 *Status*

❌ *Cursor CLI:* Not available
{status_message}
"""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Build status message
    text = """📊 *Status*

✅ *Cursor CLI:* Available
"""
    
    if agents:
        text += f"\n*Agents:* ({len(agents)} total)\n"
        for agent in agents:
            marker = "✓" if agent["id"] == selected_agent_id else " "
            text += f"{marker} {agent['name']} - {agent['model']}\n"
    else:
        text += "\n*No agents created yet.*\n"
    
    text += f"\n*Project:* `{project_dir}`"
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))


async def start_prompt_mode(update: Update, query, user_data: dict, agent_id: str) -> None:
    """Start prompt mode for selected agent."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        return
    
    agent = agents_module.get_agent(project_dir, agent_id)
    
    if not agent:
        await query.edit_message_text("❌ Agent not found.", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    text = f"""💬 *Prompt Mode*

*Agent:* {agent['name']}
*Model:* {agent['model']}

Send your prompt below, or choose the mode:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.prompt_mode_keyboard()
    )


async def show_agent_status_detail(update: Update, query, user_data: dict, agent_id: str) -> None:
    """Show detailed status for a specific agent."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        return
    
    agent = agents_module.get_agent(project_dir, agent_id)
    
    if not agent:
        await query.edit_message_text("❌ Agent not found.", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    # Get conversation summary
    summary = agents_module.get_conversation_summary(project_dir, agent_id)
    
    # Get provider display name
    provider = agent.get('provider', 'cursor')
    provider_display = {
        'cursor': 'Cursor',
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'custom': 'Custom LLM'
    }.get(provider, provider)
    
    text = f"""📊 *Agent Status*

*Name:* {agent['name']}
*Provider:* {provider_display}
*Model:* {agent['model']}
*Created:* {agent.get('created_at', 'Unknown')}

*Conversation:*
{summary}"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.back_keyboard(f"agent:select:{agent_id}")
    )


async def show_delete_agent_menu(update: Update, query, user_data: dict) -> None:
    """Show menu to select which agent to delete."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    agents = agents_module.load_agents(project_dir)
    
    if not agents:
        text = """🗑️ *Delete Agent*

No agents to delete. Create one first!"""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    text = """🗑️ *Delete Agent*

Select an agent to delete:"""
    
    # Create keyboard with delete buttons
    keyboard = []
    for agent in agents:
        keyboard.append([InlineKeyboardButton(f"🗑️ {agent['name']}", callback_data=f"agent:delete:{agent['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:vibe_code")])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_delete_agent_confirm(update: Update, query, user_data: dict, agent_id: str) -> None:
    """Show confirmation before deleting an agent."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        return
    
    agent = agents_module.get_agent(project_dir, agent_id)
    
    if not agent:
        await query.edit_message_text("❌ Agent not found.", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    text = f"""❓ *Confirm Delete*

Are you sure you want to delete this agent?

*Name:* {agent['name']}
*Model:* {agent['model']}"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.confirm_keyboard(
            f"agent:confirm_delete:{agent_id}",
            "menu:delete_agent"
        )
    )


async def confirm_delete_agent(update: Update, query, user_data: dict, agent_id: str) -> None:
    """Confirm and delete an agent."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        return
    
    agent = agents_module.get_agent(project_dir, agent_id)
    
    if not agent:
        await query.edit_message_text("❌ Agent not found.", reply_markup=keyboard.back_keyboard("menu:vibe_code"))
        return
    
    # Delete the agent
    agents_module.delete_agent(project_dir, agent_id)
    
    # Clear selection if deleted agent was selected
    if user_data.get(KEY_SELECTED_AGENT) == agent_id:
        user_data.pop(KEY_SELECTED_AGENT, None)
    
    text = f"""✅ *Agent Deleted*

*Name:* {agent['name']}
*Model:* {agent['model']}

The agent has been removed."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:vibe_code"))


async def show_custom_llm_menu(update: Update, query) -> None:
    """Show Custom LLM Model submenu."""
    text = """🤖 *Custom LLM Model*

Manage custom LLM configurations for your agents.

Select an action:"""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.custom_llm_menu_keyboard())


async def show_llm_list(update: Update, query) -> None:
    """Show list of configured LLMs."""
    llms = llms_module.load_llms()
    
    if not llms:
        text = """📋 *LLM List*

No custom LLMs configured.

Add one using "➕ Add LLM"!"""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.custom_llm_menu_keyboard())
        return
    
    text = """📋 *Custom LLMs*

"""
    for llm in llms:
        text += f"• {llm['name']}\n"
        text += f"  Endpoint: {llm['endpoint']}\n\n"
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.custom_llm_menu_keyboard())


async def start_add_llm(update: Update, query, user_data: dict) -> None:
    """Start the Add LLM flow - ask for LLM name."""
    text = """➕ *Add Custom LLM*

Please enter a name for your LLM (e.g., "OpenAI GPT-4").

Send /cancel to go back."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:custom_llm"))
    
    # Set flag indicating we're awaiting LLM name
    user_data[KEY_AWAITING_PROMPT] = "llm_name"


async def show_remove_llm_menu(update: Update, query) -> None:
    """Show menu to select which LLM to remove."""
    llms = llms_module.load_llms()
    
    if not llms:
        text = """🗑️ *Remove LLM*

No custom LLMs to remove."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.custom_llm_menu_keyboard())
        return
    
    text = """🗑️ *Remove LLM*

Select an LLM to remove:"""
    
    # Create keyboard with remove buttons
    kb = []
    for llm in llms:
        kb.append([InlineKeyboardButton(f"🗑️ {llm['name']}", callback_data=f"llm:delete:{llm['id']}")])
    
    kb.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:custom_llm")])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def show_remove_llm_confirm(update: Update, query, llm_id: str) -> None:
    """Show confirmation before removing an LLM."""
    llm = llms_module.get_llm(llm_id)
    
    if not llm:
        await query.edit_message_text("❌ LLM not found.", reply_markup=keyboard.custom_llm_menu_keyboard())
        return
    
    text = f"""❓ *Confirm Remove*

Are you sure you want to remove this LLM?

*Name:* {llm['name']}
*Endpoint:* {llm['endpoint']}"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.confirm_keyboard(
            f"llm:confirm_remove:{llm_id}",
            "llm:remove"
        )
    )


async def confirm_remove_llm(update: Update, query, llm_id: str) -> None:
    """Confirm and remove an LLM."""
    llm = llms_module.get_llm(llm_id)
    
    if not llm:
        await query.edit_message_text("❌ LLM not found.", reply_markup=keyboard.custom_llm_menu_keyboard())
        return
    
    # Delete the LLM
    llms_module.delete_llm(llm_id)
    
    text = f"""✅ *LLM Removed*

*Name:* {llm['name']}
*Endpoint:* {llm['endpoint']}

The LLM has been removed."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.custom_llm_menu_keyboard())


# User session keys for LLM and Project creation
KEY_LLM_NAME_BUFFER = "llm_name_buffer"
KEY_LLM_ENDPOINT_BUFFER = "llm_endpoint_buffer"
KEY_PROJECT_PATH_BUFFER = "project_path_buffer"


async def start_add_project(update: Update, query, user_data: dict) -> None:
    """Start the Add Project flow - ask for project path."""
    text = """➕ *Add Project*

Please enter the full path to your project folder.

Example: /Users/admin/Projects/my-project

Send /cancel to go back."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:default_project"))
    
    # Set flag indicating we're awaiting project path
    user_data[KEY_AWAITING_PROMPT] = "project_path"


async def show_remove_project_menu(update: Update, query) -> None:
    """Show menu to select which project to remove."""
    projects = projects_module.load_projects()
    
    if not projects:
        text = """🗑️ *Remove Project*

No managed projects to remove."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:default_project"))
        return
    
    text = """🗑️ *Remove Project*

Select a project to remove:"""
    
    await query.edit_message_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.projects_remove_keyboard(projects)
    )


async def confirm_remove_project(update: Update, query, project_path: str) -> None:
    """Confirm and remove a project."""
    # Remove from managed list
    removed = projects_module.remove_project(project_path)
    
    if not removed:
        await query.edit_message_text(
            "❌ Project not found in managed list.", 
            reply_markup=keyboard.back_keyboard("menu:default_project")
        )
        return
    
    text = f"""✅ *Project Removed*

The following project has been removed:
`{project_path}`"""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:default_project"))


async def discover_projects(update: Update, query) -> None:
    """Discover projects by scanning for git repositories."""
    # Get user's projects folder
    projects_folder = os.path.expanduser("~/Projects")
    
    if not os.path.isdir(projects_folder):
        text = """🔍 *Discover Projects*

Could not find `~/Projects` folder.

Make sure you have a Projects folder in your home directory."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:default_project"))
        return
    
    # Discover projects
    discovered = projects_module.discover_projects_from_folder(projects_folder)
    existing = projects_module.load_projects()
    
    text = f"""🔍 *Discover Projects*

Scanned: `{projects_folder}`
Found: {len(discovered)} git projects"""

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.discover_projects_keyboard(discovered, existing))


async def add_discovered_project(update: Update, query, project_path: str) -> None:
    """Add a discovered project."""
    # Validate the path exists before adding
    if not os.path.isdir(project_path):
        await query.edit_message_text(
            f"❌ Directory not found: `{project_path}`",
            reply_markup=keyboard.back_keyboard("menu:default_project")
        )
        return
    
    # Try to add the project
    added = projects_module.add_project(project_path)
    
    if added:
        display_name = project_path.split("/")[-1]
        text = f"""✅ *Project Added!*

*Name:* {display_name}
*Path:* `{project_path}`"""
    else:
        # Check if it's already in the list or just invalid
        existing = projects_module.load_projects()
        if project_path in existing:
            text = f"""⚠️ *Project Already Exists*

`{project_path}` is already in your list."""
        else:
            text = f"""❌ *Cannot Add Project*

Could not add `{project_path}`. Please check permissions."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:default_project"))


async def show_help_menu(update: Update, query) -> None:
    """Show help with command hierarchy."""
    text = """❓ *Help*

*Main Menu:*
• 🎯 Vibe Code - Create and use agents
• 📁 Default Project - Set project directory
• 📊 Status - View agent status
• ❓ Help - Show this message

*Vibe Code:*
• Pick Agent - Select an existing agent
• Create Agent - Make a new agent
• Delete Agent - Remove an agent

*Using Agents:*
1. Select or create an agent
2. Choose Read Only or Read-Write mode
3. Send your prompt!

*Note:* Set a default project first using 📁 Default Project."""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))


async def set_prompt_mode(update: Update, query, user_data: dict, mode: bool) -> None:
    """Set the prompt mode (read-only or yolo)."""
    user_data[KEY_PROMPT_MODE] = mode
    
    mode_name = "Read-Write (Yolo)" if mode else "Read Only"
    agent_id = user_data.get(KEY_SELECTED_AGENT)
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    agent_name = "default"
    if agent_id and project_dir:
        agents = agents_module.load_agents(project_dir)
        agent = next((a for a in agents if a["id"] == agent_id), None)
        if agent:
            agent_name = agent['name']
    
    text = f"""✅ *Mode Set*

*Agent:* {agent_name}
*Mode:* {mode_name}

Now send your prompt!"""
    
    await query.edit_message_text(text, parse_mode="Markdown")


async def start_quick_prompt(update: Update, query, user_data: dict) -> None:
    """Start quick prompt mode with the highest model (Opus 4.6)."""
    project_dir = user_data.get(KEY_SELECTED_PROJECT) or config.get_default_project_dir()
    
    if not project_dir:
        text = """📁 *No Project Selected*

Please select a default project first."""
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.back_keyboard("menu:main"))
        return
    
    # Use the highest model - Opus 4.6
    highest_model = "opus-4.6"
    
    # Create a temporary agent for quick prompt
    agent = agents_module.create_agent(project_dir, "Quick Prompt", highest_model, "cursor", None)
    
    # Select this agent
    user_data[KEY_SELECTED_AGENT] = agent["id"]
    user_data[KEY_PROMPT_MODE] = False  # Default to read-only
    
    text = f"""⚡ *Quick Prompt Mode*

*Model:* Opus 4.6 (Highest)

Now send your prompt! You can use:
• Read Only mode (default) - for queries
• Read-Write (Yolo) mode - for modifications"""
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard.prompt_mode_keyboard())


def get_callback_handler():
    """Return the callback query handler."""
    return CallbackQueryHandler(handle_callback)
