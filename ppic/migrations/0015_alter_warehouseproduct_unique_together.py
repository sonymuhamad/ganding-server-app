# Generated by Django 4.1 on 2022-08-29 18:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ppic", "0014_alter_warehouseproduct_process"),
    ]

    operations = [
        migrations.AlterUniqueTogether(name="warehouseproduct", unique_together=set(),),
    ]
