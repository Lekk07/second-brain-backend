"""
routes/search.py

GET /api/search?q=your+query&limit=8

Returns notes ranked by semantic similarity to the query.
Falls back to empty list if ML packages aren't installed yet.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

search_bp = Blueprint("search", __name__, url_prefix="/api")


def success(data=None, status=200):
    return jsonify({"success": True, "data": data}), status


def error(message, status=400):
    return jsonify({"success": False, "error": message}), status


@search_bp.route("/search", methods=["GET"])
@jwt_required()
def semantic_search():
    user_id = int(get_jwt_identity())
    query   = request.args.get("q", "").strip()
    limit   = min(int(request.args.get("limit", 8)), 20)

    if not query:
        return error("Query parameter 'q' is required")

    try:
        from services.search_service import semantic_search as do_search
        results = do_search(user_id, query, top_k=limit)
        return success({"query": query, "results": results, "count": len(results)})

    except ImportError:
        return error(
            "Semantic search not available — run: pip install sentence-transformers chromadb",
            503,
        )
    except Exception as e:
        return error(f"Search error: {str(e)}", 500)


@search_bp.route("/search/reindex", methods=["POST"])
@jwt_required()
def reindex_all():
    """
    Re-index all existing notes for a user.
    Call this once after installing sentence-transformers
    if you already have notes in the DB.
    """
    user_id = int(get_jwt_identity())

    try:
        from models import Note
        from services.search_service import index_note
        from extensions import db

        notes = Note.query.filter_by(user_id=user_id).all()
        for note in notes:
            index_note(note)
        db.session.commit()

        return success({"indexed": len(notes)})
    except ImportError:
        return error("Run: pip install sentence-transformers chromadb", 503)
    except Exception as e:
        return error(str(e), 500)
