# Generated by Django 4.1 on 2022-10-19 10:23

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ppic", "0023_deliverynotecustomer_last_update_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliverynotecustomer",
            name="date",
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name="deliverynotematerial",
            name="date",
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name="deliverynotesubcont",
            name="date",
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name="deliveryschedule",
            name="fulfilled_quantity",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="materialreceiptschedule",
            name="fulfilled_quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]