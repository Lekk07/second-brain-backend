"""
services/search_service.py

Two entry points:
  index_note()   — called whenever a note is created or updated
  semantic_search() — called by the search route
"""
from models import Note
from embeddings.embedder import embed_text, embed_note
from vector_db.store import upsert_note, delete_note, search_notes


def index_note(note) -> None:
    """
    Generate an embedding for a note and store it in ChromaDB.
    'note' is a SQLAlchemy Note model instance.
    """
    embedding = embed_note(note.title, note.content)

    metadata = {
        "title":     note.title,
        "tags":      note.tags or "",
        "is_pinned": str(note.is_pinned),
        "color":     note.color or "#1e1e2e",
    }

    upsert_note(
        user_id=note.user_id,
        note_id=note.id,
        embedding=embedding,
        metadata=metadata,
    )

    # Persist the embedding_id so we can track it in SQLite
    note.embedding_id = str(note.id)


def remove_note_index(user_id: int, note_id: int) -> None:
    """Remove a note's vector when the note is deleted."""
    delete_note(user_id, note_id)


def semantic_search(user_id: int, query: str, top_k: int = 8) -> list[dict]:
    """
    Semantic search across a user's notes.

    Steps:
      1. Embed the raw query text
      2. Find nearest vectors in ChromaDB
      3. Fetch full note data from SQLite
      4. Return enriched results sorted by relevance score

    WHY fetch from SQLite after vector search?
      ChromaDB metadata is a flat dict (no lists, no long text).
      We store only lightweight metadata there, then join back to
      the full note for content/summary/tags.
    """
    if not query.strip():
        return []

    query_embedding = embed_text(query)
    hits = search_notes(user_id, query_embedding, top_k=top_k)

    if not hits:
        return []

    # Batch fetch matching notes from SQLite
    note_ids = [h["note_id"] for h in hits]
    notes_map = {
        n.id: n.to_dict()
        for n in Note.query.filter(
            Note.id.in_(note_ids),
            Note.user_id == user_id
        ).all()
    }

    # Merge vector score into note data
    results = []
    for hit in hits:
        note = notes_map.get(hit["note_id"])
        if note:
            note["score"] = hit["score"]
            results.append(note)

    # Already sorted by score from ChromaDB, but re-sort to be safe
    return sorted(results, key=lambda x: x["score"], reverse=True)
