"""
routes/graph.py

GET /api/graph  →  {nodes, links, stats}
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.graph_service import build_graph

graph_bp = Blueprint("graph", __name__, url_prefix="/api")


@graph_bp.route("/graph", methods=["GET"])
@jwt_required()
def get_graph():
    user_id = int(get_jwt_identity())
    data = build_graph(user_id)
    return jsonify({"success": True, "data": data})
