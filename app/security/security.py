from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

jwt = JWTManager()
bcrypt = Bcrypt()