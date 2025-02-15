from rest_framework import serializers
from .models import Order, OrderItem, Product


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        extra_kwargs = {
            'product': {'required': True},
            'quantity': {'required': True}
        }

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Количество должно быть не менее 1"
            )
        return value

    def validate_product(self, value):
        if not Product.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError(
                "Продукт не существует"
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'items'
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Заказ должен содержать минимум один товар"
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
