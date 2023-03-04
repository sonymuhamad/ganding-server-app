from django.db import models
from manager.models import  AbstractCustomerVendor,AbstractCode,AbstractCreated
from datetime import date

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

class InvoiceManager(models.Manager):
    '''
    extending base manager for invoice
    '''

    def get_queryset_related(self)-> models.QuerySet:
        '''
        extended function to get list of invoice nested to sales order    
        '''
        return self.select_related('sales_order','sales_order__customer')

class Invoice(AbstractCode,AbstractCreated):
    '''
    a model class for invoicing data of sales order
    '''
    objects = InvoiceManager()

    sales_order = models.ForeignKey(SalesOrder,on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    done = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    discount = models.PositiveBigIntegerField(default=0)
    tax = models.PositiveSmallIntegerField(default=10)



