from app.models.user import User
from app.database.database import db


def get_all_users():
    return User.query.all()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def create_user(username, email, password):
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        return None
    
    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.session.commit()
    return user


def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False
