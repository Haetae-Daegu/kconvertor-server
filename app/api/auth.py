from flask import Blueprint, jsonify, request, session
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.database.database import db
from app.services.user_service import *
from app.security.security import bcrypt, jwt
from app.error import APIError

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/me", methods=['GET'])
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
    email = request.json["email"]
    username = request.json["username"]
    password = request.json["password"]

    user_exists = User.query.filter_by(email=email).first()
    if user_exists is not None:
        return APIError(409, f"Error: User already exists").to_response()
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
    new_user = User(email=email, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    session["user_id"] = new_user.id
    return jsonify({"id": new_user.id, "email": new_user.email})

@auth_bp.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'message': 'Login Success', 'access_token': access_token}), 200
    else:
        return APIError(401, f"Error: Incorrect informations").to_response()
