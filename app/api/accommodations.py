from flask import Blueprint, jsonify, request
from app.services.accommodation_service import *
from app.error import APIError
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from pydantic import ValidationError

accommodation_bp = Blueprint('accommodations', __name__, url_prefix='/accommodations')

@accommodation_bp.route('/', methods=['GET'])
def get_list_accommodations():
    accommodations = get_all_accommodations()
    return jsonify([accommodation.to_dict() for accommodation in accommodations]), 200

@accommodation_bp.route('/<int:id>', methods=['GET'])
def get_accommodation(id):
    try:
        accommodation = get_accommodation_by_id(id)
        return jsonify(accommodation.to_dict()), 200
    except:
        return APIError(404, f"Error: Accommodation not found").to_response()

@accommodation_bp.route('/', methods=['POST'])
def create_accommodation():
    try:
        data = request.get_json()
        if not data:
            return APIError(400, "Error: Invalid data").to_response()

        accommodation_data = AccommodationCreate(**data)
        
        accommodation = create_accommodation(accommodation_data.dict(), 1)  # hardcoded user_id
        return jsonify(accommodation.to_dict()), 201
    except ValidationError as e:
        return APIError(400, f"Error: {str(e)}").to_response()
    except Exception as e:
        return APIError(400, f"Error: {str(e)}").to_response()

@accommodation_bp.route('/<int:id>', methods=['PUT'])
def update_accommodation(id):
    try:
        data = request.get_json()
        if not data:
            return APIError(400, "Error: Invalid data").to_response()

        accommodation_data = AccommodationUpdate(**data)
        
        accommodation = update_accommodation(id, accommodation_data.dict(exclude_unset=True), 1)
        return jsonify(accommodation.to_dict()), 200
    except ValidationError as e:
        return APIError(400, f"Error: {str(e)}").to_response()
    except Exception as e:
        if "not found" in str(e).lower():
            return APIError(404, f"Error: Accommodation not found").to_response()
        return APIError(400, f"Error: {str(e)}").to_response()

@accommodation_bp.route('/<int:id>', methods=['DELETE'])
def remove_accommodation(id):
    try:
        delete_accommodation(id, 1)  
        return jsonify({"message": "Accommodation deleted"}), 200
    except Exception as e:
        if "not found" in str(e).lower():
            return APIError(404, f"Error: Accommodation not found").to_response()
        return APIError(400, f"Error: {str(e)}").to_response()

@accommodation_bp.route('/<int:id>/archive', methods=['POST'])
def archive_accommodation(id):
    try:
        accommodation = archive_accommodation(id, 1)
        return jsonify(accommodation.to_dict()), 200
    except Exception as e:
        if "not found" in str(e).lower():
            return APIError(404, f"Error: Accommodation not found").to_response()
        return APIError(400, f"Error: {str(e)}").to_response() 