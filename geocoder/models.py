import requests
from django.conf import settings
from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class AddressCoordinates(models.Model):
    address = models.TextField("Адрес места", max_length=200)
    latitude = models.FloatField("Широта", null=True, blank=True)
    longitude = models.FloatField("Долгота", null=True, blank=True)
    updated_at = models.DateTimeField(
        "Дата/время обновления", null=True, blank=True, db_index=True
    )

    CACHE_TTL = timezone.timedelta(days=30)

    class Meta:
        verbose_name = "координаты адреса"
        verbose_name_plural = "координаты адресов"

    @classmethod
    def get_coordinates(cls, address):
        try:
            obj, created = cls.objects.get_or_create(address=address)
            if created or obj.requires_refresh():
                obj.update_from_api()
            return (obj.latitude, obj.longitude) if obj.latitude is not None else None
        except Exception as e:
            logger.error(f"Error getting coordinates for {address}: {str(e)}")
            return None

    def requires_refresh(self):
        return (timezone.now() - self.updated_at) > self.CACHE_TTL

    def update_from_api(self):
        try:
            response = requests.get(
                "https://geocode-maps.yandex.ru/1.x/",
                params={
                    "apikey": settings.YANDEX_GEOCODER_API_KEY,
                    "format": "json",
                    "geocode": self.address,
                },
                timeout=5,
            )
            response.raise_for_status()

            data = response.json()
            if "response" in data and "GeoObjectCollection" in data["response"]:
                features = data["response"]["GeoObjectCollection"]["featureMember"]
                if features:
                    pos = features[0]["GeoObject"]["Point"]["pos"]
                    lon, lat = map(float, pos.split())
                    self.latitude = lat
                    self.longitude = lon
                    self.updated_at = timezone.now()
                    self.save()
                else:
                    logger.warning(f"No features found for address {self.address}")
                    self.latitude = None
                    self.longitude = None
                    self.save()
            else:
                logger.error(
                    f"Unexpected API response structure for {self.address}: {data}"
                )
                self.latitude = None
                self.longitude = None
                self.save()
        except requests.exceptions.RequestException as e:
            logger.error(f"Yandex API request error for {self.address}: {str(e)}")

            self.latitude = None
            self.longitude = None
            self.save()
        except Exception as e:
            logger.error(f"Error updating coordinates for {self.address}: {str(e)}")

            self.latitude = None
            self.longitude = None
            self.save()
