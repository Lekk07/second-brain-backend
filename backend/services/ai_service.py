"""
services/ai_service.py

WHY lazy client init?
  Creating the OpenAI client at module level crashes if OPENAI_API_KEY
  is missing. Lazy init (inside each function) means the app starts fine
  and only errors when you actually call the AI endpoint.
"""
import os
from extensions import db
from models import Note

SUMMARY_PROMPT = """You are a personal knowledge assistant.
Summarize the following note in 2-3 crisp sentences.
Focus on the key ideas. Be concise and insightful.
Do not start with "This note" or "The author".
Just give the summary directly."""


def _get_client():
    """Lazy OpenAI client — only created when needed."""
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set in .env")
    return OpenAI(api_key=key)


def generate_summary(note_id: int, user_id: int) -> tuple[str | None, str | None]:
    """Generate an AI summary for a note and persist it.
    Returns (summary_text, error_message)."""
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return None, "Note not found"

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=150,
            temperature=0.5,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user",   "content": f"Title: {note.title}\n\n{note.content}"},
            ],
        )
        summary = response.choices[0].message.content.strip()
        note.summary = summary
        db.session.commit()
        return summary, None

    except ValueError as e:
        return None, str(e)
    except Exception as e:
        return None, f"OpenAI error: {str(e)}"


def clear_summary(note_id: int, user_id: int) -> tuple[bool, str | None]:
    """Remove the AI summary from a note."""
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return False, "Note not found"
    note.summary = None
    db.session.commit()
    return True, None
