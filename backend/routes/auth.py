"""
routes/auth.py

WHY a separate auth blueprint?
  Auth concerns (register, login, token refresh) are completely
  separate from notes. Splitting them keeps each file focused
  and makes it easy to swap auth strategies later (OAuth, SSO).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from services.auth_service import register_user, login_user, get_user_by_id

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


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
#  POST /api/auth/register
# ─────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    user, err = register_user(data)
    if err:
        return error(err)
    token = create_access_token(identity=str(user["id"]))
    return success({"user": user, "token": token}, "Registered successfully", 201)


# ─────────────────────────────────────────────
#  POST /api/auth/login
# ─────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user, err = login_user(data)
    if err:
        return error(err, 401)
    token = create_access_token(identity=str(user["id"]))
    return success({"user": user, "token": token}, "Logged in successfully")


# ─────────────────────────────────────────────
#  GET /api/auth/me  → current user profile
# ─────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = get_user_by_id(user_id)
    if not user:
        return error("User not found", 404)
    return success(user)
