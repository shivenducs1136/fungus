# MCP Server — Deep Knowledge

This MCP server exposes two tools to Cline:

- `preserve_deep_knowledge` — capture and store architectural context before a commit
- `fetch_knowledge` — retrieve stored context by `ctx-hash` before modifying existing code

---

## Setup

### 1. Start the knowledge server

```bash
python knowledge-server/server.py
```

The server must be running on `http://localhost:8000` before any MCP tool call.

### 2. Register the MCP server with Cline

Add the following to your Cline MCP settings (`cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "deep-knowledge": {
      "command": "python",
      "args": ["D:\\myrepos\\deep-knowledge\\mcp-server\\mcp_server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 3. Restart VS Code

Cline auto-starts the MCP server on load. Both tools become available immediately.

---

## Tool: `preserve_deep_knowledge`

Captures architectural reasoning for one or more Jira tickets and stores it in the knowledge server.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickets` | `list[str]` | ✅ | List of Jira ticket IDs, e.g. `["TPR-48892"]` or `["[TPR-48892]", "TPR-12345"]` |
| `focus` | `str` | ✅ | One-line description of what this change fixes or implements |
| `discovered_constraints` | `list[str]` | ✅ | Constraints discovered during investigation (legacy rules, hidden deps, etc.) |
| `discarded_approaches` | `list[str]` | ✅ | Approaches tried and rejected, with reasons |
| `final_solution` | `str` | ✅ | Precise description of the solution implemented |

**Returns:** A line to append as the absolute last line of the Git commit message:
```
Deep-Knowledge-Key: ctx-<hash>
```

**When to call:** Before generating or suggesting a Git commit message for any non-trivial change.

---

## Tool: `fetch_knowledge`

Fetches and returns the stored architectural knowledge document for a given `Deep-Knowledge-Key`.

> **Note:** This tool only performs the HTTP lookup. Cline is responsible for running `git blame` and `git log` via `execute_command` to extract the `ctx-hash` from the commit message **before** calling this tool.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ctx_hash` | `str` | ✅ | The `Deep-Knowledge-Key` value extracted from the commit message, e.g. `"ctx-a86482cc3ed6"`. The `"ctx-"` prefix is required. |

**Pre-call workflow (Cline runs these steps via `execute_command`):**

1. **git blame** — identify the commit that last touched the line:
   ```bash
   git -C <repo_dir> blame --porcelain -L <line>,<line> -- <file_path>
   ```
   Extract the 40-character commit hash from the **first token** of the output.

2. **git log** — read the full commit message:
   ```bash
   git -C <repo_dir> log -1 --format="%B" <commit_hash>
   ```

3. **Extract the key** — search the commit message with the regex:
   ```
   Deep-Knowledge-Key: (ctx-[a-zA-Z0-9]+)
   ```
   If no key is found, there is no stored knowledge for this commit — proceed normally.

4. **Call `fetch_knowledge`** with the extracted key.

**Returns:** The full knowledge document as formatted Markdown:

```markdown
# Knowledge Document: ctx-<hash>

## Ticket: TPR-XXXXX

**Focus:** <one-line description>

**Discovered Constraints:**
- <constraint 1>
- <constraint 2>

**Discarded Approaches:**
- <approach tried and rejected, with reason>

**Final Solution:** <precise description of the solution implemented>
```

Returns an error message (`No knowledge document found for key: ctx-xxx`) if no document exists for the given key.

**When to call:** Before modifying any file that has existing commits — check whether those commits carry a `Deep-Knowledge-Key` and retrieve the context before making changes.

---

## Example Workflow

### Capturing knowledge (before a commit)

```
Cline calls preserve_deep_knowledge(
  tickets=["TPR-48892"],
  focus="Fix refresh issue in GCC vat applicability for OTG expense ledger",
  discovered_constraints=["Legacy GSTIN creation condition was bypassing the state check."],
  discarded_approaches=["Forcing UI refresh caused infinite loop in legacy UI wrapper."],
  final_solution="Corrected the create with GSTIN boolean condition directly in the ledger data model."
)
→ Returns: "Deep-Knowledge-Key: ctx-8589f5485964"
```

Append the returned line as the last line of the commit message.

### Retrieving knowledge (before modifying existing code)

```bash
# Step 1
git -C D:\myrepos\myproject blame --porcelain -L 21,21 -- ledger_model.cpp
# → extract commit hash, e.g. a1b2c3d4...

# Step 2
git -C D:\myrepos\myproject log -1 --format="%B" a1b2c3d4...
# → read commit message, find "Deep-Knowledge-Key: ctx-8589f5485964"

# Step 3 — call fetch_knowledge(ctx_hash="ctx-8589f5485964")
```

Read the returned document carefully before making any changes. **Do not repeat a discarded approach.**