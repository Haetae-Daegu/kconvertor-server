from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, get_jwt_identity
from functools import wraps
from app.services.user_service import get_user_by_id
from app.error import APIError

jwt = JWTManager()
bcrypt = Bcrypt()


def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = get_user_by_id(current_user_id)

            if not user:
                raise APIError(404, "User not found")

            if user.role not in roles:
                raise APIError(403, "Insufficient permissions")

            return fn(*args, **kwargs)

        return decorator

    return wrapper
