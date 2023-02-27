from django.db import models
from manager.models import  AbstractCustomerVendor,AbstractCode,AbstractCreated
from datetime import date

# Create your models here.

class Customer(AbstractCustomerVendor):
    pass


class AbstractCustomer(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss",)

    class Meta:
        abstract = True

class SalesOrder(AbstractCode,AbstractCustomer,AbstractCreated):
    fixed = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    date = models.DateField(default=date.today)
    description = models.TextField(default='')

    class Meta(AbstractCode.Meta,AbstractCustomer.Meta,AbstractCreated.Meta):
        pass


class Invoice(AbstractCode,AbstractCreated):
    '''
    a model class for invoicing data of sales order
    '''
    sales_order = models.ForeignKey(SalesOrder,on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    done = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    discount = models.PositiveBigIntegerField(default=0)
    tax = models.PositiveSmallIntegerField(default=10)



