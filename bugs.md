# Bugs Found

## NEW: User-Reported Bugs (from Telegram Testing) - to be fixed

### Bug 19: Change button "Default Project" to "Projects"
- [x] **File:** `bot/keyboard.py` (line 11)
- **Severity:** Low
- **Status:** ✅ FIXED

Change button label from "Default Project" to "Projects" in the main menu.

**Fix:** Changed button label in `main_menu_keyboard()` function.

---

### Bug 20: Discover Projects shows "Directory not found" error
- [x] **File:** `bot/callbacks.py`
- **Severity:** High
- **Status:** ✅ FIXED

After clicking Discover Projects and selecting a project, there is an error message "Directory not found".

**Fix:** Added `from pathlib import Path` import and used `Path(project_path).is_dir()` for proper path validation.

---

### Bug 21: Change button "LLM Models" to "Custom LLM Models"
- [x] **File:** `bot/keyboard.py` (line 10)
- **Severity:** Low
- **Status:** ✅ FIXED

Change button label from "LLM Models" to "Custom LLM Models" in the main menu.

**Fix:** Changed button label in `main_menu_keyboard()` function.

---

### Bug 22: Remove LLM button doesn't work
- [x] **File:** `bot/callbacks.py`
- **Severity:** High
- **Status:** ✅ FIXED

Button "Remove LLM" doesn't work. Once clicked, it should show a list of Custom LLMs, click on particular LLM and it will ask "Are you sure to remove it?", click "Yes" will remove it, click "No" goes back to the selection.

**Fix:** Added `show_remove_llm_confirm()` function that shows confirmation dialog before removing.

---

### Bug 23: "Create Agent" - remove "━━━ Model Families ━━━" header
- [x] **File:** `bot/keyboard.py`
- **Severity:** Medium
- **Status:** ✅ FIXED

When "Create Agent", remove the headline "━━━ Model Families ━━━" because it has error when clicking on it. The error message is "Unknown action: menu:header".

**Fix:** Removed the header line from `model_family_keyboard()` function.

---

### Bug 24: Go back from Model Version should go to Model Family
- [x] **File:** `bot/callbacks.py`
- **Severity:** Medium
- **Status:** ✅ FIXED

When going back from the screen "Select Model Version", it should go back to the screen "Selecting a Model Family" instead of going back to the screen naming the agent.

**Fix:** Changed the "Back" button in `model_versions_keyboard()` to go to `menu:create_agent`, which now shows the model family selection via `show_model_family_selection()`. Also added `show_model_family_selection()` function to handle this flow properly.

---

### Bug 25: Delete Agent doesn't work (still)
- [x] **File:** `bot/callbacks.py` or `bot/agents.py`
- **Severity:** High
- **Status:** ✅ FIXED

Button "Delete Agent" still doesn't work. When clicked, it should ask "Are you sure to remove it?", click "Yes" will remove it, click "No" goes back to the selection.

**Fix:** Added `show_delete_agent_confirm()` function that shows confirmation dialog before deleting.

---

### Bug 26: Vibe Code menu should have "Prompt" button for highest model
- [x] **File:** `bot/keyboard.py`
- **Severity:** Medium
- **Status:** ✅ FIXED

In the screen Vibe Code "Choose An Action", it should have a button "Prompt" to pick the highest model running the LLM.

**Fix:** Added "⚡ Quick Prompt (Highest Model)" button in `vibe_code_menu_keyboard()` and implemented `start_quick_prompt()` handler.

---

### Bug 27: Projects menu title shows "Default Project"
- [x] **File:** `bot/callbacks.py`
- **Severity:** Low
- **Status:** ✅ FIXED

After clicking button Projects, the title is still "📁 Default Project". Change it to "📁 Projects".

**Fix:** Changed title text in `show_default_project_menu()` function.

---

## Previously Found Bugs (1-18) - Fixed or Pending

## Bug 1: Missing llms_module import in handle_message
- [x] **File:** `bot/handlers.py` (line 170)
- **Severity:** High
- **Status:** ✅ FIXED

The `handle_message` function uses `llms_module` at line 170 to load custom LLMs during agent creation, but `llms_module` is never imported. This causes a `NameError` when trying to create an agent.

**Fix:** Added imports inside the function.

---

## Bug 2: Missing projects_module import in handle_message
- [x] **File:** `bot/handlers.py` (line 253)
- **Severity:** High
- **Status:** ✅ FIXED

The `handle_message` function uses `projects_module` to add a project, but `projects_module` is never imported. This causes a `NameError` when trying to add a project path.

**Fix:** Added imports inside the function.

---

## Bug 3: Dead code in discover_projects_keyboard
- [x] **File:** `bot/keyboard.py` (lines 176-181)
- **Severity:** Low
- **Status:** ✅ FIXED

The function `discover_projects_keyboard` has unreachable code after the first return statement.

**Fix:** Dead code removed.

---

## Bug 4: LLM buffer not cleared after LLM creation
- [x] **File:** `bot/handlers.py`
- **Severity:** Medium
- **Status:** ✅ FIXED

When creating an LLM, the buffers might not be cleared properly.

**Fix:** The buffers KEY_LLM_NAME_BUFFER, KEY_LLM_ENDPOINT_BUFFER, and KEY_AWAITING_PROMPT are properly cleared after LLM creation (lines 227-229 in handlers.py).

---

## Bug 5: delete_agent returns False when deleting the last agent
- [x] **File:** `bot/agents.py` (lines 75-87)
- **Severity:** Medium
- **Status:** ✅ FIXED

The `delete_agent` function returns `False` if the agent list becomes empty after deletion.

**Fix:** Now checks original_count before deletion.

---

## Bug 6: delete_llm returns False when deleting the last LLM
- [x] **File:** `bot/llms.py` (lines 58-70)
- **Severity:** Medium
- **Status:** ✅ FIXED

Same issue as Bug 5. The `delete_llm` function returns `False` if the LLM list becomes empty after deletion.

**Fix:** Now checks original_count before deletion.

---

## Bug 7: Unused _extract_prompt function
- [x] **File:** `bot/handlers.py` (lines 541-565)
- **Severity:** Low
- **Status:** ✅ FIXED

The function `_extract_prompt` is defined but never used anywhere in the codebase.

**Fix:** The function was renamed to `_extract_prompt_simple` and is actively used in `_extract_project_and_prompt` function.

---

## Bug 8: LLM endpoint URL not validated
- [x] **File:** `bot/handlers.py`
- **Severity:** Medium
- **Status:** ✅ FIXED

When the user enters an LLM endpoint URL, there's no validation to check if it's a valid URL format.

**Fix:** Added proper URL validation using `urllib.parse.urlparse` to validate scheme and netloc (lines 189-203 in handlers.py).

---

## Bug 9: Wrong keyboard shown after agent creation
- [x] **File:** `bot/callbacks.py`
- **Severity:** Low
- **Status:** ✅ FIXED

After creating an agent, the code shows the Vibe Code menu instead of the selected agent keyboard.

**Fix:** After agent creation, the code now shows `keyboard.selected_agent_keyboard(agent["id"])` which is the correct keyboard (line 232 in callbacks.py).

---

## Bug 10: Anthropic API request missing max_tokens parameter
- [x] **File:** `bot/cursor_cli.py` (lines 167-175)
- **Severity:** Medium
- **Status:** ✅ FIXED

When making requests to the Anthropic API, the `max_tokens` parameter was not included in the payload.

**Fix:** Added max_tokens: 4096 to the payload.

---

## Bug 11-18: Previously reported user bugs
- [x] **Status:** Superseded by bugs 19-27

Bugs 11-18 from previous report have been consolidated into bugs 19-27 above.

---

## Summary

| Bug # | Severity | Status |
|-------|----------|--------|
| 1 | High | ✅ FIXED |
| 2 | High | ✅ FIXED |
| 3 | Low | ✅ FIXED |
| 4 | Medium | ✅ FIXED |
| 5 | Medium | ✅ FIXED |
| 6 | Medium | ✅ FIXED |
| 7 | Low | ✅ FIXED |
| 8 | Medium | ✅ FIXED |
| 9 | Low | ✅ FIXED |
| 10 | Medium | ✅ FIXED |
| 11-18 | - | Superseded |
| 19 | Low | ✅ FIXED |
| 20 | High | ✅ FIXED |
| 21 | Low | ✅ FIXED |
| 22 | High | ✅ FIXED |
| 23 | Medium | ✅ FIXED |
| 24 | Medium | ✅ FIXED |
| 25 | High | ✅ FIXED |
| 26 | Medium | ✅ FIXED |
| 27 | Low | ✅ FIXED |
