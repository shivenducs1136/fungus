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

5. **Access the Application:**
   - Frontend (Release): `http://localhost:3000`
   - Frontend (Dev): `http://localhost:5173`
   - API Base URL: `http://localhost:8000`
   - API Swagger Docs: `http://localhost:8000/docs`

Note: Start only one API profile at a time (`release` or `dev`) because both map to port `8000`.

## Running from Docker Hub

The production API image is available on Docker Hub at `gsquare3/fungus`.

### Prerequisites

- Docker installed and running
- Docker Hub account with access to the private `gsquare3/fungus` repository
- Environment variables configured (see below)

### Pulling the Image

First, authenticate with Docker Hub:

```bash
docker login
```

Then pull the image:

```bash
docker pull gsquare3/fungus:latest
```

Or specify a version:

```bash
docker pull gsquare3/fungus:1.0.0
```

### Setting Up Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration — required, no default
DATABASE_URL=postgresql://postgres:your_password@db:5432/fungus
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=fungus

# API key — all context API calls require X-API-Key: <value>
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
FUNGUS_API_KEY=your_generated_key

# CORS — comma-separated list of allowed browser origins
ALLOWED_ORIGINS=https://your-frontend-domain.com

# MCP Server
KNOWLEDGE_SERVER_BASE_URL=http://your-server:8000
KNOWLEDGE_SERVER_TIMEOUT_SECONDS=15

# Logging
FUNGUS_LOG_LEVEL=INFO
```

> Copy `.env.example` to `.env` and fill in the values. `DATABASE_URL` and `FUNGUS_API_KEY` are required — the server will not start without them.

### Running the Image

**Option 1: Using environment variables directly**

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:password@db:5432/fungus" \
  -e POSTGRES_USER="postgres" \
  -e POSTGRES_PASSWORD="your_password" \
  -e POSTGRES_DB="fungus" \
  -e FUNGUS_API_KEY="your_generated_key" \
  -e ALLOWED_ORIGINS="https://your-frontend-domain.com" \
  -e KNOWLEDGE_SERVER_BASE_URL="http://your-server:8000" \
  gsquare3/fungus:latest
```

**Option 2: Using an environment file**

```bash
docker run -p 8000:8000 --env-file .env gsquare3/fungus:latest
```

### Accessing the Application

Once the container is running:

- **API Base URL:** `http://localhost:8000`
- **API Swagger Docs:** `http://localhost:8000/docs`
- **API ReDoc:** `http://localhost:8000/redoc`

### Giving Others Access

To grant another user access to the private image:

1. Go to [Docker Hub](https://hub.docker.com)
2. Navigate to your `fungus` repository
3. Click on "Collaborators"
4. Add their Docker Hub username
5. They will receive an invite and can then pull the image

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

### Distributing as a Standalone Executable

The MCP server can be packaged into a single `fungus-mcp.exe` so users need no Python installation.

**Build (Windows, from repo root):**

```powershell
.\build\build_exe.ps1
```

This installs PyInstaller into the active venv if needed and produces `dist\fungus-mcp.exe` (~20 MB).

**Ship to users:**

| File | Purpose |
|---|---|
| `dist\fungus-mcp.exe` | Self-contained MCP server |
| `build\mcp_distribution.json` | Drop-in `mcp.json` — update `command` path, rename to `mcp.json` |

**User setup (no Python required):**

1. Place `fungus-mcp.exe` anywhere (e.g. `C:\Tools\fungus-mcp.exe`).
2. Create `mcp.json` (location depends on client — see below) with:

```json
{
  "servers": {
    "fungus-knowledge": {
      "type": "stdio",
      "command": "C:\\Tools\\fungus-mcp.exe",
      "args": [],
      "env": {
        "KNOWLEDGE_SERVER_BASE_URL": "http://<your-server>:8000",
        "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15"
      }
    }
  }
}
```

The exe is launched automatically by the MCP client (VS Code / Cursor / Claude Desktop) — users never run it directly.

**Clean rebuild:**

```powershell
.\build\build_exe.ps1 -Clean
```

### Run Locally

1. Start the FastAPI Knowledge Server (for example with Docker or uvicorn).
2. Start the MCP server process:

```bash
python -m app.mcp.server
```

### Run Tests

Run all commands from repository root `D:/Fungus/fungus` unless noted.

#### Backend (Python)

```bash
.venv/Scripts/python.exe -m pytest -q
```

Run only API tests:

```bash
.venv/Scripts/python.exe -m pytest -q tests/test_api.py
```

Run only MCP server tests:

```bash
.venv/Scripts/python.exe -m pytest -q tests/test_mcp_server.py
```

Run only git-scripts tests:

```bash
.venv/Scripts/python.exe -m pytest -q git-scripts/test_extract_regex_from_commit.py
```

#### Frontend (Vite + Vitest)

```bash
cd frontend
npm test -- --run
```

Coverage:

```bash
cd frontend
npm run test:coverage
```

### Knowledge Server Logging

When you run the FastAPI Knowledge Server, logs are written to the configured log directory.

Start the API server:

```bash
uvicorn app.main:app --reload
```

Default log files:

- `logs/knowledge_server.log` (FastAPI knowledge server)
- `logs/mcp_server.log` (MCP stdio server)
- `logs/extract_regex_from_commit.log` (git extraction script)

### MCP Client Configuration

Use the same stdio command for all clients:

```bash
python -m app.mcp.server
```

#### Claude Desktop

Add to Claude's MCP config file (for example `claude_desktop_config.json`):

**Using the standalone exe (recommended for distribution):**
```json
{
   "mcpServers": {
      "fungus-knowledge": {
         "command": "C:\\Tools\\fungus-mcp.exe",
         "args": [],
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15"
         }
      }
   }
}
```

**Using Python directly (development):**
```json
{
   "mcpServers": {
      "fungus-knowledge": {
         "command": "python",
         "args": ["-m", "app.mcp.server"],
         "cwd": "D:/Fungus/fungus",
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15",
            "FUNGUS_API_KEY": "your_generated_key",
            "FUNGUS_LOG_LEVEL": "INFO"
         }
      }
   }
}
```

#### Cursor

Add to Cursor MCP config (same schema):

**Using the standalone exe (recommended for distribution):**
```json
{
   "mcpServers": {
      "fungus-knowledge": {
         "command": "C:\\Tools\\fungus-mcp.exe",
         "args": [],
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15",
            "FUNGUS_API_KEY": "your_generated_key"
         }
      }
   }
}
```

**Using Python directly (development):**
```json
{
   "mcpServers": {
      "fungus-knowledge": {
         "command": "python",
         "args": ["-m", "app.mcp.server"],
         "cwd": "D:/Fungus/fungus",
         "env": {
            "KNOWLEDGE_SERVER_BASE_URL": "http://127.0.0.1:8000",
            "KNOWLEDGE_SERVER_TIMEOUT_SECONDS": "15",
            "FUNGUS_API_KEY": "your_generated_key",
            "FUNGUS_LOG_LEVEL": "INFO"
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
   - Environment: Set `KNOWLEDGE_SERVER_BASE_URL=http://127.0.0.1:8000` and `FUNGUS_API_KEY=your_generated_key`

3. **Reload window** and open Copilot Chat to access:
   - `save_knowledge`
   - `retrieve_knowledge`
   - `retrieve_knowledge_from_code`

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string. Server refuses to start if unset |
| `FUNGUS_API_KEY` | **Yes (prod)** | — | Secret key required in `X-API-Key` header on all context API calls. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FUNGUS_AUTH_DISABLED` | No | `false` | Set to `true` to skip API key enforcement in local dev only. Never set in production |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173` | Comma-separated list of browser origins permitted by CORS |
| `API_BASE_URL` | No | `http://api:8000` | Internal API URL used by the nginx proxy in the production frontend container |
| `KNOWLEDGE_SERVER_BASE_URL` | No | `http://127.0.0.1:8000` | URL of the FastAPI knowledge server (used by MCP server) |
| `KNOWLEDGE_SERVER_TIMEOUT_SECONDS` | No | `15` | HTTP timeout for knowledge server calls |
| `FUNGUS_LOG_LEVEL` | No | `INFO` | Log verbosity: `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `FUNGUS_LOG_DIR` | No | `<repo_root>/logs/` | Directory where log files are written |
| `DEMO_EMAIL_ENABLED` | No | `false` | Enable demo booking confirmation email automation |
| `SMTP_HOST` | No | — | SMTP host for outgoing emails |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USERNAME` | No | — | SMTP auth username |
| `SMTP_PASSWORD` | No | — | SMTP auth password |
| `SMTP_PASSWORD_ENCRYPTED` | No | — | Encrypted SMTP password (preferred over plain text) |
| `SMTP_CREDENTIALS_KEY` | No | — | Fernet key used to decrypt `SMTP_PASSWORD_ENCRYPTED` |
| `SMTP_CREDENTIALS_KEY_FILE` | No | `/run/secrets/smtp_credentials_key` | Path to file containing Fernet decryption key (preferred) |
| `SMTP_SENDER_EMAIL` | No | `SMTP_USERNAME` | Sender email address |
| `SMTP_USE_TLS` | No | `true` | Use STARTTLS for SMTP transport |

Copy `.env.example` to `.env` and adjust as needed.

**Log level quick reference:**
- `DEBUG` — full trace including every git call, HTTP request detail, and intermediate results
- `INFO` — normal operation: tool calls, JIRA IDs resolved, HTTP responses (default)
- `WARNING` — only misconfiguration warnings and recoverable issues
- `ERROR` / `CRITICAL` — failures only

### Validation Test

Run MCP tests:

```bash
pytest tests/test_mcp_server.py -v
```

## Demo Booking API

Create a demo booking:

```bash
POST /api/v1/demo-bookings/
```

Request payload:

```json
{
   "name": "Ada Lovelace",
   "work_email": "ada@company.com",
   "time": "10:30 AM UTC",
   "contact_number": "+14155552671",
   "short_note": "Need architecture walkthrough",
   "scheduled_datetime": "2026-08-20T10:30:00+00:00"
}
```

The API stores these fields and also generates:

- `submitted_datetime` (UTC timestamp when form was submitted)
- `booking_id`

After successful creation, the backend automatically attempts to send a confirmation email to `work_email`.

Manual email automation script:

```bash
python -m app.scripts.auto_email_demo_booking --email someone@company.com --name "Jane Doe" --scheduled-datetime "2026-08-15T10:30:00+00:00" --time "10:30 AM UTC" --contact-number "+15551234567"
```

### Encrypted SMTP Password Setup

You can keep encrypted SMTP credentials in `.env` and decrypt at runtime.

1. Generate a Fernet key (store securely, not in git):
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. Encrypt your SMTP password using that key:
   ```bash
   python -c "from cryptography.fernet import Fernet; key='PASTE_KEY'; print(Fernet(key.encode()).encrypt('PASTE_SMTP_PASSWORD'.encode()).decode())"
   ```

3. Store key outside `.env` in a file on the server (or Docker secret) at `/run/secrets/smtp_credentials_key`.

If you run with Docker Compose, this repository now mounts a secret named `smtp_credentials_key` automatically for `api-dev` and `api-release`.

- Default source file on host: `./secrets/smtp_credentials_key`
- Optional override: set `SMTP_CREDENTIALS_KEY_SOURCE_FILE` to another host file path

Create the secret source file before `docker compose up`:

```bash
mkdir -p secrets
printf "%s" "PASTE_KEY_HERE" > secrets/smtp_credentials_key
```

4. Configure environment values:
   - `SMTP_PASSWORD_ENCRYPTED=<ciphertext from step 2>`
   - `SMTP_CREDENTIALS_KEY_FILE=/run/secrets/smtp_credentials_key`
   - leave `SMTP_PASSWORD` empty

At runtime the app uses `SMTP_PASSWORD_ENCRYPTED` first; if absent, it falls back to `SMTP_PASSWORD`.
For decryption key lookup, it reads `SMTP_CREDENTIALS_KEY_FILE` first and only falls back to `SMTP_CREDENTIALS_KEY` for backward compatibility.

## TODO
- Add server-side pagination to `GET /context/` and `GET /context/jira/{id}` endpoints and wire frontend to use server params instead of client-side slicing.
- Migrate database interactions from synchronous `psycopg2-binary` + SQLAlchemy to asynchronous using `asyncpg` to follow FastAPI best practices for async I/O.
- Set up Alembic for schema migrations so production schema changes have a safe rollback path.
