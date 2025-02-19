import requests
from geopy import distance
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

YANDEX_GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"

def get_coordinates(address):
    cached = cache.get(f"geocode_{address}")
    if cached:
        return cached

    try:
        response = requests.get(YANDEX_GEOCODER_URL, params={
            "apikey": settings.YANDEX_GEOCODER_API_KEY,
            "format": "json",
            "geocode": address
        }, timeout=5)
        response.raise_for_status()
        data = response.json()

        feature = data['response']['GeoObjectCollection']['featureMember'][0]
        pos = feature['GeoObject']['Point']['pos']
        lon, lat = map(float, pos.split())
        cache.set(f"geocode_{address}", (lat, lon), 3600*24)
        return (lat, lon)

    except Exception as e:
        logger.error(f"Geocoding error for {address}: {str(e)}")
        return None

def calculate_distance(point_a, point_b):
    if not point_a or not point_b:
        return None
    try:
        return round(distance.distance(point_a, point_b).km, 1)
    except Exception as e:
        logger.error(f"Distance calculation error: {str(e)}")
        return None
