from app.models.accommodation import Accommodation
from app.database.database import db
from werkzeug.exceptions import NotFound, Forbidden
import requests
import os
from app.services.alert_service import AlertType, send_alert
from app.services.storage_factory import StorageFactory, StorageType

google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")


def get_all_accommodations():
    return Accommodation.query.filter_by(status="active").all()


def get_all_accommodations_by_user(user_id):
    return Accommodation.query.filter_by(host_id=user_id).all()


def is_accommodation_by_user(accommodation_id, user):
    accommodation = Accommodation.query.get(accommodation_id)
    if not accommodation:
        raise NotFound("Accommodation not found")
    if accommodation.host_id != user.id and user.role != "admin":
        return False
    return True


def get_accommodation_by_id(accommodation_id):
    accommodation = Accommodation.query.get(accommodation_id)
    if not accommodation:
        raise NotFound("Accommodation not found")
    return accommodation


def create_accommodation(data):
    accommodation = Accommodation(
        title=data["title"],
        description=data["description"],
        price_per_month=data["price_per_month"],
        security_deposit=data.get("security_deposit", 0),
        location=data["location"],
        bedrooms=data["bedrooms"],
        bathrooms=data["bathrooms"],
        max_guests=data["max_guests"],
        minimum_stay=data.get("minimum_stay", 1),
        amenities=data.get("amenities", []),
        house_rules=data.get("house_rules"),
        host_id=data["host_id"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        image_urls=data.get("image_urls", []),
    )

    try:
        set_coordinates(accommodation)
    except ValueError as e:
        print(e)
        raise e

    db.session.add(accommodation)
    db.session.commit()
    return accommodation


def update_accommodation(accommodation_id, data, user_id):
    accommodation = get_accommodation_by_id(accommodation_id)
    if accommodation.host_id != user_id:
        raise Forbidden("Not authorized to update this accommodation")

    for key, value in data.items():
        setattr(accommodation, key, value)

    set_coordinates(accommodation)
    db.session.commit()
    return accommodation


def update_accommodation_status(accommodation_id, data, user):

    accommodation = get_accommodation_by_id(accommodation_id)
    if not is_accommodation_by_user(accommodation_id, user):
        raise Forbidden("Not authorized to update this accommodation")
    accommodation.status = data["status"]
    db.session.commit()
    return accommodation


def delete_accommodation(accommodation_id, host_id):
    accommodation = get_accommodation_by_id(accommodation_id)

    if accommodation.host_id != host_id:
        raise Forbidden("Not authorized to delete this accommodation")

    db.session.delete(accommodation)
    db.session.commit()


def archive_accommodation(accommodation_id, host_id):
    accommodation = get_accommodation_by_id(accommodation_id)

    if accommodation.host_id != host_id:
        raise Forbidden("Not authorized to archive this accommodation")

    accommodation.status = "archived"
    db.session.commit()
    return accommodation


def set_coordinates(accommodation):
    location = accommodation.location
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={google_maps_api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            accommodation.longitude = data["results"][0]["geometry"]["location"]["lng"]
            accommodation.latitude = data["results"][0]["geometry"]["location"]["lat"]
            print(
                f"Coordinates updated: {accommodation.latitude}, {accommodation.longitude}"
            )
        else:
            raise ValueError(
                f'Address not found: {location}. Error status: {data["status"]}'
            )
    except Exception as e:
        print(f"Error calling API: {e}")
        raise


def update_accommodation_with_images(accommodation_id, data, files, user_id):
    accommodation = get_accommodation_by_id(accommodation_id)

    if accommodation.host_id != user_id:
        send_alert(
            "Update Accommodation",
            f"Not authorized to update this accommodation",
            AlertType.INFO,
        )
        raise Forbidden("Not authorized to update this accommodation")

    if files and any(file.filename for file in files):
        storage_service = StorageFactory.get_storage_service(StorageType.S3)
        new_image_urls = storage_service.upload_files(files)

        if "image_urls" in data:
            data["image_urls"] = data["image_urls"] + new_image_urls
            send_alert(
                "Update Accommodation",
                f"list of images: {new_image_urls}",
                AlertType.INFO,
            )

    for key, value in data.items():
        setattr(accommodation, key, value)

    set_coordinates(accommodation)
    db.session.commit()
    return accommodation


def create_accommodation_with_images(data, files, user_id):
    if not files or not any(file.filename for file in files):
        send_alert("Create Accommodation", f"Error: No images selected", AlertType.INFO)
        raise ValueError("No images selected")

    storage_service = StorageFactory.get_storage_service(StorageType.S3)
    image_urls = storage_service.upload_files(files)

    data["image_urls"] = image_urls
    data["host_id"] = user_id

    accommodation = create_accommodation(data)

    send_alert(
        "Create Accommodation",
        f"New accommodation created with {len(image_urls)} images",
        AlertType.INFO,
    )

    return accommodation
