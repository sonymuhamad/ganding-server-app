from django.db import models
from manager.models import  AbstractCustomerVendor,AbstractCode,AbstractCreated

# Create your models here.

class Customer(AbstractCustomerVendor):
    pass


class AbstractCustomer(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss",)

    class Meta:
        abstract = True

class SalesOrder(AbstractCode,AbstractCustomer,AbstractCreated):
    fixed = models.BooleanField(default=False)

    class Meta(AbstractCode.Meta,AbstractCustomer.Meta,AbstractCreated.Meta):
        pass





