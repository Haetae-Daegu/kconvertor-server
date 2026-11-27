from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
)
from app.services.user_service import *
from app.services.auth_service import *
from app.services.alert_service import AlertType, send_alert
from pydantic import BaseModel, ValidationError
from app.error import APIError
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


def _login_payload(user):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "access_token": create_access_token(identity=str(user.id)),
        "refresh_token": create_refresh_token(identity=str(user.id)),
    }


@auth_bp.route("/me", methods=["GET"])
def get_me():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()

        user = User.query.filter_by(id=int(user_id)).first()

        if user:
            return jsonify(user.to_private_dict()), 200
        else:
            return APIError(404, "User not found").to_response()
    except JWTExtendedException as jwt_error:
        send_alert("JWT error", f"Error: {str(jwt_error)}", AlertType.ERROR)
        return APIError(401, f"JWT error: {str(jwt_error)}").to_response()
    except PyJWTError as pyjwt_error:
        send_alert("JWT error", f"Error: {str(pyjwt_error)}", AlertType.ERROR)
        return APIError(401, f"Token error: {str(pyjwt_error)}").to_response()
    except Exception as e:
        send_alert("JWT error", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(500, f"Internal server error: {str(e)}").to_response()


@auth_bp.route("/register", methods=["POST"])
def register_user():
    try:
        data = RegisterSchema(**request.json).model_dump()
        user_exists = User.query.filter_by(email=data["email"]).first()

        if user_exists is not None:
            send_alert("Registration", f"Error: User already exists", AlertType.INFO)
            return APIError(409, "Error: User already exists").to_response()

        new_user = register_data_user(data["email"], data["username"], data["password"])
        send_alert(
            "Registration",
            f"New user registered: {new_user.email} | {new_user.username}",
            AlertType.INFO,
        )

        return jsonify({"id": new_user.id, "email": new_user.email})
    except ValidationError as error:
        send_alert("Registration", f"Error: {error.errors()}", AlertType.ERROR)
        return APIError(400, error.errors()).to_response()
    except Exception as e:
        send_alert("Registration", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()


@auth_bp.route("/login", methods=["POST"])
def login_user():
    try:
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            send_alert(
                "Login", f"Error: Email and password are required", AlertType.INFO
            )
            return APIError(400, "Email and password are required").to_response()

        email = data["email"]
        password = data["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            send_alert("Login", f"Error: This user doesn't exist", AlertType.INFO)
            return APIError(401, "This user doesn't exist").to_response()

        if user.password is None:
            send_alert("Login", f"Error: Google-only account", AlertType.INFO)
            return APIError(400, "This account uses Google sign-in").to_response()

        if not check_user_password(user, password):
            send_alert("Login", f"Error: Invalid credentials", AlertType.INFO)
            return APIError(401, "Invalid credentials").to_response()

        return jsonify(_login_payload(user)), 200

    except Exception as e:
        send_alert("Login", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error on server").to_response()


@auth_bp.route("/google", methods=["POST"])
def google_login():
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        send_alert(
            "Google sign-in", "Error: GOOGLE_CLIENT_ID is not set", AlertType.ERROR
        )
        return APIError(503, "Google sign-in is not configured").to_response()

    data = request.get_json(silent=True) or {}
    credential = data.get("credential")
    if not credential or not isinstance(credential, str):
        return APIError(400, "credential is required").to_response()

    try:
        idinfo = verify_google_token(credential, client_id)
    except GoogleAuthError as error:
        send_alert("Google sign-in", f"Error: {error}", AlertType.INFO)
        return APIError(401, "Invalid Google token").to_response()
    except GoogleUnavailableError as error:
        send_alert("Google sign-in", f"Error: {error}", AlertType.ERROR)
        return APIError(503, "Google is unreachable, try again later").to_response()

    try:
        user, created = google_sign_in(idinfo)
    except GoogleAccountConflictError as error:
        send_alert("Google sign-in", f"Error: {error}", AlertType.INFO)
        return APIError(409, str(error)).to_response()
    except Exception as e:
        send_alert("Google sign-in", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(500, "Error on server").to_response()

    if created:
        send_alert(
            "Registration",
            f"New user registered with Google: {user.email} | {user.username}",
            AlertType.INFO,
        )

    return jsonify(_login_payload(user)), 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Exchange a refresh token for new tokens.

    The refresh token is read from the JSON body ("refresh_token", what the
    frontend sends) or from the Authorization header.
    """
    try:
        verify_jwt_in_request(refresh=True, locations=["json", "headers"])
    except (JWTExtendedException, PyJWTError) as error:
        return APIError(401, f"Invalid refresh token: {error}").to_response()

    try:
        user = User.query.filter_by(id=int(get_jwt_identity())).first()

        if not user:
            send_alert("Refresh token", f"Error: Invalid credentials", AlertType.INFO)
            return APIError(401, "Invalid credentials").to_response()

        return (
            jsonify(
                {
                    "access_token": create_access_token(
                        identity=str(user.id), fresh=False
                    ),
                    "refresh_token": create_refresh_token(identity=str(user.id)),
                }
            ),
            200,
        )
    except Exception as e:
        send_alert("Refresh token", f"Error: {str(e)}", AlertType.ERROR)
        return APIError(400, f"Error: {str(e)}").to_response()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Successfully logged out"}), 200
