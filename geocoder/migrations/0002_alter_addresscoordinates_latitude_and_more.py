# Generated by Django 5.1.6 on 2025-02-19 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("geocoder", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="addresscoordinates",
            name="latitude",
            field=models.FloatField(null=True, verbose_name="Широта"),
        ),
        migrations.AlterField(
            model_name="addresscoordinates",
            name="longitude",
            field=models.FloatField(null=True, verbose_name="Долгота"),
        ),
    ]
