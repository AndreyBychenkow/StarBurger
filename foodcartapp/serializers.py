from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from django.core.exceptions import ValidationError
from .models import Order, OrderItem, Product


class NameValidator:
    def __call__(self, value):
        for char in value:
            if not (char.isalpha() or char.isspace() or char == '-'):
                raise ValidationError(
                    "Может содержать только буквы, пробелы и дефисы")


class AddressValidator:
    def __call__(self, value):
        for char in value:
            if not (
                char.isalpha() or char.isdigit() or char.isspace() or char in '-.,/'):
                raise ValidationError("Адрес содержит недопустимые символы")


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={'does_not_exist': 'Товар с ID {pk_value} не существует'}
    )
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=20,
        error_messages={
            'min_value': 'Минимальное количество:  1',
            'max_value': 'Максимальное количество:  20'
        }
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def validate_product(self, value):
        if not value.is_available:
            raise serializers.ValidationError("Товар недоступен для заказа")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    firstname = serializers.CharField(
        max_length=10,
        min_length=2,
        trim_whitespace=True,
        validators=[NameValidator()],
        error_messages={
            'min_length': 'Имя должно содержать минимум 2 символа',
            'max_length': 'Имя не может быть длиннее 10 символов',
            'blank': 'Имя не может быть пустым'
        }
    )

    lastname = serializers.CharField(
        max_length=20,
        min_length=2,
        trim_whitespace=True,
        validators=[NameValidator()],
        error_messages={
            'min_length': 'Фамилия должна содержать минимум 2 символа',
            'max_length': 'Фамилия не может быть длиннее 20 символов',
            'blank': 'Фамилия не может быть пустой'
        }
    )

    phonenumber = PhoneNumberField(
        error_messages={'invalid': 'Неверный формат номера телефона'}
    )

    address = serializers.CharField(
        max_length=200,
        min_length=10,
        trim_whitespace=True,
        validators=[AddressValidator()],
        error_messages={
            'min_length': 'Адрес должен содержать минимум 10 символов',
            'max_length': 'Адрес не может быть длиннее 200 символов',
            'blank': 'Адрес не может быть пустым'
        }
    )

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'items']

    def validate(self, data):
        items = data.get('items', [])


        product_ids = [item['product'].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError({
                'items': ['Обнаружены дублирующиеся товары в заказе']
            })

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item_data)
            for item_data in items_data
        ])

        return order
