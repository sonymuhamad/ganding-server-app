# Generated by Django 4.1 on 2022-12-21 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0007_invoice"),
    ]

    operations = [
        migrations.AddField(
            model_name="salesorder",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
    ]
