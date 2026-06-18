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

You can easily run the Fungus Knowledge Server and its required database using Docker Compose.

1. **Start the stack**:
   ```bash
   docker compose up --build -d
   ```
   This will build the API image and start both the API and a PostgreSQL database in the background.

2. **Access the API**:
   The API will be available at `http://localhost:8000`. You can view the interactive Swagger documentation at `http://localhost:8000/docs`.

3. **Stop the stack**:
   ```bash
   docker compose down
   ```
