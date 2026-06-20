## Problem
AI-assisted software development generates valuable architectural reasoning during implementation.

The final code captures what was built, but not:

- Why a solution was chosen
- Constraints discovered during investigation
- Approaches that were tried and rejected
- Tradeoffs considered during implementation

This information is typically lost once the chat session ends.

Fungus preserves that reasoning and links it directly to source code through Git history.

## Goals
- Preserve architectural knowledge generated during AI-assisted development
- Associate implementation reasoning with Git commits
- Enable future engineers and AI agents to retrieve historical context
- Avoid vector databases, embeddings, semantic search, and RAG systems
- Provide deterministic O(1) retrieval using Git metadata

## Core Idea

When significant code changes are completed:

Developer + AI Discussion -> Architectural Reasoning -> Deep Knowledge Storage ->  Context Hash (ctx-xxxx) -> Git Commit Message  

The generated context hash becomes part of the commit message.  

Example:
__Deep-Knowledge-Key: ctx-a86482cc3ed6__

## Storage Flow
- Developer finishes a feature, bug fix, or architectural change.
- AI summarizes the implementation reasoning.
- MCP tool stores the reasoning.
- Knowledge server generates a unique context hash.
- Hash is appended to the Git commit message.

Result:  
Commit -> ctx-hash -> Knowledge Document

## Retrieval Flow

When a user asks:

- Explain this function
- Why is this implemented this way?
- Can this be simplified?
- What constraints exist here?

The system:

- Performs git blame on the code.
- Retrieves the commit hash.
- Reads the commit message.
- Extracts the Deep-Knowledge-Key.
- Retrieves the stored reasoning document.
- Uses that information when answering.

Result:  
Code -> Commit -> ctx-hash -> Knowledge

## Architecture
### Components  

__MCP Server__  

Responsible for:

- Saving architectural knowledge
- Retrieving architectural knowledge
- Running Git operations
- Interacting with the Knowledge Server

__Knowledge Server__

FastAPI-based service providing:

- Knowledge storage
- Context retrieval
- Hash generation
- Persistence

__Key-Value Store__

Stores:  

{  
  "ctx-a86482cc3ed6": {  
    "timestamp": "...",  
    "ticket": "ERP-24",  
    "content": "Architectural reasoning..."  
    ... }  
}  

## Flow Diagram

<img width="2165" height="969" alt="image" src="https://github.com/user-attachments/assets/fdbd93be-52ad-44b3-be67-11d618ec5325" />

## Vision

Code explains what exists.

Deep Knowledge explains why it exists.

The goal is to preserve implementation rationale so future developers and future AI agents can make informed decisions without repeating past investigations.

## Running with Docker

Use Docker Compose profiles to run either a production-like runtime image (`release`) or a development image (`dev`).

1. **Run release profile (runtime dependencies only):**
   ```bash
   docker compose --profile release up --build -d
   ```

2. **Run dev profile (runtime + dev dependencies, reload enabled):**
   ```bash
   docker compose --profile dev up --build -d
   ```

3. **View logs:**
   ```bash
   docker compose logs -f
   ```

4. **Stop and remove containers:**
   ```bash
   docker compose down
   ```

5. **Access the API:**
   - Base URL: `http://localhost:8000`
   - Swagger: `http://localhost:8000/docs`

Note: Start only one API profile at a time (`release` or `dev`) because both map to port `8000`.

## MCP Server (stdio)

This repository includes an MCP server layer that exposes two tools over `stdio` using the official Python SDK.

### Tools

- `save_knowledge` (generic)
   - Inputs: `jira_ids`, plus either `chat_context` or `content`, optional `metadata`.
   - Action: Stores active chat reasoning using `POST /api/v1/context/`.

- `retrieve_knowledge` (generic)
   - Inputs (option A): `jira_ids`, optional `depth`.
   - Inputs (option B): `file_path`, `start_line`, optional `end_line`, optional `depth`.
   - Action: If code location is provided, runs `git-scripts/extract_regex_from_commit.py` to infer JIRA IDs from commit history, then fetches context from FastAPI.

- Aliases available for chat naming flexibility:
   - `save_architectural_knowledge`
   - `save_architecture_knowledge`
   - `retrieve_architectural_knowledge`
   - `retrieve_knowledge_from_code`

### Intended Agent Flow

1. User says save command with JIRA IDs.
2. Client sends active chat text as `chat_context`.
3. MCP tool saves the document to FastAPI/DB.

For retrieval:

1. User asks about selected code (for example "explain this function").
2. Client provides selected file/line range.
3. MCP tool extracts JIRA IDs from git history and fetches matching context.
4. Tool returns both structured payload and a concatenated summary for chat display.

### Run Locally

1. Start the FastAPI Knowledge Server (for example with Docker or uvicorn).
2. Start the MCP server process:

```bash
python -m app.mcp.server
```

### MCP Client Configuration

Use the same stdio command for all clients:

```bash
python -m app.mcp.server
```

#### Claude Desktop

Add to Claude's MCP config file (for example `claude_desktop_config.json`):

```json
{
   "mcpServers": {
      "fungus-knowledge": {
         "command": "python",
         "args": ["-m", "app.mcp.server"],
         "cwd": "D:/Fungus/fungus",
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15"
         }
      }
   }
}
```

#### Cursor

Add to Cursor MCP config (same schema):

```json
{
   "mcpServers": {
      "fungus-knowledge": {
         "command": "python",
         "args": ["-m", "app.mcp.server"],
         "cwd": "D:/Fungus/fungus",
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15"
         }
      }
   }
}
```

#### GitHub Copilot (VS Code)

**See detailed setup guide**: [VSCODE_MCP_SETUP.md](VSCODE_MCP_SETUP.md)

Quick steps:

1. **Start dependencies**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Register MCP server in VS Code**:
   - Press `Ctrl+Shift+P` → `MCP: Add Server`.
   - Command: `python`
   - Args: `-m app.mcp.server`
   - Working directory: `D:\Fungus\fungus`
   - Environment: Set `KNOWLEDGE_SERVER_BASE_URL=http://127.0.0.1:8000`

3. **Reload window** and open Copilot Chat to access:
   - `save_knowledge`
   - `retrieve_knowledge`
   - `retrieve_knowledge_from_code`

- `KNOWLEDGE_SERVER_BASE_URL` (default: `http://127.0.0.1:8000`)
- `KNOWLEDGE_SERVER_TIMEOUT_SECONDS` (default: `15`)

### Validation Test

Run MCP tests:

```bash
pytest tests/test_mcp_server.py -v
```

## TODO
- Migrate database interactions from synchronous `psycopg2-binary` + SQLAlchemy to asynchronous using `asyncpg` to follow FastAPI best practices for async I/O.
