# Generated by Django 5.1.6 on 2025-02-17 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, help_text='Дополнительная информация о заказе', verbose_name='Комментарий'),
        ),
    ]
