# PulseAPI Docs Assistant

A conversational AI chatbot that answers developer questions about **PulseAPI** (a fictional REST API for sending transactional email, SMS, and push notifications) — built with LangChain/LangGraph, with both a Streamlit demo UI and a production-style FastAPI backend + embeddable chat widget.

## What This Demonstrates

- **Code-first agent development with LangChain/LangGraph** — a deliberate contrast to the visual/no-code n8n approach used in a separate project ([`support-triage-agent`](https://github.com/sbalne/support-triage-agent))
- **Multi-turn conversational memory** using LangGraph's checkpointer-based persistence (the current-recommended pattern, replacing the now-deprecated `RunnableWithMessageHistory`)
- **Scoped, boundary-aware prompting** — an assistant that stays strictly within its documentation domain, corrects false premises, and resists prompt injection attempts
- **A real path to production** — the same chatbot logic exposed as a REST API (FastAPI) and connected to a standalone HTML/JS chat widget, not just a Streamlit demo

## Architecture

```
User message
   ↓
LangGraph StateGraph (single node: call_model)
   ↓
Claude (Anthropic API), with:
   - System prompt defining scope + the full PulseAPI documentation
   - Full conversation history (via MemorySaver checkpointer, keyed by thread_id)
   ↓
Response
```

Two interchangeable front-ends sit on top of the same core chatbot logic:

| Front-end | Purpose |
|---|---|
| **Streamlit app** (`app/app.py`) | Quick, shareable demo UI — run locally with `streamlit run app.py` |
| **FastAPI backend + HTML widget** (`backend/api.py` + `widget/index.html`) | Demonstrates the actual production integration pattern: a REST `/chat` endpoint (analogous to a Spring Boot `@RestController`) called from a standalone floating chat-bubble widget, the same pattern real "Chat with us" website widgets use |

## Why LangGraph, Not RunnableWithMessageHistory

This project originally used LangChain's `RunnableWithMessageHistory` for conversation memory, but that pattern is deprecated as of LangChain v0.3.1+ in favor of LangGraph's built-in checkpointer-based persistence. The project was migrated to LangGraph's `StateGraph` + `MemorySaver` pattern, which is also better aligned with how LangChain recommends building stateful agents going forward.

## Testing

The assistant was tested against 5 edge cases targeting common chatbot failure modes: multi-part questions, memory-dependent follow-ups, false-premise/trick questions, prompt injection attempts, and ambiguous interpretive questions. All 5 passed without requiring prompt revisions — full results and reasoning in [`tests/test_results.md`](./tests/test_results.md).

## Known Limitations

- **No real retrieval (RAG) yet.** The entire documentation file is stuffed directly into the system prompt on every request. This works for a short doc like PulseAPI's, but wouldn't scale to a large documentation site. A vector-search-based RAG upgrade is a planned next step.
- **In-memory conversation storage.** `MemorySaver` keeps conversation history in RAM only — history is lost on server restart. A production deployment would use a persistent checkpointer (e.g., backed by Postgres or Redis).
- **CORS is wide open (`allow_origins=["*"]`)** in the FastAPI backend for local demo purposes. A real deployment would restrict this to the actual hosting domain.
- **No authentication on the `/chat` endpoint.** A production API would need rate limiting and/or API key auth to prevent abuse.

## Stack

Python · LangChain · LangGraph · Anthropic API (Claude) · Streamlit · FastAPI · Uvicorn · HTML/CSS/JavaScript

## Files

| Path | Contents |
|---|---|
| [`app/`](./app) | Streamlit demo application |
| [`backend/`](./backend) | FastAPI REST backend exposing the chatbot as a `/chat` endpoint |
| [`widget/`](./widget) | Standalone HTML/CSS/JS chat widget demonstrating a real embeddable "chat with us" integration |
| [`docs/`](./docs) | PulseAPI documentation content and the system prompt template |
| [`tests/`](./tests) | Edge-case test results |
