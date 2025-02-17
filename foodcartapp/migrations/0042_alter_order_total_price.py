# Generated by Django 5.1.6 on 2025-02-16 14:43

import foodcartapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0041_order_total_price_alter_orderitem_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, validators=[foodcartapp.models.validate_positive]),
        ),
    ]
