from app.models.accommodation import Accommodation
from app.database.database import db
from werkzeug.exceptions import NotFound, Forbidden

def get_all_accommodations():
    return Accommodation.query.filter_by(status='active').all()

def get_accommodation_by_id(accommodation_id):
    accommodation = Accommodation.query.get(accommodation_id)
    if not accommodation:
        raise NotFound('Accommodation not found')
    return accommodation

def create_accommodation(data, host_id):
    accommodation = Accommodation(
        title=data['title'],
        description=data['description'],
        price_per_month=data['price_per_month'],
        security_deposit=data.get('security_deposit', 0),
        location=data['location'],
        bedrooms=data['bedrooms'],
        bathrooms=data['bathrooms'],
        max_guests=data['max_guests'],
        minimum_stay=data.get('minimum_stay', 1),
        amenities=data.get('amenities', []),
        house_rules=data.get('house_rules'),
        host_id=host_id,
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        image_urls=data.get('image_urls', [])
    )
    
    db.session.add(accommodation)
    db.session.commit()
    return accommodation

def update_accommodation(accommodation_id, data, host_id):
    accommodation = get_accommodation_by_id(accommodation_id)
    
    if accommodation.host_id != host_id:
        raise Forbidden('Not authorized to update this accommodation')
    
    for key, value in data.items():
        setattr(accommodation, key, value)
    
    db.session.commit()
    return accommodation

def delete_accommodation(accommodation_id, host_id):
    accommodation = get_accommodation_by_id(accommodation_id)
    
    if accommodation.host_id != host_id:
        raise Forbidden('Not authorized to delete this accommodation')
    
    db.session.delete(accommodation)
    db.session.commit()

def archive_accommodation(accommodation_id, host_id):
    accommodation = get_accommodation_by_id(accommodation_id)
    
    if accommodation.host_id != host_id:
        raise Forbidden('Not authorized to archive this accommodation')
    
    accommodation.status = 'archived'
    db.session.commit()
    return accommodation 