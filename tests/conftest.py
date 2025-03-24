import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database.database import db as _db
from app.models.user import User
from app.models.accommodation import Accommodation
import tempfile
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test_secret_key'
    
    with app.app_context():
        _db.create_all()
        
        yield app
        
        _db.session.remove()
        _db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

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
    if hasattr(user, 'set_password'):
        user.set_password("password123")
    else:
        user.password = "password123"
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_admin(db):
    """Créer un administrateur de test."""
    admin = User(username="admin", email="admin@example.com")
    if hasattr(User, 'is_admin'):
        admin.is_admin = True
    
    if hasattr(admin, 'set_password'):
        admin.set_password("admin123")
    else:
        admin.password = "admin123"
    
    db.session.add(admin)
    db.session.commit()
    return admin

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
        image_urls=["http://example.com/image1.jpg"]
    )
    db.session.add(accommodation)
    db.session.commit()
    return accommodation

@pytest.fixture
def user_token(test_user):
    return create_access_token(identity=test_user.id)

@pytest.fixture
def admin_token(test_admin):
    return create_access_token(identity=test_admin.id) 