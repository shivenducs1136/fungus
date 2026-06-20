# VS Code MCP Setup Guide

## Prerequisites

1. **Python environment configured**
   ```bash
   cd D:\Fungus\fungus
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

2. **FastAPI Knowledge Server running**
   ```bash
   uvicorn app.main:app --reload
   ```
   Expected: Server starts at `http://127.0.0.1:8000`

## Option A: Workspace MCP File (Recommended)

### Step 1: Create or Update `.vscode/mcp.json`

Create `.vscode/mcp.json` in the workspace with this content:

```json
{
   "servers": {
      "fungus-knowledge": {
         "type": "stdio",
         "command": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
         "args": ["-m", "app.mcp.server"],
         "cwd": "${workspaceFolder}",
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15"
         }
      }
   },
   "inputs": []
}
```

### Step 2: Reload VS Code

1. Press `Ctrl+Shift+P` → `Developer: Reload Window`.
2. Open Copilot Chat.
3. Confirm tools are visible.

## Option B: Command Palette (UI-driven)

### Step 1: Open Command Palette

1. Press `Ctrl+Shift+P`.
2. Type `MCP: Add Server`.
3. Select the option.

### Step 2: Configure Server

Fill in the prompts:

| Field | Value |
|-------|-------|
| **Server Name** | `fungus-knowledge` |
| **Transport** | `stdio` |
| **Command** | `python` |
| **Arguments** | `-m app.mcp.server` |
| **Working Directory** | `D:\Fungus\fungus` |
| **Environment Variables** | `KNOWLEDGE_SERVER_BASE_URL=http://127.0.0.1:8000` |

### Step 3: Verify Registration

1. Open Copilot Chat.
2. You should see these tools available:
   - `save_knowledge`
   - `retrieve_knowledge`
   - `retrieve_knowledge_from_code`

## Testing in Copilot Chat

Before running tests, ensure workspace instructions are loaded from `.github/copilot-instructions.md`.
If already open, run `Developer: Reload Window` once after pulling latest changes.

### Test 1: Direct Save and Retrieve

```
@copilot Save this discussion for JIRA TEST-001.
```

Expected response:
```
SAVE ok [TEST-001]
entry_id: <UUID>
timestamp: <ISO-8601>
```

Expected behavior:
- Copilot auto-generates `chat_context` from the active conversation.
- Copilot calls `save_knowledge` without asking you to paste context again.

### Test 2: Retrieve Saved Knowledge

```
@copilot retrieve_knowledge with jira_ids=["TEST-001"] depth=3
```

Expected response:
```
RETRIEVE ok
TEST-001: 1 entry
- This is a test message from VS Code Copilot chat.
```

### Test 3: Code-Based Retrieval

Select a code block (for example lines 1-50 of `app/main.py`):

```
@copilot explain this function using retrieve_knowledge_from_code with file_path="app/main.py" start_line=1 end_line=50 depth=1
```

Expected:
- MCP extracts JIRA IDs from git history for lines 1-50.
- Returns architectural knowledge linked to those commits.

## Troubleshooting

### "MCP: Add Server" not found

- Update VS Code to the latest version.
- Ensure GitHub Copilot extension is up-to-date.
- Check that you're in a workspace folder.

### "Server failed to start"

1. Verify Python is in PATH:
   ```bash
   python --version
   ```

2. Check MCP server imports:
   ```bash
   python -c "from app.mcp.server import mcp; print('OK')"
   ```

3. Verify FastAPI is running:
   ```bash
   curl http://127.0.0.1:8000/docs
   ```

### "Tools not showing in Copilot Chat"

1. Check MCP server output for errors:
   - Look at VS Code Debug Console (`Ctrl+Shift+Y`).
   
2. Reload the window:
   - `Ctrl+Shift+P` → `Developer: Reload Window`.

3. Restart the MCP server:
   - Stop Python process.
   - Start FastAPI again.
   - Reload VS Code.

### "Timeout errors when calling tools"

- Increase `KNOWLEDGE_SERVER_TIMEOUT_SECONDS` to `30`.
- Verify FastAPI is not overloaded.
- Check database connectivity in FastAPI logs.

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `KNOWLEDGE_SERVER_BASE_URL` | `http://127.0.0.1:8000` | FastAPI endpoint URL |
| `KNOWLEDGE_SERVER_TIMEOUT_SECONDS` | `15` | HTTP timeout for knowledge server calls |

## Quick Reference Commands

```bash
# Start FastAPI
uvicorn app.main:app --reload

# Verify MCP server works
python -c "from app.mcp.server import mcp; print('MCP server initialized')"

# Run unit tests
pytest tests/test_mcp_server.py -v

# Check if tools are discoverable
python -m app.mcp.server --help
```

## File Locations

- **MCP Server**: `app/mcp/server.py`
- **FastAPI App**: `app/main.py`
- **Git Script**: `git-scripts/extract_regex_from_commit.py`
- **Unit Tests**: `tests/test_mcp_server.py`
- **Config**: `.vscode/mcp.json`
