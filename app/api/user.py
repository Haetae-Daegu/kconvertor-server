from flask import Blueprint, jsonify, request
from app.models.user import User
from app.database.database import db
from app.services.user_service import *
from app.error import APIError


user_bp = Blueprint("user", __name__, url_prefix="/users")

@user_bp.route("/", methods=["GET"])
def list_users():
    users = get_all_users()
    return jsonify([user.to_dict() for user in users]), 200

@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return APIError(404, f"Error: User not found").to_response()
    return jsonify({"id": user.id, "username": user.username}), 200

@user_bp.route("/", methods=["POST"])
def add_user():
    data = request.get_json()
    if not data or "username" not in data or "email" not in data or "password" not in data:
        return APIError(400, f"Error: Invalid data").to_response()
    user = create_user(data["username"], data["email"], data["password"])
    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 201

@user_bp.route("/<int:user_id>", methods=["PUT"])
def modify_user(user_id):
    data = request.get_json()
    if not data:
        return APIError(400, f"Error: Invalid data").to_response()
    user = update_user(user_id, data["username"], data["email"], data["password"])
    if not user:
        return APIError(404, f"Error: User not found").to_response()
    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200

@user_bp.route("/<int:user_id>", methods=["DELETE"])
def remove_user(user_id):
    if delete_user(user_id):
        return jsonify({"message": "User deleted"}), 200
    return APIError(404, f"Error: User not found").to_response()
