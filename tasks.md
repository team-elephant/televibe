# Implementation Tasks

## Phase 1: Project Setup ✅ COMPLETED

- [x] 1.1 Create `bot/` directory with `__init__.py`
- [x] 1.2 Create `requirements.txt` with dependencies
- [x] 1.3 Create `.env.example` template with all CLI API keys
- [x] 1.4 Copy `.env.example` to `.env` and fill in values

**Status:** All completed. Requirements include python-telegram-bot, python-dotenv, and aiohttp.

---

## Phase 2: Core Bot Infrastructure ✅ COMPLETED

- [x] 2.1 Implement `bot/config.py`
  - Load environment variables for all CLIs ✅
  - Validate Telegram bot token ✅
  - Validate owner ID ✅
  - Load API keys for Cursor, Claude, Codex, Grok ✅

- [x] 2.2 Implement `bot/main.py`
  - Initialize bot for group chat mode ✅
  - Set up message handlers for tagged messages ✅
  - Implement owner verification ✅
  - Long polling loop ✅
  - Graceful shutdown ✅

**Status:** All completed. Config supports both `TELEGRAM_OWNER_ID` and legacy `TELEGRAM_ALLOWED_USER_ID`. Main.py has separate handlers for group messages (tagged) and private messages.

**Findings:**
- ✅ Config loads all CLI API keys (Cursor, Anthropic, OpenAI, Grok)
- ✅ Owner verification implemented with `is_owner()` method
- ✅ Group message handler with `filters.IS_GROUP_MESSAGE`
- ✅ Private message handler with `filters.IS_PRIVATE_MESSAGE`

---

## Phase 3: Group-Project Management ✅ COMPLETED

- [x] 3.1 Create `bot/groups.py` for group management
  - Data model: group_id, project_path, project_name, linked_at ✅
  - Load/save groups.json ✅
  - Link group to project ✅
  - Unlink group ✅
  - Get project path for group_id ✅

- [x] 3.2 Implement `/link` command
  - Accept project path as parameter ✅
  - Validate directory exists ✅
  - Store group_id → project_path mapping ✅
  - Send confirmation message ✅

- [x] 3.3 Implement `/unlink` command
  - Remove group_id mapping ✅
  - Send confirmation message ✅

- [x] 3.4 Implement `/status` command
  - Show linked project path ✅
  - Show active agents ✅ (shows CLI status)
  - Show recent executions ⚠️ (not yet implemented)

**Status:** Mostly completed. Commands are implemented and working.

**Findings:**
- ✅ `groups.py` has complete CRUD operations for group-project mappings
- ✅ `/link` command validates paths and expands `~` to full path
- ✅ `/unlink` command properly removes mappings
- ✅ `/status` command shows group status (called `group_status_command` in code, but registered as `/status`)
- ⚠️ **Issue:** Status command doesn't show recent executions yet (Phase 6 feature)
- ✅ Owner verification on all group commands

---

## Phase 4: Multi-CLI Agent System

- [ ] 4.1 Create `bot/agents.py` for agent management
  - Define agent types: cursor, claude, codex, grok
  - Load/save agents.json
  - Enable/disable agents
  - Get agent by name

- [x] 4.2 Create `bot/cli_cursor.py` (Already exists as `cursor_cli.py`)
  - Async wrapper around `agent -p` subprocess ✅
  - Support for `--force` flag ✅
  - Streaming output handling ✅
  - Timeout and error handling ✅

- [ ] 4.3 Create `bot/cli_claude.py`
  - Async API wrapper for Anthropic API
  - Streaming response handling
  - Error handling

- [ ] 4.4 Create `bot/cli_codex.py`
  - Async API wrapper for OpenAI Codex
  - Streaming response handling
  - Error handling

- [ ] 4.5 Create `bot/cli_grok.py`
  - Async API wrapper for xAI Grok
  - Streaming response handling
  - Error handling

**Status:** Partially completed. Cursor CLI exists and works. Other CLIs need implementation.

**Findings:**
- ✅ `cursor_cli.py` already exists with full functionality
- ❌ Claude CLI not yet created
- ❌ Codex CLI not yet created
- ❌ Grok CLI not yet created
- ⚠️ **Note:** There's a `_build_agent_cli()` function in handlers.py that currently only supports Cursor

---

## Phase 5: Tag-Based Message Handling ⚠️ PARTIALLY COMPLETED

- [x] 5.1 Implement tag detection in `bot/handlers.py`
  - Detect @cursor, @claude, @codex, @grok mentions ✅
  - Extract agent name from tag ✅
  - Verify sender is owner ✅
  - Ignore messages from non-owners ✅

- [x] 5.2 Implement message routing
  - Route to appropriate CLI handler based on tag ✅
  - Pass project path from group mapping ✅
  - Extract prompt (remove tag) ✅

- [x] 5.3 Implement prompt execution
  - Execute prompt via selected CLI ✅ (only Cursor works currently)
  - Stream output back to group ✅
  - Handle errors gracefully ✅

- [x] 5.4 Implement status updates
  - Post completion status to group ✅
  - Include files modified (if applicable) ⚠️ (placeholder)
  - Include execution time ⚠️ (not shown)

**Status:** Infrastructure is completed but only works with Cursor CLI currently.

**Findings:**
- ✅ `detect_agent_tag()` function extracts tags like `@cursor`, `@claude`, etc.
- ✅ `handle_group_message()` processes tagged messages
- ✅ `_execute_agent_prompt()` executes the prompt
- ✅ `_build_agent_cli()` exists but only returns CursorCLI
- ⚠️ **Issue:** Only Cursor agent is functional; Claude, Codex, Grok return NotImplementedError
- ⚠️ Status message says "Modified X files" but doesn't actually track files

---

## Phase 6: Execution History Tracking

- [ ] 6.1 Create `bot/history.py`
  - Data model: id, agent, prompt, timestamp, status, files_modified
  - Load/save <group_id>_history.json per group
  - Add execution record
  - Get recent executions

- [ ] 6.2 Track all agent executions
  - Record when prompt starts
  - Update when completed/failed
  - Store modified files list

- [ ] 6.3 Implement `/history` command
  - Show recent executions in this group
  - Show agent used, prompt preview, status

**Status:** Not started.

---

## Phase 7: Testing

- [ ] 7.1 Create test Telegram group
- [ ] 7.2 Add bot to group
- [ ] 7.3 Test `/link` command with real project
- [ ] 7.4 Test @cursor tag with simple prompt
- [ ] 7.5 Test @claude tag with simple prompt
- [ ] 7.6 Test @codex tag with simple prompt
- [ ] 7.7 Test @grok tag with simple prompt
- [ ] 7.8 Test owner verification (non-owner can't invoke)
- [ ] 7.9 Test `/status` command
- [ ] 7.10 Test `/history` command

**Status:** Not started.

---

## Phase 8: Error Handling & Robustness

- [ ] 8.1 Handle unlinked groups gracefully
- [ ] 8.2 Handle unknown agent tags
- [ ] 8.3 Handle CLI timeouts
- [ ] 8.4 Handle API rate limits
- [ ] 8.5 Handle network errors
- [ ] 8.6 Implement retry logic for transient failures

**Status:** Not started.

---

## Phase 9: Documentation

- [ ] 9.1 Update README with setup instructions
- [ ] 9.2 Document all commands
- [ ] 9.3 Document agent tagging syntax
- [ ] 9.4 Document .env configuration
- [ ] 9.5 Add troubleshooting guide

**Status:** Not started.

---

## Phase 10: Deployment

- [ ] 10.1 Set up on MacBook (Device A)
- [ ] 10.2 Configure .env with all API keys
- [ ] 10.3 Create systemd/launchd service for auto-start
- [ ] 10.4 Test remote access from phone (Device B)
- [ ] 10.5 Set up logging and monitoring

**Status:** Not started.

---

## Summary of Findings

### ✅ What's Working:
1. **Phase 1-3 Complete**: Project setup, config, and group management
2. **Tag Detection**: Bot can detect agent tags in group messages
3. **Cursor Integration**: @cursor tag works with full CLI integration
4. **Owner Verification**: Only owner can use commands and tag agents
5. **Group Linking**: `/link` and `/unlink` commands work properly

### ⚠️ Issues Found:
1. **Missing CLI Implementations**: Only Cursor CLI exists; Claude, Codex, Grok need to be created
2. **`_build_agent_cli()` Function**: Currently raises NotImplementedError for non-Cursor agents
3. **Status Command**: Doesn't show recent executions (needs Phase 6)
4. **File Tracking**: Status message claims to show modified files but doesn't actually track them
5. **Execution History**: Not yet implemented (Phase 6)

### 📝 Recommendations:
1. **Priority**: Implement Claude, Codex, and Grok CLI wrappers (Phase 4.3-4.5)
2. **Next**: Complete execution history tracking (Phase 6)
3. **Then**: Begin testing phase (Phase 7)
