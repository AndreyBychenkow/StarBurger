import logging
from geopy import distance

logger = logging.getLogger(__name__)


def calculate_distance(point_a, point_b):
    if not point_a or not point_b:
        return None
    try:
        return round(distance.distance(point_a, point_b).km, 1)
    except Exception as e:
        logger.error(f"Distance calculation error: {str(e)}")
        return None
