from app.database.database import db

class Accommodation(db.Model):
    __tablename__ = 'accommodations'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price_per_month = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2), default=0)
    location = db.Column(db.String(200), nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    minimum_stay = db.Column(db.Integer, default=1)
    amenities = db.Column(db.ARRAY(db.String))
    house_rules = db.Column(db.Text)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    status = db.Column(db.String(20), default='active')
    image_urls = db.Column(db.ARRAY(db.String))
    host = db.relationship('User', backref='accommodations')

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price_per_month": float(self.price_per_month) if self.price_per_month else None,
            "security_deposit": float(self.security_deposit) if self.security_deposit else None,
            "location": self.location,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "max_guests": self.max_guests,
            "minimum_stay": self.minimum_stay,
            "amenities": self.amenities,
            "house_rules": self.house_rules,
            "host_id": self.host_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "status": self.status,
            "image_urls": self.image_urls
        } 