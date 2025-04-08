from flask import Blueprint, jsonify, request
from app.services.alert_service import AlertType, send_alert
from app.services.user_service import *
from app.error import APIError
from app.schemas.user import UserCreate, UserUpdate
from pydantic import ValidationError
from flask_jwt_extended import jwt_required

user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    try:
        users = get_all_users()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return APIError(400, f"Error: {str(e)}").to_response()


@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        send_alert("Get User", f"Error: User not found", AlertType.ERROR)
        return APIError(404, f"Error: User not found").to_response()
    return jsonify(user.to_dict()), 200


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
            password=user_data.password,
        )
        return (
            jsonify({"id": user.id, "username": user.username, "email": user.email}),
            201,
        )
    except ValidationError as e:
        send_alert("Create User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()
    except Exception as e:
        send_alert("Create User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()


@user_bp.route("/<int:user_id>", methods=["PUT"])
def modify_user(user_id):
    try:
        data = request.get_json()
        if not data:
            return APIError(400, "Error: Invalid data").to_response()

        user_data = UserUpdate(**data)

        update_data = user_data.model_dump(exclude_unset=True)

        user = update_user(user_id=user_id, data=update_data)

        if not user:
            send_alert("Modify User", f"Error: User not found", AlertType.ERROR)
            return APIError(404, f"Error: User not found").to_response()
        return (
            jsonify({"id": user.id, "username": user.username, "email": user.email}),
            200,
        )
    except ValidationError as e:
        send_alert("Modify User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()
    except Exception as e:
        send_alert("Modify User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_user(user_id):
    try:
        if delete_user(user_id):
            send_alert("Delete User", f"User {user_id} deleted", AlertType.INFO)
            return jsonify({"message": "User deleted"}), 200
        send_alert("Delete User", f"Error: User not found", AlertType.ERROR)
        return APIError(404, f"Error: User not found").to_response()
    except Exception as e:
        send_alert("Delete User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()
