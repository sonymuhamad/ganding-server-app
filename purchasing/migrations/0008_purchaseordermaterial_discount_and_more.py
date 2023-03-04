# Generated by Django 4.1 on 2022-12-19 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("purchasing", "0007_purchaseordermaterial_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchaseordermaterial",
            name="discount",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="purchaseordermaterial",
            name="tax",
            field=models.PositiveSmallIntegerField(default=10),
        ),
    ]