# Generated by Django 4.1 on 2022-08-19 09:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0002_alter_salesorder_customer"),
    ]

    operations = [
        migrations.AddField(
            model_name="salesorder",
            name="created",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
