from api.currency import *

from flask import Flask, request, jsonify

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    @app.route('/')
    def hello():
        return 'Hello, World!'
    
    @app.route('/currency')
    def json_currency():
        country = os.environ.get("COUNTRY")
        return exchange_rate(country)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
    print("Launching app")