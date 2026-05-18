"""
routes/ai.py

WHY a separate AI blueprint?
  AI routes have different characteristics — they're slow (network calls),
  expensive (token cost), and will grow significantly (search, chat, graph).
  Keeping them separate makes rate-limiting and monitoring easier later.
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ai_service import generate_summary, clear_summary

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


def success(data=None, message=None, status=200):
    resp = {"success": True}
    if message:
        resp["message"] = message
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status


def error(message, status=400):
    return jsonify({"success": False, "error": message}), status


# ─────────────────────────────────────────────
#  POST /api/ai/notes/<id>/summarize
# ─────────────────────────────────────────────
@ai_bp.route("/notes/<int:note_id>/summarize", methods=["POST"])
@jwt_required()
def summarize(note_id):
    user_id = int(get_jwt_identity())
    summary, err = generate_summary(note_id, user_id)
    if err:
        return error(err)
    return success({"summary": summary}, "Summary generated")


# ─────────────────────────────────────────────
#  DELETE /api/ai/notes/<id>/summarize
# ─────────────────────────────────────────────
@ai_bp.route("/notes/<int:note_id>/summarize", methods=["DELETE"])
@jwt_required()
def delete_summary(note_id):
    user_id = int(get_jwt_identity())
    ok, err = clear_summary(note_id, user_id)
    if err:
        return error(err, 404)
    return success(message="Summary cleared")
