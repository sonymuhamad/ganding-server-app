# Generated by Django 4.1 on 2022-08-27 21:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ppic", "00101_delete_warehouseproduct"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="WarehouseProductfix", new_name="WarehouseProduct",
        ),
    ]
