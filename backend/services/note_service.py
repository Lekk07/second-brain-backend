"""
services/note_service.py
CRUD logic + auto-indexing into ChromaDB on every write.
"""
from extensions import db
from models import Note


def _try_index(note):
    """Index into ChromaDB — silently skip if ML packages not installed yet."""
    try:
        from services.search_service import index_note
        index_note(note)
        db.session.commit()   # persist embedding_id
    except ImportError:
        pass   # sentence-transformers not installed yet — that's fine
    except Exception as e:
        print(f"[search] indexing skipped: {e}")


def _try_remove_index(user_id, note_id):
    try:
        from services.search_service import remove_note_index
        remove_note_index(user_id, note_id)
    except Exception:
        pass


def get_all_notes(user_id: int, search: str = None, tag: str = None) -> list[dict]:
    query = Note.query.filter_by(user_id=user_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(Note.title.ilike(pattern), Note.content.ilike(pattern))
        )
    if tag:
        query = query.filter(Note.tags.ilike(f"%{tag}%"))
    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    return [n.to_dict() for n in notes]


def get_note_by_id(note_id: int, user_id: int) -> dict | None:
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    return note.to_dict() if note else None


def create_note(user_id: int, data: dict) -> tuple[dict, str | None]:
    title   = data.get("title", "").strip()
    content = data.get("content", "").strip()
    if not title:   return None, "Title is required"
    if not content: return None, "Content is required"
    if len(title) > 200: return None, "Title must be under 200 characters"

    tags_input = data.get("tags", [])
    tags_str = ", ".join(tags_input) if isinstance(tags_input, list) else str(tags_input)

    note = Note(
        title=title, content=content, tags=tags_str,
        is_pinned=bool(data.get("is_pinned", False)),
        color=data.get("color", "#1e1e2e"),
        user_id=user_id,
    )
    db.session.add(note)
    db.session.commit()
    _try_index(note)
    return note.to_dict(), None


def update_note(note_id: int, user_id: int, data: dict) -> tuple[dict | None, str | None]:
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note: return None, "Note not found"

    if "title" in data:
        title = data["title"].strip()
        if not title: return None, "Title cannot be empty"
        note.title = title
    if "content" in data:
        content = data["content"].strip()
        if not content: return None, "Content cannot be empty"
        note.content = content
    if "tags" in data:
        tags_input = data["tags"]
        note.tags = ", ".join(tags_input) if isinstance(tags_input, list) else str(tags_input)
    if "is_pinned" in data:
        note.is_pinned = bool(data["is_pinned"])
    if "color" in data:
        note.color = data["color"]

    from datetime import datetime, timezone
    note.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    _try_index(note)
    return note.to_dict(), None


def delete_note(note_id: int, user_id: int) -> bool:
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note: return False
    _try_remove_index(user_id, note_id)
    db.session.delete(note)
    db.session.commit()
    return True


def toggle_pin(note_id: int, user_id: int) -> tuple[dict | None, str | None]:
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note: return None, "Note not found"
    note.is_pinned = not note.is_pinned
    db.session.commit()
    return note.to_dict(), None


def get_all_tags(user_id: int) -> list[str]:
    notes = Note.query.filter_by(user_id=user_id).all()
    tag_set = set()
    for note in notes:
        for tag in (note.tags or "").split(","):
            t = tag.strip()
            if t: tag_set.add(t)
    return sorted(tag_set)
