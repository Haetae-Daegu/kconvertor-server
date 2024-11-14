import os

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from app.api.api import *

SWAGGER_URL = "/apidocs"
API_URL = "/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Access API"}
)


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    app.register_blueprint(swagger_ui_blueprint)
    app.register_blueprint(api_bp)

    @app.route("/")
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append("%s" % rule)
        return routes

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return error.to_response()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
