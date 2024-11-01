from app.api.api import *
from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL="/swagger"
#Note: We can't provide any custom file path for swagger.json
API_URL="/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Access API'
    }
)

def create_app():
    #config
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    
    #register blueprint
    app.register_blueprint(api_bp)
    # app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    #routes

    @app.route("/")
    def spec():
        return "Hello"

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
    print("Launching app")