# Generated by Django 5.1.6 on 2025-02-15 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_order_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_available',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Доступен для заказа'),
        ),
    ]
