from django.db import models
from django.core.validators import MinValueValidator

from django.db.models import Count
from django.db.models import Sum, F

from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError

from geocoder.models import AddressCoordinates
from foodcartapp.utils import get_coordinates, calculate_distance, logger


def validate_positive(value):
    if value <= 0:
        raise ValidationError('Итоговая цена не может быть отрицательной.')


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('restaurant', 'Передан в ресторан'),
        ('delivery', 'У курьера'),
        ('completed', 'Завершён'),
    ]

    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )

    PAYMENT_METHOD_CHOICES = [
        ('electronic', 'Электронно'),
        ('cash', 'Наличные'),
    ]

    payment_method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        db_index=True
    )

    restaurant = models.ForeignKey(
        'Restaurant',
        verbose_name='Исполняющий ресторан',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    def get_available_restaurants(self):
        return Restaurant.objects.filter(
            menu_items__product__in=self.items.values('product'),
            menu_items__availability=True
        ).annotate(
            total_products=Count('menu_items__product', distinct=True)
        ).filter(
            total_products=self.items.count()
        ).distinct()

    comment = models.TextField(
        'Комментарий',
        blank=True,
        help_text='Дополнительная информация о заказе'
    )

    firstname = models.CharField('Имя', max_length=50)
    lastname = models.CharField('Фамилия', max_length=50)
    phonenumber = PhoneNumberField('Номер телефона', region='RU')
    address = models.CharField('Адрес', max_length=200)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    called_at = models.DateTimeField('Дата звонка', null=True, blank=True)
    delivered_at = models.DateTimeField('Дата доставки', null=True, blank=True)

    def update_total_price(self):
        self.total_price = self.items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0
        self.save()

    def get_restaurants_with_distances(self):

        try:
            delivery_point = get_coordinates(self.address)
            if not delivery_point:
                return []

            restaurants = []
            for restaurant in self.get_available_restaurants():
                restaurant_point = get_coordinates(restaurant.address)
                dist = calculate_distance(delivery_point, restaurant_point)
                if dist is not None:
                    restaurants.append({
                        'restaurant': restaurant,
                        'distance': dist
                    })

            return sorted(restaurants, key=lambda x: x['distance'])

        except Exception as e:
            logger.error(f"Error calculating distances: {str(e)}")
            return []


    def save(self, *args, **kwargs):
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.address != self.address:
                AddressCoordinates.objects.filter(address=old_order.address).delete()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.id} от {self.created_at.strftime("%d-%m-%Y %H:%M")}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='товар'
    )
    quantity = models.PositiveIntegerField('количество', default=1)
    fixed_price = models.DecimalField(
        verbose_name='фиксированная цена',
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00,
    )

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)
        self.order.update_total_price()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_total_price()

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.pk:
            old_rest = Restaurant.objects.get(pk=self.pk)
            if old_rest.address != self.address:
                AddressCoordinates.objects.filter(address=old_rest.address).delete()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )
    is_available = models.BooleanField(
        'Доступен для заказа',
        default=True,
        db_index=True
    )
    comment = models.TextField(
        null=True,
        blank=True
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    PAYMENT_METHOD_CHOICES = [
        ('electronic', 'Электронно'),
        ('cash', 'Наличные'),
    ]
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        db_index=True
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"
