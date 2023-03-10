# Generated by Django 4.1 on 2022-10-19 09:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ppic", "0022_conversionmaterialreport_created_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliverynotecustomer",
            name="last_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="deliverynotematerial",
            name="image",
            field=models.ImageField(blank=True, upload_to="images/"),
        ),
        migrations.AddField(
            model_name="deliverynotematerial",
            name="last_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="deliverynotesubcont",
            name="last_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="productionreport",
            name="last_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="ScheduledProductDelivery",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "product_delivery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ppic.productdelivercustomer",
                    ),
                ),
                (
                    "schedule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ppic.deliveryschedule",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScheduledMaterialArrival",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "material_receipt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ppic.materialreceipt",
                    ),
                ),
                (
                    "schedule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ppic.materialreceiptschedule",
                    ),
                ),
            ],
        ),
    ]
