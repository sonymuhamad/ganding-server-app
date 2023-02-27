from django.db import models
from manager.models import AbstractCustomerVendor,AbstractCode,AbstractCreated
import datetime

class Supplier(AbstractCustomerVendor):
    pass

class AbstractSupplier(models.Model):
    supplier = models.ForeignKey(Supplier,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss")

    class Meta:
        abstract = True

class PurchaseOrderMaterial(AbstractCode,AbstractSupplier,AbstractCreated):
    done = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    date = models.DateField(default=datetime.date.today)
    tax = models.PositiveSmallIntegerField(default=10)
    discount = models.PositiveBigIntegerField(default=0)
    description = models.TextField(default='')

    class Meta(AbstractCode.Meta,AbstractSupplier.Meta,AbstractCreated.Meta):
        pass
    



















