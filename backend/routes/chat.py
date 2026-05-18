"""
routes/chat.py

POST /api/chat
Body: { message: string, history: [{role, content}, ...] }

WHY send history from the client?
  The backend is stateless — it doesn't store conversation sessions.
  The frontend owns the conversation state and sends it on every request.
  This is simpler, more scalable, and avoids server-side session storage.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.chat_service import chat

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


def success(data=None, status=200):
    return jsonify({"success": True, "data": data}), status


def error(message, status=400):
    return jsonify({"success": False, "error": message}), status


@chat_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat_endpoint():
    user_id = int(get_jwt_identity())
    body    = request.get_json(silent=True) or {}

    message = (body.get("message") or "").strip()
    history = body.get("history") or []

    if not message:
        return error("message is required")

    if len(message) > 2000:
        return error("Message too long (max 2000 characters)")

    try:
        result = chat(user_id, message, history)
        return success(result)
    except ValueError as e:
        return error(str(e), 503)
    except RuntimeError as e:
        return error(str(e), 500)
