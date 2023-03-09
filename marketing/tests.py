from django.test import TestCase
from .models import Invoice,SalesOrder,Customer
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError

class BaseTestCase:
    def setUp(self):
        Customer.objects.create(name='Exedy',address='Address',email='Exedy@gmail.com',phone=2412418212,pk=1)
        customer = Customer.objects.get(name='Exedy')
        
        sales_order = SalesOrder.objects.create(customer=customer,code='Code Sales Order',pk=1)
        Invoice.objects.create(code='Code Invoice',sales_order=sales_order,pk=1)

class SalesOrderTestCase(BaseTestCase,TestCase):

    def test_sales_order_not_exists(self):
        ## test fixed field is false when sales order is created     
        with self.assertRaises(ObjectDoesNotExist):
            SalesOrder.objects.get(code='Code Sales Orders')

    def test_default_fixed_field(self):
        ## test default value of fixed field
        sales_order = SalesOrder.objects.get(code='Code Sales Order')
        self.assertFalse(sales_order.fixed)

    def test_default_done_field(self):
        ## test default value of done field
        sales_order = SalesOrder.objects.get(code='Code Sales Order')
        self.assertFalse(sales_order.fixed)

    def test_default_date_field(self):
        ## test default value of done field
        sales_order = SalesOrder.objects.get(pk=1)
        self.assertEqual(date.today(),sales_order.date)

    def test_default_created_field(self):
        ## test default value of created field
        sales_order = SalesOrder.objects.get(pk=1)
        self.assertIsNotNone(sales_order.created)

class InvoiceTestCase(BaseTestCase,TestCase):
    
    def test_default_invoice_tax(self):
        '''
        check the default value of tax's field
        '''
        invoice = Invoice.objects.get(code='Code Invoice')
        self.assertEqual(10,invoice.tax)

    def test_default_discount_field(self):
        ## test default discount field
        invoice = Invoice.objects.get(code='Code Invoice')
        self.assertEqual(0,invoice.discount)

    def test_default_done_field(self):
        ## test default done field of invoice
        invoice = Invoice.objects.get(pk=1)
        self.assertFalse(invoice.done)

    def test_default_closed_field(self):
        ## test default done field of invoice
        invoice = Invoice.objects.get(pk=1)
        self.assertFalse(invoice.closed)

    def test_sales_order_field_is_not_none(self):
        ## test sales order field of invoice is not none
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(code='New Invoice Code')

    def test_sales_order_invoices_is_not_none(self):
        """
        test sales order invoice's is not none
        """
        invoice = Invoice.objects.get(code='Code Invoice')
        
        with self.assertRaises(IntegrityError):
            invoice.sales_order = None
            invoice.save()
