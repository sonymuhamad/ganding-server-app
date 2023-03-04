'''
this file provide serializer class for handle all request of sales order, product order
'''
from rest_framework.serializers import ModelSerializer,IntegerField,CharField,Serializer,DateField

from datetime import date
from manager.shortcuts import invalid
from marketing.models import SalesOrder
from ppic.models import ProductOrder,DeliverySchedule

from ppic.serializers.delivery_serializer import TwoDepthProductDeliverCustomerSerializer

class BaseSalesOrderSerializer(ModelSerializer):
    '''
    a serializer base class of sales order
    '''

    class Meta:
        model   = SalesOrder
        fields  = '__all__'

class OneDepthSalesOrderSerializer(BaseSalesOrderSerializer):
    '''
    extend one depth serializer class of sales order
    '''
    
    class Meta(BaseSalesOrderSerializer.Meta):
        depth = 1

class BaseProductOrderSerializer(ModelSerializer):
    '''
    a serializer base class of product order
    '''

    class Meta:
        model   = ProductOrder
        fields  = '__all__'

class ProductOrderSerializer(BaseProductOrderSerializer):
    '''
    a serializer for handle create, update, delete request of product order
    '''

    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class OneDepthProductOrderSerializer(BaseProductOrderSerializer):
    '''
    extend one depth serializer class of product order
    '''

    class Meta(BaseProductOrderSerializer.Meta):
        depth = 1

class TwoDepthProductOrderSerializer(BaseProductOrderSerializer):
    '''
    extend two depth serialize class of product order
    '''

    class Meta(BaseProductOrderSerializer.Meta):
        depth = 2

class OneDepthSalesOrderNestedProductOrderSerializer(BaseSalesOrderSerializer):
    '''
    extend one depth nested sales order serializer to two depth product order serializer 
    '''
    productorder_set = TwoDepthProductOrderSerializer(many=True,read_only=True)

    class Meta(BaseSalesOrderSerializer.Meta):
        depth = 1

class BaseDeliveryScheduleSerializer(ModelSerializer):
    '''
    base delivery schedule serializer class
    '''

    class Meta:
        model = DeliverySchedule
        fields = '__all__'

class ThreeDepthDeliveryScheduleSerializer(BaseDeliveryScheduleSerializer):
    '''
    a serializer for get and retrieve delivery schedule
    '''

    class Meta(BaseDeliveryScheduleSerializer.Meta):
        depth = 3


class NestedProductOrderListSerializer(ModelSerializer):
    '''
    a serializer class for get product order nested from sales order
    '''
    productdelivercustomer_set = TwoDepthProductDeliverCustomerSerializer(many=True)
    total_deliver = IntegerField(read_only=True)
    class Meta:
        model = ProductOrder
        exclude = ['sales_order']
        depth = 1

class SalesOrderListSerializer(ModelSerializer):
    '''
    a serializer class for get, and retrieve sales order nested to product order
    '''
    productordered = IntegerField(read_only=True)
    productdelivered = IntegerField(read_only=True)
    productorder_set = NestedProductOrderListSerializer(many= True)
    class Meta:
        model = SalesOrder
        fields = '__all__'
        depth = 1

class SalesOrderManagementSerializer(ModelSerializer):
    '''
    a serializer class for management sales order
    '''
    
    description = CharField(allow_blank=True,default='')

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

class ProductOrderManagementSerializer(ModelSerializer):
    '''
    a serializer class for management product order
    '''
    delivered = IntegerField(default=0)
    price = IntegerField(default=0)
    
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

    def date_validation(self,scheduleDate):
        
        if scheduleDate < date.today():
            invalid('Could not enter a schedule for the past')
        
    def create(self, validated_data):
        self.date_validation(validated_data['date'])

        return super().create(validated_data)

    def validate_product_order(self,attrs):

        if attrs.delivered >= attrs.ordered:
            invalid('Order tersebut sudah selesai')

        if attrs.sales_order.closed:
            invalid('Sales order sudah ditutup')
        return attrs

    def update(self, instance, validated_data):

        if instance.fulfilled_quantity > 0:
            invalid('Jadwal sudah tidak bisa diubah')

        if validated_data['date'] != instance.date:
            self.date_validation(validated_data['date'])

        instance.quantity = validated_data.get('quantity',instance.quantity)
        instance.date = validated_data.get('date',instance.date)
        instance.save()
        return instance
        
    class Meta:
        model = DeliverySchedule
        fields = '__all__'

class ReportProductOrderSerializer(Serializer):
    '''
    a serializer for provide set of data about quantity product order each month
    '''
    total_order = IntegerField()
    date = DateField()
