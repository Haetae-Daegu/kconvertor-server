from flask import Blueprint, jsonify, request
from app.services.alert_service import AlertType, send_alert
from app.services.user_service import *
from app.error import APIError
from app.schemas.user import UserCreate, UserUpdate
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.security.security import role_required

user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(["admin"])
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
@jwt_required()
def modify_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = get_user_by_id(current_user_id)
    
    if not current_user:
        send_alert("Modify User", f"Error: User not found", AlertType.INFO)
        return APIError(404, f"Error: User not found").to_response()
    
    if current_user.role != "admin" and int(current_user_id) != user_id:
        send_alert("Modify User", f"Error: Insufficient permissions", AlertType.ERROR)
        return APIError(403, f"Error: Insufficient permissions").to_response()

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
        send_alert("Modify User", f"User {user.username} | {user.id} updated", AlertType.SUCCESS)
        return (
            jsonify({"id": user.id, "username": user.username, "email": user.email}),
            200,
        )
    except ValidationError as e:
        send_alert("Modify User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()
    except Exception as e:
        send_alert("Modify User", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = get_user_by_id(current_user_id)
    
    if not current_user:
        send_alert("Remove User", f"Error: User not found", AlertType.INFO)
        return APIError(404, f"Error: User not found").to_response()
        
    if current_user.role != "admin" and current_user_id != user_id:
        send_alert("Remove User", f"Error: Insufficient permissions", AlertType.ERROR)
        return APIError(403, f"Error: Insufficient permissions").to_response()
    
    user = get_user_by_id(user_id)
    if not user:
        send_alert("Remove User", f"Error: User not found", AlertType.INFO)
        return APIError(404, f"Error: User not found").to_response()
        
    delete_user(user_id)
    send_alert("Remove User", f"User {user.username} | {user.id} deleted", AlertType.SUCCESS)
    return jsonify({"message": "User deleted successfully"}), 200
