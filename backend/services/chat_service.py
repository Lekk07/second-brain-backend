"""
services/chat_service.py

WHY retrieve notes as context before answering?
  This is RAG — Retrieval-Augmented Generation.
  Instead of the LLM guessing from training data, we:
    1. Semantically search the user's notes for the most relevant ones
    2. Inject them as context into the system prompt
    3. The LLM answers GROUNDED in the user's actual knowledge base

  Result: answers are accurate, personal, and cite real notes.

WHY pass conversation history?
  LLMs are stateless — each API call is independent.
  We send the full conversation so the model can refer to
  earlier messages ("as I mentioned above…", "following up on…").
"""
import os
from models import Note


SYSTEM_PROMPT = """You are the user's personal Second Brain assistant.
You have access to excerpts from their notes below.
Answer questions using their notes as your primary source.
Be concise, insightful, and conversational.
If a note is relevant, mention its title naturally in your answer.
If the notes don't cover the question, say so honestly and answer from general knowledge.
Never make up note contents.

--- USER'S RELEVANT NOTES ---
{context}
--- END OF NOTES ---"""


def _get_client():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set in backend/.env")
    return OpenAI(api_key=key)


def _retrieve_context(user_id: int, query: str, top_k: int = 5) -> tuple[str, list[dict]]:
    """
    Find the most relevant notes for the query using semantic search.
    Falls back to recent notes if semantic search isn't available.
    Returns (formatted_context_string, list_of_source_notes).
    """
    source_notes = []

    # Try semantic search first
    try:
        from services.search_service import semantic_search
        results = semantic_search(user_id, query, top_k=top_k)
        if results:
            source_notes = results
    except Exception:
        pass

    # Fallback: grab the 5 most recent notes
    if not source_notes:
        notes = Note.query.filter_by(user_id=user_id)\
            .order_by(Note.updated_at.desc()).limit(top_k).all()
        source_notes = [n.to_dict() for n in notes]

    if not source_notes:
        return "No notes found.", []

    # Format notes into a readable context block
    lines = []
    for i, note in enumerate(source_notes, 1):
        score = f" [{note.get('score', '?')}% match]" if 'score' in note else ""
        tags  = ", ".join(note.get("tags", [])) or "none"
        lines.append(
            f"[Note {i}]{score}\n"
            f"Title: {note['title']}\n"
            f"Tags: {tags}\n"
            f"Content: {note['content'][:600]}{'…' if len(note['content']) > 600 else ''}"
        )
        if note.get("summary"):
            lines.append(f"Summary: {note['summary']}")
        lines.append("")   # blank line between notes

    return "\n".join(lines), source_notes


def chat(user_id: int, message: str, history: list[dict]) -> dict:
    """
    Send a message and get a response grounded in the user's notes.

    Args:
        user_id:  The authenticated user's ID
        message:  The latest user message
        history:  List of {role, content} dicts (previous turns)

    Returns:
        {reply, sources} where sources is the list of notes used as context
    """
    context_text, source_notes = _retrieve_context(user_id, message)

    # Build the messages array for the API
    system = SYSTEM_PROMPT.format(context=context_text)

    messages = [{"role": "system", "content": system}]

    # Include up to last 10 turns of history to stay within context limits
    for turn in history[-10:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Add the new user message
    messages.append({"role": "user", "content": message})

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=600,
            temperature=0.7,
            messages=messages,
        )
        reply = response.choices[0].message.content.strip()

        return {
            "reply":   reply,
            "sources": [
                {"id": n.get("id"), "title": n.get("title"), "score": n.get("score")}
                for n in source_notes
            ],
        }
    except ValueError as e:
        raise
    except Exception as e:
        raise RuntimeError(f"OpenAI error: {str(e)}")
