# PulseAPI Docs Assistant

A conversational AI chatbot that answers developer questions about **PulseAPI** (a fictional REST API for sending transactional email, SMS, and push notifications) — built with LangChain/LangGraph and real retrieval-augmented generation (RAG), with both a Streamlit demo UI and a production-style FastAPI backend + embeddable chat widget.

## What This Demonstrates

- **Code-first agent development with LangChain/LangGraph** — a deliberate contrast to the visual/no-code n8n approach used in a separate project ([`support-triage-agent`](https://github.com/sravanibalne/support-triage-agent))
- **Real retrieval-augmented generation (RAG)** — documentation is chunked, embedded (OpenAI `text-embedding-3-small`), and stored in a Pinecone vector database. Each user question triggers a fresh semantic similarity search, so only the relevant chunks are sent to the model — not the entire document
- **Multi-turn conversational memory** using LangGraph's checkpointer-based persistence, working correctly alongside per-message retrieval (verified: the assistant can resolve a contextual follow-up like "is the Go one officially supported?" using prior conversation history, while retrieval independently fetches fresh relevant context for that specific message)
- **Scoped, boundary-aware prompting** — an assistant that stays strictly within its documentation domain, corrects false premises, and resists prompt injection attempts
- **A real path to production** — the same chatbot logic exposed as a REST API (FastAPI) and connected to a standalone HTML/JS chat widget, not just a Streamlit demo
- **Manual agent-loop implementation** (see `agent_loop.py` in the training repo) — a hand-built ReAct-style tool-calling loop using `StateGraph` with conditional edges, alongside the equivalent `create_agent` prebuilt shortcut, to demonstrate understanding of the underlying mechanics rather than just the high-level API

## Architecture

```
Document ingestion (one-time, ingest.py):
PulseAPI docs (.md) → chunked (RecursiveCharacterTextSplitter) → embedded (OpenAI) → stored in Pinecone

Runtime (per user message):
User message
   ↓
Embed the message → semantic similarity search against Pinecone → top-k relevant chunks retrieved
   ↓
LangGraph StateGraph (single node: call_model)
   ↓
Claude (Anthropic API), with:
   - System prompt: scope rules + only the retrieved chunks (not the full doc)
   - Full conversation history (via MemorySaver checkpointer, keyed by thread_id)
   ↓
Response
```

Two interchangeable front-ends sit on top of the same core chatbot logic:

| Front-end | Purpose |
|---|---|
| **Streamlit app** (`app/app.py`) | Quick, shareable demo UI — run locally with `streamlit run app.py` |
| **FastAPI backend + HTML widget** (`backend/api.py` + `widget/index.html`) | Demonstrates the actual production integration pattern: a REST `/chat` endpoint (analogous to a Spring Boot `@RestController`) called from a standalone floating chat-bubble widget |

## Why RAG, and Why It Replaced the Original Approach

The original version of this project stuffed the entire PulseAPI documentation file into the system prompt on every single request. That worked because the fictional doc was short, but it doesn't reflect how real documentation assistants are built — a real docs site can be hundreds of pages, which wouldn't fit in a context window, would be slow, and would cost more per request than necessary.

The RAG upgrade replaces that with real semantic search: documents are chunked and embedded once (`ingest.py`), stored in Pinecone, and each user question triggers a fresh retrieval of just the relevant chunks. This was verified to work correctly on meaning, not just keyword overlap — e.g., the query "how do I stop getting rate limited?" correctly retrieved the Rate Limits and 429 error sections, despite sharing no exact wording with either.

## Why LangGraph, Not RunnableWithMessageHistory

This project originally used LangChain's `RunnableWithMessageHistory` for conversation memory, but that pattern is deprecated as of LangChain v0.3.1+ in favor of LangGraph's built-in checkpointer-based persistence. The project was migrated to LangGraph's `StateGraph` + `MemorySaver` pattern.

## Testing

The assistant was tested against 5 edge cases targeting common chatbot failure modes: multi-part questions, memory-dependent follow-ups, false-premise/trick questions, prompt injection attempts, and ambiguous interpretive questions. All 5 passed without requiring prompt revisions — full results in [`tests/test_results.md`](./tests/test_results.md). The memory-dependent follow-up test was re-verified after the RAG migration to confirm conversation history and per-message retrieval work correctly together.

## Known Limitations

- **Chunk boundaries aren't fully clean.** Using a fixed `chunk_size`/`chunk_overlap` character-based splitter occasionally cuts across section boundaries, so a retrieved chunk can contain a trailing sentence from the previous section. This doesn't appear to affect answer quality in practice, but a structure-aware splitter (e.g., splitting explicitly on markdown headers) would produce cleaner chunks.
- **In-memory conversation storage.** `MemorySaver` keeps conversation history in RAM only — history is lost on server restart. A production deployment would use a persistent checkpointer (e.g., backed by Postgres or Redis).
- **CORS is wide open (`allow_origins=["*"]`)** in the FastAPI backend for local demo purposes. A real deployment would restrict this to the actual hosting domain.
- **No authentication on the `/chat` endpoint.** A production API would need rate limiting and/or API key auth to prevent abuse.
- **No formal retrieval evaluation.** Retrieval quality was spot-checked manually rather than measured against a systematic golden-dataset evaluation.

## Stack

Python · LangChain · LangGraph · Anthropic API (Claude) · OpenAI Embeddings · Pinecone · Streamlit · FastAPI · Uvicorn · HTML/CSS/JavaScript

## Files

| Path | Contents |
|---|---|
| [`app/`](./app) | Streamlit demo application |
| [`backend/`](./backend) | FastAPI REST backend exposing the chatbot as a `/chat` endpoint |
| [`widget/`](./widget) | Standalone HTML/CSS/JS chat widget demonstrating a real embeddable "chat with us" integration |
| [`docs/`](./docs) | PulseAPI documentation content, system prompt template, and `ingest.py` (chunking/embedding pipeline) |
| [`tests/`](./tests) | Edge-case test results |
