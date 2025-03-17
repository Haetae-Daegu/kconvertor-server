from app.models.user import User
from app.services.user_service import *
from app.database.database import db
from app.security.security import bcrypt


def register_data_user(email: str, username: str, password: str):
    hashed_password = bcrypt.generate_password_hash(password).decode("utf8")
    new_user = User(email=email, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return new_user
