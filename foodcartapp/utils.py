import logging
from geopy import distance
import requests
from geocoder.models import AddressCoordinates

logger = logging.getLogger(__name__)
from django.utils import timezone


def get_coordinates(address):
    response = requests.get(f"http://api.example.com/geocode?address={address}")
    data = response.json()

    if not data or "response" not in data:
        return None
    try:
        pos = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"][
            "Point"
        ]["pos"]
        longitude, latitude = map(float, pos.split())

        AddressCoordinates.objects.update_or_create(
            address=address,
            defaults={
                "latitude": latitude,
                "longitude": longitude,
                "updated_at": timezone.now(),
            },
        )
        return (latitude, longitude)
    except (IndexError, KeyError, ValueError):

        return None


def calculate_distance(point_a, point_b):
    if not point_a or not point_b:
        return None
    try:
        if not (isinstance(point_a, tuple) and isinstance(point_b, tuple)):
            logger.error("Invalid points provided for distance calculation.")
            return None
        return round(distance.distance(point_a, point_b).km, 1)
    except Exception as e:
        logger.error(f"Distance calculation error: {str(e)}")
        return None
