from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # OAuth client ID (type "Web application") used to check the audience of
    # Google ID tokens. Google sign-in is refused while it is not set.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


class TestingConfig(Config):
    TESTING = True
    # A dedicated Postgres DB (the models use ARRAY, which SQLite lacks).
    # Tables are dropped after each test: never point this at a real database.
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    JWT_SECRET_KEY = "test_secret_key"
    GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        assert os.environ.get("SECRET_KEY")
        assert os.environ.get("DATABASE_URL")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
