"""Inline keyboard layouts for the Remote Cursor bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with Vibe Code, Custom LLM Models, Projects, Status, Help."""
    keyboard = [
        [InlineKeyboardButton("🎯 Vibe Code", callback_data="menu:vibe_code")],
        [InlineKeyboardButton("🤖 Custom LLM Models", callback_data="menu:custom_llm")],
        [InlineKeyboardButton("📁 Projects", callback_data="menu:default_project")],
        [InlineKeyboardButton("📊 Status", callback_data="menu:status")],
        [InlineKeyboardButton("❓ Help", callback_data="menu:help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def vibe_code_menu_keyboard() -> InlineKeyboardMarkup:
    """Vibe Code submenu with Pick Agent, Create Agent, Delete Agent, and Quick Prompt."""
    keyboard = [
        [InlineKeyboardButton("👤 Pick Agent", callback_data="menu:pick_agent")],
        [InlineKeyboardButton("➕ Create Agent", callback_data="menu:create_agent")],
        [InlineKeyboardButton("🗑️ Delete Agent", callback_data="menu:delete_agent")],
        [InlineKeyboardButton("⚡ Quick Prompt (Highest Model)", callback_data="menu:quick_prompt")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def model_family_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with main model families for first step of model selection."""
    # Note: Removed the header line to avoid "menu:header" error (Bug 23)
    keyboard = [
        [InlineKeyboardButton("🔹 Claude Opus", callback_data="model_family:opus")],
        [InlineKeyboardButton("🔹 Claude Sonnet", callback_data="model_family:sonnet")],
        [InlineKeyboardButton("🔹 Claude Haiku", callback_data="model_family:haiku")],
        [InlineKeyboardButton("🔹 GPT-4o", callback_data="model_family:gpt-4o")],
        [InlineKeyboardButton("🔹 GPT-4", callback_data="model_family:gpt-4")],
        [InlineKeyboardButton("🔹 Gemini", callback_data="model_family:gemini")],
        [InlineKeyboardButton("🔹 Grok", callback_data="model_family:grok")],
        [InlineKeyboardButton("🔹 Kimi", callback_data="model_family:kimi")],
        [InlineKeyboardButton("🔹 Composer", callback_data="model_family:composer")],
        [InlineKeyboardButton("🔹 Codex", callback_data="model_family:codex")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:vibe_code")],
    ]
    return InlineKeyboardMarkup(keyboard)


def model_versions_keyboard(family: str, custom_llms: list = None) -> InlineKeyboardMarkup:
    """Keyboard with model versions for a specific family."""
    custom_llms = custom_llms or []
    
    models = {
        "opus": [
            ("cursor:opus-4.6", "Opus 4.6"),
            ("cursor:opus-4.6-thinking", "Opus 4.6 (Thinking)"),
            ("cursor:opus-4.5", "Opus 4.5"),
            ("cursor:opus-4.5-thinking", "Opus 4.5 (Thinking)"),
            ("anthropic:claude-3-opus-20240229", "Claude 3 Opus"),
        ],
        "sonnet": [
            ("cursor:sonnet-4.6", "Sonnet 4.6"),
            ("cursor:sonnet-4.6-thinking", "Sonnet 4.6 (Thinking)"),
            ("cursor:sonnet-4.5", "Sonnet 4.5"),
            ("cursor:sonnet-4.5-thinking", "Sonnet 4.5 (Thinking)"),
            ("anthropic:claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
        ],
        "haiku": [
            ("anthropic:claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
            ("anthropic:claude-3-haiku-20240307", "Claude 3 Haiku"),
        ],
        "gpt-4o": [
            ("cursor:gpt-5.3-codex", "GPT-5.3 Codex"),
            ("cursor:gpt-5.3-codex-high", "GPT-5.3 Codex High"),
            ("cursor:gpt-5.3-codex-xhigh", "GPT-5.3 Codex X-High"),
            ("openai:gpt-4o", "GPT-4o"),
            ("openai:gpt-4o-mini", "GPT-4o Mini"),
        ],
        "gpt-4": [
            ("openai:gpt-4-turbo", "GPT-4 Turbo"),
            ("openai:gpt-4", "GPT-4"),
            ("openai:gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ],
        "gemini": [
            ("cursor:gemini-3.1-pro", "Gemini 3.1 Pro"),
        ],
        "grok": [
            ("cursor:grok", "Grok"),
        ],
        "kimi": [
            ("cursor:kimi-k2.5", "Kimi K2.5"),
        ],
        "composer": [
            ("cursor:composer-1.5", "Composer 1.5"),
        ],
        "codex": [
            ("cursor:gpt-5.2-codex", "GPT-5.2 Codex"),
            ("cursor:gpt-5.2-codex-high", "GPT-5.2 Codex High"),
            ("cursor:gpt-5.2-codex-xhigh", "GPT-5.2 Codex X-High"),
            ("cursor:gpt-5.1-codex-max", "GPT-5.1 Codex Max"),
            ("cursor:gpt-5.1-codex-mini", "GPT-5.1 Codex Mini"),
        ],
    }
    
    family_models = models.get(family, [])
    
    # Build keyboard
    keyboard = []
    keyboard.append([InlineKeyboardButton(f"━━━ {family.title()} Versions ━━━", callback_data="menu:header")])
    
    for model_id, model_name in family_models:
        keyboard.append([InlineKeyboardButton(f"  {model_name}", callback_data=f"model:{model_id}")])
    
    # Add custom LLMs at the end if any
    if custom_llms:
        keyboard.append([InlineKeyboardButton("━━━ Custom LLM ━━━", callback_data="menu:header")])
        for llm in custom_llms:
            keyboard.append([InlineKeyboardButton(f"  {llm['name']}", callback_data=f"model:custom:{llm['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:create_agent")])
    return InlineKeyboardMarkup(keyboard)


def model_versions_keyboard_with_back(family: str, custom_llms: list = None) -> InlineKeyboardMarkup:
    """Keyboard with model versions for a specific family - with back to model family."""
    custom_llms = custom_llms or []
    
    models = {
        "opus": [
            ("cursor:opus-4.6", "Opus 4.6"),
            ("cursor:opus-4.6-thinking", "Opus 4.6 (Thinking)"),
            ("cursor:opus-4.5", "Opus 4.5"),
            ("cursor:opus-4.5-thinking", "Opus 4.5 (Thinking)"),
            ("anthropic:claude-3-opus-20240229", "Claude 3 Opus"),
        ],
        "sonnet": [
            ("cursor:sonnet-4.6", "Sonnet 4.6"),
            ("cursor:sonnet-4.6-thinking", "Sonnet 4.6 (Thinking)"),
            ("cursor:sonnet-4.5", "Sonnet 4.5"),
            ("cursor:sonnet-4.5-thinking", "Sonnet 4.5 (Thinking)"),
            ("anthropic:claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
        ],
        "haiku": [
            ("anthropic:claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
            ("anthropic:claude-3-haiku-20240307", "Claude 3 Haiku"),
        ],
        "gpt-4o": [
            ("cursor:gpt-5.3-codex", "GPT-5.3 Codex"),
            ("cursor:gpt-5.3-codex-high", "GPT-5.3 Codex High"),
            ("cursor:gpt-5.3-codex-xhigh", "GPT-5.3 Codex X-High"),
            ("openai:gpt-4o", "GPT-4o"),
            ("openai:gpt-4o-mini", "GPT-4o Mini"),
        ],
        "gpt-4": [
            ("openai:gpt-4-turbo", "GPT-4 Turbo"),
            ("openai:gpt-4", "GPT-4"),
            ("openai:gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ],
        "gemini": [
            ("cursor:gemini-3.1-pro", "Gemini 3.1 Pro"),
        ],
        "grok": [
            ("cursor:grok", "Grok"),
        ],
        "kimi": [
            ("cursor:kimi-k2.5", "Kimi K2.5"),
        ],
        "composer": [
            ("cursor:composer-1.5", "Composer 1.5"),
        ],
        "codex": [
            ("cursor:gpt-5.2-codex", "GPT-5.2 Codex"),
            ("cursor:gpt-5.2-codex-high", "GPT-5.2 Codex High"),
            ("cursor:gpt-5.2-codex-xhigh", "GPT-5.2 Codex X-High"),
            ("cursor:gpt-5.1-codex-max", "GPT-5.1 Codex Max"),
            ("cursor:gpt-5.1-codex-mini", "GPT-5.1 Codex Mini"),
        ],
    }
    
    family_models = models.get(family, [])
    
    # Build keyboard
    keyboard = []
    keyboard.append([InlineKeyboardButton(f"━━━ {family.title()} Versions ━━━", callback_data="menu:header")])
    
    for model_id, model_name in family_models:
        keyboard.append([InlineKeyboardButton(f"  {model_name}", callback_data=f"model:{model_id}")])
    
    # Add custom LLMs at the end if any
    if custom_llms:
        keyboard.append([InlineKeyboardButton("━━━ Custom LLM ━━━", callback_data="menu:header")])
        for llm in custom_llms:
            keyboard.append([InlineKeyboardButton(f"  {llm['name']}", callback_data=f"model:custom:{llm['id']}")])
    
    # Back goes to model family selection
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:create_agent")])
    return InlineKeyboardMarkup(keyboard)


def back_keyboard(callback_data: str = "menu:main") -> InlineKeyboardMarkup:
    """Single back button keyboard."""
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data=callback_data)],
    ]
    return InlineKeyboardMarkup(keyboard)


def agents_keyboard(agents: list, selected_agent_id: str = None) -> InlineKeyboardMarkup:
    """Keyboard with agent options and a Back button.
    
    Args:
        agents: List of agent dicts with 'id' and 'name' keys.
        selected_agent_id: ID of currently selected agent (for marking).
    """
    keyboard = []
    for agent in agents:
        # Agent name with selection indicator
        label = f"✓ {agent['name']}" if agent['id'] == selected_agent_id else agent['name']
        keyboard.append([InlineKeyboardButton(label, callback_data=f"agent:select:{agent['id']}")])
    
    # Add delete option if there are agents
    if agents:
        keyboard.append([InlineKeyboardButton("🗑️ Delete Agent", callback_data="menu:delete_agent")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:vibe_code")])
    return InlineKeyboardMarkup(keyboard)


def models_keyboard(custom_llms: list = None) -> InlineKeyboardMarkup:
    """Keyboard with available models: Cursor, OpenAI, Anthropic, and Custom."""
    custom_llms = custom_llms or []
    
    # Section header
    keyboard = [
        [InlineKeyboardButton("━━━ Cursor Models ━━━", callback_data="menu:header")],
    ]
    
    # Cursor models
    cursor_models = [
        ("cursor:auto", "Auto (Recommended)"),
        ("cursor:sonnet-4.6", "Sonnet 4.6"),
        ("cursor:sonnet-4.6-thinking", "Sonnet 4.6 (Thinking)"),
        ("cursor:sonnet-4.5", "Sonnet 4.5"),
        ("cursor:sonnet-4.5-thinking", "Sonnet 4.5 (Thinking)"),
        ("cursor:opus-4.6", "Opus 4.6"),
        ("cursor:opus-4.6-thinking", "Opus 4.6 (Thinking)"),
        ("cursor:opus-4.5", "Opus 4.5"),
        ("cursor:opus-4.5-thinking", "Opus 4.5 (Thinking)"),
        ("cursor:gpt-5.3-codex", "GPT-5.3 Codex"),
        ("cursor:gpt-5.3-codex-high", "GPT-5.3 Codex High"),
        ("cursor:gpt-5.3-codex-xhigh", "GPT-5.3 Codex X-High"),
        ("cursor:gpt-5.2-codex", "GPT-5.2 Codex"),
        ("cursor:gpt-5.2-codex-high", "GPT-5.2 Codex High"),
        ("cursor:gpt-5.2-codex-xhigh", "GPT-5.2 Codex X-High"),
        ("cursor:gpt-5.1-codex-max", "GPT-5.1 Codex Max"),
        ("cursor:gpt-5.1-codex-mini", "GPT-5.1 Codex Mini"),
        ("cursor:gemini-3.1-pro", "Gemini 3.1 Pro"),
        ("cursor:grok", "Grok"),
        ("cursor:composer-1.5", "Composer 1.5"),
        ("cursor:kimi-k2.5", "Kimi K2.5"),
    ]
    for model_id, model_name in cursor_models:
        keyboard.append([InlineKeyboardButton(f"  {model_name}", callback_data=f"model:{model_id}")])
    
    # OpenAI models
    keyboard.append([InlineKeyboardButton("━━━ OpenAI ━━━", callback_data="menu:header")])
    openai_models = [
        ("openai:gpt-4o", "GPT-4o"),
        ("openai:gpt-4o-mini", "GPT-4o Mini"),
        ("openai:gpt-4-turbo", "GPT-4 Turbo"),
        ("openai:gpt-4", "GPT-4"),
        ("openai:gpt-3.5-turbo", "GPT-3.5 Turbo"),
    ]
    for model_id, model_name in openai_models:
        keyboard.append([InlineKeyboardButton(f"  {model_name}", callback_data=f"model:{model_id}")])
    
    # Anthropic models
    keyboard.append([InlineKeyboardButton("━━━ Anthropic ━━━", callback_data="menu:header")])
    anthropic_models = [
        ("anthropic:claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
        ("anthropic:claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
        ("anthropic:claude-3-opus-20240229", "Claude 3 Opus"),
        ("anthropic:claude-3-haiku-20240307", "Claude 3 Haiku"),
    ]
    for model_id, model_name in anthropic_models:
        keyboard.append([InlineKeyboardButton(f"  {model_name}", callback_data=f"model:{model_id}")])
    
    # Custom LLMs (from bot/llms.json)
    if custom_llms:
        keyboard.append([InlineKeyboardButton("━━━ Custom LLM ━━━", callback_data="menu:header")])
        for llm in custom_llms:
            keyboard.append([InlineKeyboardButton(f"  {llm['name']}", callback_data=f"model:custom:{llm['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:vibe_code")])
    return InlineKeyboardMarkup(keyboard)


def projects_keyboard(projects: list, selected_project: str = None) -> InlineKeyboardMarkup:
    """Keyboard with project directory options.
    
    Args:
        projects: List of project directory paths.
        selected_project: Currently selected project (for marking).
    """
    keyboard = []
    
    # List of projects
    for project in projects:
        # Truncate long paths for display
        display_name = project.split("/")[-1]
        if project == selected_project:
            display_name = f"✓ {display_name}"
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"project:select:{project}")])
    
    # Add/Remove/Discover options
    keyboard.append([InlineKeyboardButton("➕ Add Project", callback_data="project:add")])
    keyboard.append([InlineKeyboardButton("🔍 Discover Projects", callback_data="project:discover")])
    keyboard.append([InlineKeyboardButton("🗑️ Remove Project", callback_data="project:remove")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:main")])
    return InlineKeyboardMarkup(keyboard)


def discover_projects_keyboard(discovered: list, existing: list) -> InlineKeyboardMarkup:
    """Keyboard for discovered projects to add.
    
    Args:
        discovered: List of discovered project paths.
        existing: List of already managed project paths.
    """
    keyboard = []
    
    # Filter out already existing projects
    new_projects = [p for p in discovered if p not in existing]
    
    if not new_projects:
        keyboard.append([InlineKeyboardButton("No new projects found", callback_data="menu:header")])
    else:
        for project in new_projects:
            display_name = project.split("/")[-1]
            keyboard.append([InlineKeyboardButton(f"➕ {display_name}", callback_data=f"project:add_discovered:{project}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:default_project")])
    return InlineKeyboardMarkup(keyboard)


def projects_remove_keyboard(projects: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a project to remove."""
    keyboard = []
    
    for project in projects:
        display_name = project.split("/")[-1]
        keyboard.append([InlineKeyboardButton(f"🗑️ {display_name}", callback_data=f"project:delete:{project}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:default_project")])
    return InlineKeyboardMarkup(keyboard)


def status_keyboard() -> InlineKeyboardMarkup:
    """Status view with Back button."""
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def custom_llm_menu_keyboard() -> InlineKeyboardMarkup:
    """Custom LLM Model submenu."""
    keyboard = [
        [InlineKeyboardButton("📋 List LLMs", callback_data="llm:list")],
        [InlineKeyboardButton("➕ Add LLM", callback_data="llm:add")],
        [InlineKeyboardButton("🗑️ Remove LLM", callback_data="llm:remove")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def llms_keyboard(llms: list, selected_llm_id: str = None) -> InlineKeyboardMarkup:
    """Keyboard with LLM options and a Back button."""
    keyboard = []
    for llm in llms:
        label = f"✓ {llm['name']}" if llm['id'] == selected_llm_id else llm['name']
        keyboard.append([InlineKeyboardButton(label, callback_data=f"llm:select:{llm['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:custom_llm")])
    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard(confirm_callback: str, cancel_callback: str = "menu:main") -> InlineKeyboardMarkup:
    """Confirm/Cancel keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=confirm_callback),
            InlineKeyboardButton("❌ Cancel", callback_data=cancel_callback),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def selected_agent_keyboard(agent_id: str) -> InlineKeyboardMarkup:
    """Keyboard for selected agent - prompt or view status."""
    keyboard = [
        [InlineKeyboardButton("💬 Prompt", callback_data=f"agent:prompt:{agent_id}")],
        [InlineKeyboardButton("📊 Agent Status", callback_data=f"agent:status:{agent_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:pick_agent")],
    ]
    return InlineKeyboardMarkup(keyboard)


def prompt_mode_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for switching between read-only and read-write modes."""
    keyboard = [
        [InlineKeyboardButton("🔒 Read Only", callback_data="prompt:mode:false")],
        [InlineKeyboardButton("✏️ Read-Write (Yolo)", callback_data="prompt:mode:true")],
    ]
    return InlineKeyboardMarkup(keyboard)
