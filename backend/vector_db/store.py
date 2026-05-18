"""
vector_db/store.py

WHY ChromaDB?
  - Runs embedded (in-process, no separate server needed)
  - Persists to disk automatically
  - Simple Python API, perfect for a local second-brain app
  - Can swap to Pinecone/Weaviate later with minimal changes

Architecture:
  One ChromaDB collection per user keeps search isolated.
  Collection name: "user_{user_id}_notes"
  Each document ID matches the Note.id from SQLite.
"""
from __future__ import annotations
import os
import chromadb
from chromadb.config import Settings

# Persist vector DB next to the backend
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "instance", "chroma")
_client: chromadb.Client | None = None


def get_client() -> chromadb.Client:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _collection(user_id: int):
    """Get or create the ChromaDB collection for this user."""
    return get_client().get_or_create_collection(
        name=f"user_{user_id}_notes",
        metadata={"hnsw:space": "cosine"},   # cosine similarity for text
    )


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────

def upsert_note(user_id: int, note_id: int, embedding: list[float], metadata: dict):
    """
    Add or update a note's vector in ChromaDB.
    Call this every time a note is created or updated.
    """
    col = _collection(user_id)
    col.upsert(
        ids=[str(note_id)],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def delete_note(user_id: int, note_id: int):
    """Remove a note's vector when the note is deleted."""
    col = _collection(user_id)
    try:
        col.delete(ids=[str(note_id)])
    except Exception:
        pass  # Already gone — no problem


def search_notes(user_id: int, query_embedding: list[float], top_k: int = 8) -> list[dict]:
    """
    Find the top_k most semantically similar notes to the query.
    Returns list of {note_id, score, metadata} dicts sorted by relevance.
    """
    col = _collection(user_id)

    if col.count() == 0:
        return []

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, col.count()),
        include=["metadatas", "distances"],
    )

    hits = []
    for note_id, distance, meta in zip(
        results["ids"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score 0-100
        score = round((1 - distance / 2) * 100, 1)
        hits.append({
            "note_id": int(note_id),
            "score":   score,
            "meta":    meta,
        })

    return hits
