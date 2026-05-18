"""
embeddings/embedder.py

WHY sentence-transformers instead of OpenAI embeddings?
  - Runs 100% locally — no API cost per search
  - all-MiniLM-L6-v2 is tiny (80MB), fast, and great for semantic similarity
  - OpenAI embeddings cost money on every note save AND every search query
  - Local model = instant search with zero ongoing cost

WHY lazy loading?
  Loading the model takes ~2 seconds. We do it once on first use,
  not at import time, so the app starts instantly.
"""
from __future__ import annotations

_model = None  # module-level singleton


def get_model():
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # all-MiniLM-L6-v2: 80MB, 384-dim vectors, excellent for short texts
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list[float]:
    """Convert any text string into a 384-dimensional embedding vector."""
    model = get_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()


def embed_note(title: str, content: str) -> list[float]:
    """
    Embed a note by combining title + content.
    Weighting the title more makes search results title-aware.
    """
    combined = f"{title}\n{title}\n{content}"   # title repeated = higher weight
    return embed_text(combined)
