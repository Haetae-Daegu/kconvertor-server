from app.api.currency import currency_bp
from app.api.user import user_bp
from app.api.graph import graph_bp
from app.api.auth import auth_bp
from app.api.accommodations import accommodation_bp

from app.error import APIError
from flask import Flask, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from app.database.database import db
from app.security.security import bcrypt, jwt
from dotenv import load_dotenv
from pathlib import Path
from flask_jwt_extended import JWTManager
from .config import config
import os

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


def create_app(config_name=None):
    app = Flask(__name__)

    if not config_name:
        config_name = os.environ.get("FLASK_ENV", "default")

    app.config.from_object(config[config_name])

    if hasattr(config[config_name], "init_app"):
        config[config_name].init_app(app)

    CORS(app)
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)

    SWAGGER_URL = "/apidocs"
    API_URL = "/static/swagger.json"
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "Access API"}
    )
    app.register_blueprint(swagger_ui_blueprint)

    app.register_blueprint(currency_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(accommodation_bp)

    @app.route("/")
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append("%s" % rule)
        return routes

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify({"code": error.code, "message": error.message}), error.code

    return app
