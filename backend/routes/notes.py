"""
routes/notes.py

Thin HTTP layer. Each route:
  1. Extracts data from request
  2. Calls service
  3. Returns JSON response

Zero business logic here — that's intentional.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.note_service import (
    get_all_notes,
    get_note_by_id,
    create_note,
    update_note,
    delete_note,
    toggle_pin,
    get_all_tags,
)

notes_bp = Blueprint("notes", __name__, url_prefix="/api/notes")


def success(data=None, message=None, status=200):
    resp = {"success": True}
    if message:
        resp["message"] = message
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status


def error(message, status=400):
    return jsonify({"success": False, "error": message}), status


@notes_bp.route("", methods=["GET", "POST"])
@jwt_required()
def notes_collection():
    user_id = int(get_jwt_identity())

    if request.method == "GET":
        search = request.args.get("search", "").strip() or None
        tag = request.args.get("tag", "").strip() or None
        notes = get_all_notes(user_id, search=search, tag=tag)
        return success(notes)

    data = request.get_json(silent=True) or {}
    note, err = create_note(user_id, data)
    if err:
        return error(err)
    return success(note, "Note created", 201)


@notes_bp.route("/tags", methods=["GET"])
@jwt_required()
def tags():
    user_id = int(get_jwt_identity())
    return success(get_all_tags(user_id))


@notes_bp.route("/<int:note_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def note_item(note_id):
    user_id = int(get_jwt_identity())

    if request.method == "GET":
        note = get_note_by_id(note_id, user_id)
        if not note:
            return error("Note not found", 404)
        return success(note)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        note, err = update_note(note_id, user_id, data)
        if err:
            return error(err, 404 if "not found" in err else 400)
        return success(note, "Note updated")

    deleted = delete_note(note_id, user_id)
    if not deleted:
        return error("Note not found", 404)
    return success(message="Note deleted")


@notes_bp.route("/<int:note_id>/pin", methods=["PATCH"])
@jwt_required()
def pin_note(note_id):
    user_id = int(get_jwt_identity())
    note, err = toggle_pin(note_id, user_id)
    if err:
        return error(err, 404)
    return success(note, "Pin toggled")
