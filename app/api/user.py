from flask import Blueprint, jsonify, request
from app.services.user_service import *
from app.error import APIError
from app.schemas.user import UserCreate, UserUpdate
from pydantic import ValidationError


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
    try:
        data = request.get_json()
        if not data:
            return APIError(400, "Error: Invalid data").to_response()

        user_data = UserCreate(**data)
        
        user = create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        return jsonify({"id": user.id, "username": user.username, "email": user.email}), 201
    except ValidationError as e:
        return APIError(400, f"Error: {str(e)}").to_response()
    except Exception as e:
        return APIError(400, f"Error: {str(e)}").to_response()

@user_bp.route("/<int:user_id>", methods=["PUT"])
def modify_user(user_id):
    try:
        data = request.get_json()
        if not data:
            return APIError(400, "Error: Invalid data").to_response()

        user_data = UserUpdate(**data)
        
        user = update_user(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        if not user:
            return APIError(404, f"Error: User not found").to_response()
        return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200
    except ValidationError as e:
        return APIError(400, f"Error: {str(e)}").to_response()
    except Exception as e:
        return APIError(400, f"Error: {str(e)}").to_response()

@user_bp.route("/<int:user_id>", methods=["DELETE"])
def remove_user(user_id):
    if delete_user(user_id):
        return jsonify({"message": "User deleted"}), 200
    return APIError(404, f"Error: User not found").to_response()
