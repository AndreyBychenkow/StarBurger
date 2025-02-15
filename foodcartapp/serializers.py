from rest_framework import serializers
from phonenumber_field.validators import validate_international_phonenumber

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .models import Order, OrderItem, Product


@deconstructible
class NameValidator:
    def __call__(self, value):
        for char in value:
            if not (char.isalpha() or char.isspace() or char == '-'):
                raise ValidationError(
                    "Может содержать только буквы, пробелы и дефисы")


@deconstructible
class AddressValidator:
    def __call__(self, value):
        for char in value:
            if not (
                char.isalpha() or char.isdigit() or char.isspace() or char in '-.,/'):
                raise ValidationError("Адрес содержит недопустимые символы")


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        extra_kwargs = {
            'product': {'required': True},
            'quantity': {'required': True}
        }

    def validate_quantity(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError(
                "Количество должно быть от 1 до 20"
            )
        return value

    def validate_product(self, value):
        if not Product.objects.filter(pk=value.pk, is_available=True).exists():
            raise serializers.ValidationError(
                "Товар недоступен для заказа"
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    firstname = serializers.CharField(
        max_length=10,
        min_length=2,
        validators=[NameValidator()]
    )
    lastname = serializers.CharField(
        max_length=20,
        min_length=2,
        validators=[NameValidator()]
    )
    phonenumber = serializers.CharField(
        validators=[validate_international_phonenumber]
    )
    address = serializers.CharField(
        max_length=200,
        min_length=10,
        validators=[AddressValidator()]
    )

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'items']
        extra_kwargs = {
            'firstname': {'required': True},
            'lastname': {'required': True},
            'phonenumber': {'required': True},
            'address': {'required': True},
        }

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Заказ должен содержать минимум один товар"
            )

        product_ids = {item['product'].id for item in value}
        if len(product_ids) != len(value):
            raise serializers.ValidationError(
                "Обнаружены дублирующиеся товары в заказе"
            )

        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity']
            )

        return order
