from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.services.user_service import *
from app.services.auth_service import *
from pydantic import BaseModel, ValidationError
from app.error import APIError
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


class RegisterSchema(BaseModel):
    email: str
    password: str
    username: str


class LoginSchema(BaseModel):
    email: str
    password: str


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    if user:
        return jsonify({"message": "User found", "username": user.username}), 200
    else:
        return APIError(401, f"Error: User already exists").to_response()


@auth_bp.route("/register", methods=["POST"])
def register_user():
    try:
        data = RegisterSchema(**request.json).model_dump()
        user_exists = User.query.filter_by(email=data["email"]).first()

        if user_exists is not None:
            return APIError(409, "Error: User already exists").to_response()

        new_user = register_data_user(data["email"], data["username"], data["password"])

        return jsonify({"id": new_user.id, "email": new_user.email})
    except ValidationError as error:
        return APIError(400, error.errors()).to_response()


@auth_bp.route("/login", methods=["POST"])
def login_user():
    try:
        data = request.get_json()
        
        if not data or "email" not in data or "password" not in data:
            return APIError(400, "Email and password are required").to_response()
            
        email = data["email"]
        password = data["password"]
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return APIError(401, "This user doesn't exist").to_response()
        
        try:
            if user.password.startswith('$2b$') or user.password.startswith('$2y$'):
                from flask_bcrypt import Bcrypt
                bcrypt = Bcrypt()
                password_correct = bcrypt.check_password_hash(user.password, password)
            else:
                password_correct = check_password_hash(user.password, password)
                
            if not password_correct:
                return APIError(401, "Invalid credentials").to_response()
                
        except ValueError as e:
            print(f"Hash error: {str(e)}")
            if user.password != password:
                return APIError(401, "Invalid credentials").to_response()
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "access_token": access_token
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return APIError(400, f"Error: {str(e)}").to_response()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Successfully logged out"}), 200
