from app.api.currency import currency_bp
from app.api.user import user_bp
from app.api.graph import graph_bp
from app.api.auth import auth_bp
from app.error import APIError
from flask import Flask, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from app.database.database import db
from app.security.security import bcrypt, jwt

import os


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
        JWT_TOKEN_LOCATION=['headers'],
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL')
    )

    CORS(app)
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

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
