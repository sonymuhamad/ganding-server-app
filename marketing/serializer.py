from rest_framework.serializers import ModelSerializer,IntegerField,DateField
from .models import Customer, SalesOrder,Invoice
from ppic.models import DeliverySchedule, Product, Process, ProductOrder,DeliveryNoteCustomer,ProductDeliverCustomer, WarehouseProduct
from rest_framework import serializers
from django.db.models import Prefetch
from manager.shortcuts import invalid
from datetime import date

from ppic.serializer import ProductListSerializer

class SalesOrderSerializer(ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = ['id','fixed','code','created','date',]

class CustomerSerializer(ModelSerializer):
    '''
    a serializer class for get data customer
    '''
    total_product = serializers.IntegerField(read_only=True)
    total_sales_order = serializers.IntegerField(read_only=True)
    most_ordered_product = ProductListSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = '__all__'


class DeliveryScheduleReadOnlySerializer(ModelSerializer):
    '''
    a serializer class for get and retrieve delivery schedule
    '''
    class Meta:
        model = DeliverySchedule
        fields = '__all__'
        depth = 3


class ProductOrderManagementSerializer(ModelSerializer):
    '''
    a serializer class for management product order
    '''
    delivered = serializers.IntegerField(default=0)
    price = serializers.IntegerField(default=0)
    
    def validate(self, attrs):
        '''
        kalo quantity PRODUCT ORDERED lebih daripada DELIVERED, maka invalid
        '''
        delivered = attrs.get('delivered',0)
        so = attrs.get('sales_order')
        product = attrs.get('product')

        if delivered > attrs['ordered']:
             invalid('Jumlah product terkirim lebih dari jumlah product pesanan')

        if so.fixed or so.closed:
             invalid('Sales order tersebut sudah fixed atau sudah ditutup')

        if so.customer != product.customer:
            invalid(f'Product tersebut bukan milik ${so.customer.name}')

        return super().validate(attrs)

    def create(self, validated_data):

        product = validated_data['product']
        sales_order = validated_data['sales_order']
        
        product_order = ProductOrder.objects.filter(product=product,sales_order=sales_order).first()
        
        if product_order == None:
            product_order = ProductOrder.objects.create(**validated_data)
        else:
            product_order.ordered += validated_data['ordered']
            product_order.save()

        return product_order

    def update(self, instance, validated_data):
    
        instance.ordered = validated_data['ordered']
        instance.price = validated_data.get('price',instance.price)
        instance.save()
        
        return instance 
        
    class Meta:
        model = ProductOrder
        fields = '__all__'

class DeliveryScheduleManagementSerializer(ModelSerializer):
    '''
    a serializer class for management delivery schedule
    '''
    def validate_date(self,attrs):
        
        if attrs < date.today():
            invalid('Could not enter a schedule for the past')
        
        return attrs

    def validate_product_order(self,attrs):

        if attrs.delivered >= attrs.ordered:
            invalid('Order tersebut sudah selesai')

        if attrs.sales_order.closed:
            invalid('Sales order sudah ditutup')
        return attrs

    def update(self, instance, validated_data):

        if instance.fulfilled_quantity > 0:
            invalid('Jadwal sudah tidak bisa diubah')

        instance.quantity = validated_data.get('quantity',instance.quantity)
        instance.date = validated_data.get('date',instance.date)
        instance.save()
        return instance
        
    class Meta:
        model = DeliverySchedule
        fields = '__all__'

class SalesOrderManagementSerializer(ModelSerializer):
    '''
    a serializer class for management sales order
    '''
    
    description = serializers.CharField(allow_blank=True,default='')

    def update(self, instance, validated_data):
        
        fixed = instance.fixed
        validate_data_fixed = validated_data['fixed']
        if instance.closed:
            invalid('Sales order tersebut sudah ditutup')

        if not instance.closed and validated_data['closed']:
            for product_order in instance.productorder_set.all():
                if product_order.ordered < product_order.delivered:
                    invalid('Masih ada pesanan yang belum selesai, Sales order tidak bisa ditutup')
        
        if fixed and validate_data_fixed and not validated_data['closed']:
            invalid('Sales order sudah berjalan, jika ingin mengubah data, jadikan status sales order menjadi Pending')
        
        return super().update(instance, validated_data)
        
    class Meta:
        model = SalesOrder
        fields = '__all__'

class ProductOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
        
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','delivered','product','deliveryschedule_set','price']
        depth = 1

class SalesOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    productorder_set = ProductOrderReadOnlySerializer(many= True)
    class Meta:
        model = SalesOrder
        fields = ['id','code','productorder_set','fixed','date','description','closed']

### Sales order page

class ProductDeliverListSerializer(ModelSerializer):
    '''
    for get all delivered product related to particular sales order
    '''
    class Meta:
        model  = ProductDeliverCustomer
        exclude = ['product_order']
        depth = 2

class NestedProductOrderListSerializer(ModelSerializer):
    '''
    a serializer class for get product order nested from sales order
    '''
    productdelivercustomer_set = ProductDeliverListSerializer(many=True)
    total_deliver = serializers.IntegerField(read_only=True)
    class Meta:
        model = ProductOrder
        exclude = ['sales_order']
        depth = 1

class SalesOrderListSerializer(ModelSerializer):
    '''
    a serializer class for get, and retrieve sales order nested to product order
    '''
    productordered = serializers.IntegerField(read_only=True)
    productdelivered = serializers.IntegerField(read_only=True)
    productorder_set = NestedProductOrderListSerializer(many= True)
    class Meta:
        model = SalesOrder
        fields = '__all__'
        depth = 1

class DeliveryProductCustomerListSerializer(ModelSerializer):
    '''
    get
    '''
    class Meta:
        model = ProductDeliverCustomer
        fields = '__all__'
        depth = 2

class DeliveryNoteCustomerListSerializer(ModelSerializer):
    '''
    get
    '''
    productdelivercustomer_set = DeliveryProductCustomerListSerializer(many=True)
    class Meta:
        model = DeliveryNoteCustomer
        fields = '__all__'
        depth = 1



class DeliveryProductCustomerSerializer(ModelSerializer):
    '''
    get
    '''
    class Meta:
        model = ProductDeliverCustomer
        fields = ['id','quantity','product_order']
        depth = 2

class DeliveryNoteCustomerSerializer(ModelSerializer):
    '''
    get
    '''
    productdelivercustomer_set = DeliveryProductCustomerSerializer(many=True)
    class Meta:
        model = DeliveryNoteCustomer
        fields = ['id','code','created','note','driver','vehicle','productdelivercustomer_set']
        depth = 1

class DeliveryCustomerSerializer(ModelSerializer):
    '''
    get
    '''
    ppic_deliverynotecustomer_related = DeliveryNoteCustomerSerializer(many = True)
    class Meta:
        model = Customer
        fields = ['id','name','email','phone','address','ppic_deliverynotecustomer_related']

class DeliveryNoteCustomerManagementSerializer(ModelSerializer):
    '''
    put post
    '''
    class Meta:
        model = DeliveryNoteCustomer
        fields = ['id','code','note']

class WarehouseProductReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseProduct
        exclude = ['product','process']
        depth = 1

class ProcessReadOnlySerializer(ModelSerializer):
    warehouseproduct_set = WarehouseProductReadOnlySerializer(many=True)
    class Meta:
        model = Process
        exclude = ['product']
        depth = 1

class ProductCustomerReadOnlySerializer(ModelSerializer):
    ppic_process_related = ProcessReadOnlySerializer(many=True)
    class Meta:
        model = Product
        exclude = ['customer']
        depth = 1

class CustomerDetailReadOnlySerializer(ModelSerializer):
    ppic_deliverynotecustomer_related = DeliveryNoteCustomerSerializer(many = True)
    marketing_salesorder_related = SalesOrderReadOnlySerializer(many=True)
    ppic_product_related = ProductCustomerReadOnlySerializer(many=True)
    class Meta:
        model = Customer
        fields = '__all__'

class ProductCustomerDetailSerializer(ModelSerializer):
    class Meta:
        model = Product
        exclude = ['customer']

class CustomerDetailProductSerializer(ModelSerializer):
    ppic_product_related = ProductCustomerDetailSerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id','name','ppic_product_related']


class InvoiceManagementSerializer(ModelSerializer):
    '''
    a serializer class for management invoice
    '''

    def create(self, validated_data):

        sales_order = validated_data['sales_order']
        if not sales_order.closed:
            invalid('Harap selesaikan sales order dahulu sebelum membuat invoice') 

        querysetInvoice = Invoice.objects.filter(sales_order=sales_order)
        if querysetInvoice.exists():
            invalid('Invoice untuk sales order tersebut sudah dibuat')

        return super().create(validated_data)

    def update(self, instance, validated_data):

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

    class Meta:
        model = Invoice
        fields = '__all__'

class ProductOrderReadOnlyFromInvoiceSerializer(ModelSerializer):
    '''
    a nested serializer for get product order from sales order and from invoice
    '''
    class Meta:
        model = ProductOrder
        exclude = ['sales_order']
        depth = 2

class SalesOrderReadOnlyFromInvoiceSerializer(ModelSerializer):
    '''
    a nested serializer for get sales order from invoice
    '''
    productorder_set = ProductOrderReadOnlyFromInvoiceSerializer(many=True)
    class Meta:
        model = SalesOrder
        fields = '__all__'
        depth = 1

class InvoiceReadOnlySerializer(ModelSerializer):
    '''
    a serializer class for get data of invoice
    '''
    sales_order = SalesOrderReadOnlyFromInvoiceSerializer()
    class Meta:
        model = Invoice
        fields = '__all__'


class ReportProductOrderSerializer(serializers.Serializer):
    '''
    a serializer for provide set of data about quantity product order each month
    '''
    total_order = IntegerField()
    date = DateField()






