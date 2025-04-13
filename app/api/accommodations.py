from flask import Blueprint, jsonify, request
from app.services.accommodation_service import *
from app.services.alert_service import AlertType, send_alert
from app.services.user_service import *
from app.error import APIError
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from pydantic import ValidationError
from dotenv import load_dotenv
import json
from app.services.storage_factory import StorageFactory, StorageType
from pathlib import Path
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

client_url = os.getenv("CLIENT_URL")
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

accommodation_bp = Blueprint("accommodations", __name__, url_prefix="/accommodations")


@accommodation_bp.route("/", methods=["GET"])
def get_list_accommodations():
    accommodations = get_all_accommodations()
    return jsonify([accommodation.to_dict() for accommodation in accommodations]), 200


@accommodation_bp.route("/user", methods=["GET"])
@jwt_required()
def get_list_accommodations_by_user():
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        if not user:
            send_alert("Get Accommodations", f"Error: User not found", AlertType.INFO)
            return APIError(404, "Not authorized").to_response()
        accommodations = get_all_accommodations_by_user(user_id)
        return (
            jsonify([accommodation.to_dict() for accommodation in accommodations]),
            200,
        )
    except Exception as e:
        send_alert("Get Accommodations", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()


@accommodation_bp.route("/<int:id>", methods=["GET"])
def get_accommodation(id):
    try:
        accommodation = get_accommodation_by_id(id)
        return jsonify(accommodation.to_dict()), 200
    except:
        send_alert(
            "Get Accommodation", f"Error: Accommodation not found", AlertType.INFO
        )
        return APIError(404, f"Error: Accommodation not found").to_response()


@accommodation_bp.route("/", methods=["POST"])
@jwt_required()
def create_new_accommodation():
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)

        if not user:
            send_alert("Create Accommodation", f"Error: Not authorized", AlertType.INFO)
            return APIError(404, "Not authorized").to_response()

        files = request.files.getlist("images[]")
        if not files or all(not file.filename for file in files):
            send_alert(
                "Create Accommodation", f"Error: No images selected", AlertType.INFO
            )
            return APIError(400, "Error: No images selected").to_response()

        storage_service = StorageFactory.get_storage_service(StorageType.S3)
        image_urls = storage_service.upload_files(files)

        data = json.loads(request.form["data"])
        data["image_urls"] = image_urls
        data["host_id"] = user_id

        accommodation_data = AccommodationCreate(**data)
        accommodation = create_accommodation(
            accommodation_data.model_dump(exclude_unset=True),
        )

        accommodation_dict = accommodation.to_dict()
        send_alert(
            "Accommodation",
            f"New accommodation created: [{accommodation.id}, {accommodation.title}] by {user.username} \n {client_url}/accommodation/{accommodation.id}",
            AlertType.SUCCESS,
        )

        return jsonify(accommodation_dict), 201

    except Exception as e:
        send_alert("Create Accommodation", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()


@accommodation_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def modify_accommodation(id):
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)

        if not user:
            send_alert("Modify Accommodation", f"Error: Not authorized", AlertType.INFO)
            return APIError(404, "Not authorized").to_response()

        data = request.get_json()
        if not data:
            send_alert("Modify Accommodation", f"Error: Invalid data", AlertType.INFO)
            return APIError(400, "Error: Invalid data").to_response()

        accommodation_data = AccommodationUpdate(**data)
        accommodation = update_accommodation(
            id, accommodation_data.model_dump(exclude_unset=True), user.id
        )
        send_alert(
            "Accommodation",
            f"Accommodation [{accommodation.id}, {accommodation.title}] updated by {user.username} \n {client_url}/accommodation/{accommodation.id}",
            AlertType.SUCCESS,
        )

        return jsonify(accommodation.to_dict()), 200
    except ValidationError as e:
        send_alert("Modify Accommodation", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()
    except Exception as e:
        if "not found" in str(e).lower():
            send_alert(
                "Modify Accommodation",
                f"Error: Accommodation not found",
                AlertType.ERROR,
            )
            return APIError(404, f"Error: Accommodation not found").to_response()
        send_alert("Modify Accommodation", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()


@accommodation_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def remove_accommodation(id):
    try:
        current_user_id = get_jwt_identity()
        current_user = get_user_by_id(current_user_id)

        if not current_user and current_user.role != "admin":
            send_alert("Delete Accommodation", f"Error: Not authorized", AlertType.INFO)
            return APIError(404, "Not authorized").to_response()

        send_alert(
            "Accommodation",
            f"Accommodation {id} deleted by {current_user.username}",
            AlertType.INFO,
        )
        delete_accommodation(id, current_user.id)
        return jsonify({"message": "Accommodation deleted"}), 200
    except Exception as e:
        if "not found" in str(e).lower():
            send_alert(
                "Delete Accommodation",
                f"Error: Accommodation not found",
                AlertType.INFO,
            )
            return APIError(404, f"Error: Accommodation not found").to_response()
        send_alert("Delete Accommodation", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()


@accommodation_bp.route("/<int:id>/archive", methods=["POST"])
@jwt_required()
def archive_accommodation(id):
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)

        if not user:
            return APIError(404, "Not authorized").to_response()
        accommodation = archive_accommodation(id, user_id)
        return jsonify(accommodation.to_dict()), 200
    except Exception as e:
        if "not found" in str(e).lower():
            return APIError(404, f"Error: Accommodation not found").to_response()
        return APIError(400, f"Error: {str(e)}").to_response()
