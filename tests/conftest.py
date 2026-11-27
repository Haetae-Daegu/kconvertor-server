import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.database.database import db as _db
from app.models.user import User
from app.models.accommodation import Accommodation
from flask_jwt_extended import create_access_token


@pytest.fixture
def app():
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.fail(
            "TEST_DATABASE_URL is not set (Postgres test DB, see docs/RUNBOOK.md)"
        )

    app = create_app("testing")

    with app.app_context():
        _db.create_all()

        yield app

        _db.session.remove()
        _db.drop_all()


@pytest.fixture(autouse=True)
def fake_geocoding(monkeypatch):
    """Never call the Google Geocoding API from tests."""

    def set_coordinates(accommodation):
        accommodation.latitude = 35.8562
        accommodation.longitude = 128.4896

    monkeypatch.setattr(
        "app.services.accommodation_service.set_coordinates", set_coordinates
    )


@pytest.fixture
def client(app):
    """Client de test pour faire des requêtes à l'application."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Session de base de données pour les tests."""
    with app.app_context():
        yield _db


@pytest.fixture
def test_user(db):
    """Créer un utilisateur de test."""
    user = User(username="testuser", email="test@example.com")
    if hasattr(user, "set_password"):
        user.set_password("password123")
    else:
        user.password = "password123"
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_admin(db):
    """Créer un administrateur de test."""
    admin = User(username="admin", email="admin@example.com", role="admin")

    if hasattr(admin, "set_password"):
        admin.set_password("admin123")
    else:
        admin.password = "admin123"

    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def other_user(db):
    """A regular user who does not own test_accommodation."""
    user = User(username="otheruser", email="other@example.com", password="x")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_accommodation(db, test_user):
    """Créer une accommodation de test."""
    accommodation = Accommodation(
        title="Test Accommodation",
        description="A test accommodation",
        location="123 Test Street, Test City, Test Country",
        price_per_month=1000.0,
        bedrooms=2,
        bathrooms=1,
        max_guests=4,
        host_id=test_user.id,
        image_urls=["http://example.com/image1.jpg"],
    )
    db.session.add(accommodation)
    db.session.commit()
    return accommodation


@pytest.fixture
def user_token(test_user):
    return create_access_token(identity=str(test_user.id))


@pytest.fixture
def other_token(other_user):
    return create_access_token(identity=str(other_user.id))


@pytest.fixture
def admin_token(test_admin):
    return create_access_token(identity=str(test_admin.id))
