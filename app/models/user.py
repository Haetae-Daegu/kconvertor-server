from app.database.database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # NULL for accounts created with Google sign-in that never set a password.
    password = db.Column(db.String(128), nullable=True)
    google_sub = db.Column(db.String(255), unique=True, nullable=True)
    auth_provider = db.Column(db.String(20), default="local", server_default="local")
    avatar_url = db.Column(db.String(500), nullable=True)
    discord_username = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    instagram_username = db.Column(db.String(100), nullable=True)
    kakaotalk_id = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "discord_username": self.discord_username,
            "phone_number": self.phone_number,
            "instagram_username": self.instagram_username,
            "kakaotalk_id": self.kakaotalk_id,
            "role": self.role,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_private_dict(self):
        """to_dict plus fields only the user themself should see."""
        return {
            **self.to_dict(),
            "auth_provider": self.auth_provider,
            "has_password": self.password is not None,
        }
