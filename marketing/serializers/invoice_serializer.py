'''
this file provide serializer class for handle all request of invoice
'''

from rest_framework.serializers import ModelSerializer
from marketing.models import Invoice,SalesOrder

from .sales_order_serializer import OneDepthSalesOrderNestedProductOrderSerializer
from manager.shortcuts import invalid


class BaseInvoiceSerializer(ModelSerializer):
    '''
    a serializer base class of invoice
    '''

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceSerializer(BaseInvoiceSerializer):
    '''
    a serializer class for handle create, update, delete request of invoice 
    '''

    def validate_unique_invoice(self,sales_order:SalesOrder):
        '''
        check if there are invoice from this sales order
        '''

        if Invoice.objects.filter(sales_order=sales_order).exists():
            invalid('Invoice untuk sales order tersebut sudah dibuat')
        
        return sales_order

    def validate_sales_order(self,attrs:SalesOrder):
        '''
        if sales order is not closed then unable to make invoice
        '''
        if not attrs.closed:
            invalid()

        return attrs
    
    def create(self, validated_data):
        '''
        method to create invoice
        '''
        sales_order = validated_data['sales_order']
        self.validate_unique_invoice(sales_order)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        '''
        method to update invoice
        '''
        
        if instance.done and validated_data['done']:
            invalid('Invoice sudah selesai')

        if instance.closed:
            invalid('Invoice tersebut sudah ditutup')

        instance.code = validated_data.get('code',instance.code)
        instance.date = validated_data.get('date',instance.date)
        instance.discount = validated_data.get('discount',instance.discount)
        instance.tax = validated_data.get('tax',instance.tax)
        instance.closed = validated_data.get('closed',instance.closed)
        instance.done = validated_data.get('done',instance.done)

        instance.save()
        return instance

class OneDepthInvoiceSerializer(BaseInvoiceSerializer):
    '''
    extend one depth of invoice serializer
    '''

    class Meta(BaseInvoiceSerializer.Meta):
        depth = 1

class InvoiceNestedSalesOrderSerializer(BaseInvoiceSerializer):
    '''
    invoice serializer nested to one depth sales order serializer and nested to two depth product order serializer
    '''
    sales_order = OneDepthSalesOrderNestedProductOrderSerializer()


