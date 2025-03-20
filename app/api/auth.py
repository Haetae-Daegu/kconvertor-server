from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, verify_jwt_in_request
from app.services.user_service import *
from app.services.auth_service import *
from pydantic import BaseModel, ValidationError
from app.error import APIError
from werkzeug.security import check_password_hash
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


class RegisterSchema(BaseModel):
    email: str
    password: str
    username: str


class LoginSchema(BaseModel):
    email: str
    password: str


@auth_bp.route("/me", methods=["GET"])
def get_me():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = User.query.filter_by(id=int(user_id)).first()

        if user:
            return jsonify({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            }), 200
        else:
            return APIError(404, "User not found").to_response()
    except JWTExtendedException as jwt_error:
        print(f"Erreur JWT: {str(jwt_error)}")
        return APIError(401, f"JWT error: {str(jwt_error)}").to_response()
    except PyJWTError as pyjwt_error:
        print(f"Erreur PyJWT: {str(pyjwt_error)}")
        return APIError(401, f"Token error: {str(pyjwt_error)}").to_response()
    except Exception as e:
        print(f"Error in /auth/me endpoint: {str(e)}")
        return APIError(500, f"Internal server error: {str(e)}").to_response()


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
        
        access_token = create_access_token(identity=str(user.id))
        
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
