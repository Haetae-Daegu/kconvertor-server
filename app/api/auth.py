from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.services.user_service import *
from app.services.auth_service import *
from pydantic import BaseModel, ValidationError
from app.error import APIError

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
        data = LoginSchema(**request.json).model_dump()
        user = User.query.filter_by(email=data["email"]).first()

        if user and bcrypt.check_password_hash(user.password, data["password"]):
            access_token = create_access_token(identity=user.id)
            return (
                jsonify({"message": "Login Success", "access_token": access_token}),
                200,
            )
        else:
            return APIError(401, f"Error: Incorrect information").to_response()
    except ValidationError as error:
        return APIError(400, error.errors()).to_response()


# TODO Implementing logout when the main feature will be finished
##Blacklist the token by creating a table in DB and storing that token then checking if this token is in there
# @auth_bp.route("/logout", methods=["POST"])
# def logout():
