from rest_framework.serializers import ModelSerializer,ValidationError,StringRelatedField
from .models import Customer, SalesOrder
from ppic.models import DeliverySchedule, Product, Process, ProductOrder,DeliveryNoteCustomer,ProductDeliverCustomer, WarehouseProduct
from rest_framework import serializers
from django.db.models import Prefetch

class SalesOrderSerializer(ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = ['id','fixed','code','created','done','date',]

class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'



class CustomerManagementSerializer(ModelSerializer):
    marketing_salesorder_related = SalesOrderSerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id','name','email','phone','address','marketing_salesorder_related']


### Customer sales order management serializer

class DeliveryScheduleManagementSerializer(ModelSerializer):

    '''
    post , put
    '''
    class Meta:
        model = DeliverySchedule
        fields = ['id','quantity','date']

class ProductOrderManagementSerializer(ModelSerializer):
    '''
    post , put
    '''
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)

    def validate_deliveryschedule_set(self,attrs):
        delivered = self.initial_data.get('delivered',0)
        available_schedule = self.initial_data['ordered'] - delivered
        temp = 0
        
        for schedule in attrs:
            temp += schedule['quantity']
        
        if temp > available_schedule:
            raise ValidationError('Jumlah pengiriman product pada jadwal melebihi pesanan')
        
        return attrs

    def validate(self, attrs):
        '''
        kalo quantity PRODUCT ORDERED lebih daripada DELIVERED, maka invalid
        '''
        delivered = attrs.get('delivered',0)
        so = attrs.get('sales_order')
        done = attrs.get('done')

        if delivered > attrs['ordered']:
             raise ValidationError('Jumlah product terkirim lebih dari jumlah product pesanan')

        if so.fixed or so.done:
             raise ValidationError('Sales order tersebut sudah fixed atau sudah selesai')

        if done:
            raise ValidationError('Product order tersebut sudah selesai')

        return super().validate(attrs)

    def create(self, validated_data):
        
        schedules = validated_data.pop('deliveryschedule_set')
        inserted_schedule = []
        product = validated_data['product']
        sales_order = validated_data['sales_order']
        
        product_order = ProductOrder.objects.filter(product=product,sales_order=sales_order).first()
        
        if product_order == None:
            product_order = ProductOrder.objects.create(**validated_data)
        else:
            product_order.ordered += validated_data['ordered']
            product_order.save()

        for schedule in schedules:
            inserted_schedule.append(DeliverySchedule(**schedule,product_order=product_order))

        DeliverySchedule.objects.bulk_create(inserted_schedule)

        return product_order

    def update(self, instance, validated_data):
        inserted_schedule = []
        updated_schedule = []
        deleted_schedule = []

        schedules = validated_data.pop('deliveryschedule_set')
        len_schedules = len(schedules)

        instance_schedules = instance.deliveryschedule_set.all()
        len_instance_schedules = len(instance_schedules)
        instance.ordered = validated_data['ordered']
        instance.delivered = validated_data.get('delivered',instance.delivered)
        instance.save()

        l = 0
        if len_schedules > 0:    
            for i in range(len_schedules):
                if i > len_instance_schedules - 1:
                    inserted_schedule.append(DeliverySchedule(**schedules[i],product_order=instance))
                else:
                    instance_schedule = instance_schedules[i]
                    instance_schedule.quantity = schedules[i]['quantity']
                    instance_schedule.date = schedules[i]['date']
                    updated_schedule.append(instance_schedule)
            l += i

        deleted_schedule = deleted_schedule[:] + instance_schedules[l:]

        DeliverySchedule.objects.bulk_create(inserted_schedule)
        DeliverySchedule.objects.bulk_update(updated_schedule,['quantity','date'])

        for schedule in deleted_schedule:
            schedule.delete()
        
        return instance 
        
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','product','delivered','deliveryschedule_set','sales_order','done']



class ProductOrderManagementUnitedSerializer(ModelSerializer):
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','product','delivered','deliveryschedule_set','done']

class SalesOrderManagementSerializer(ModelSerializer):
    '''
    post , put
    '''
    productorder_set = ProductOrderManagementUnitedSerializer(many=True)

    def validate_productorder_set(self,attrs):
        
        count = 1

        for productorder in attrs:
            temp = 0
            for schedule in productorder['deliveryschedule_set']:
                temp += schedule['quantity']
            if temp > productorder['ordered']:
                raise ValidationError(f'Jumlah product pada jadwal pengiriman melebihi jumlah product pada pesanan {count}')
            count += 1

        return attrs

    def validate(self, attrs):
        productorder = attrs['productorder_set']
        customer = attrs['customer']
        for porder in productorder:
            if porder['product'].customer != customer:
                raise ValidationError('Product and customer do not match')

        return super().validate(attrs)


    def create(self, validated_data):
        delivery_schedule_objects = [] 
        temp_product_orders = validated_data.pop('productorder_set')
        new_sales_order = SalesOrder.objects.create(**validated_data)
        
        for product_order in temp_product_orders:
            schedules = product_order.pop('deliveryschedule_set')

            product = product_order['product']

            new_product_order = ProductOrder.objects.filter(product=product,sales_order=new_sales_order).first()
        
            if new_product_order == None:
                new_product_order = ProductOrder.objects.create(sales_order=new_sales_order,**product_order)
            else:
                new_product_order.ordered += product_order['ordered']
                new_product_order.save()
            
            for schedule in schedules:
                delivery_schedule_objects.append(DeliverySchedule(**schedule,product_order=new_product_order))     

        DeliverySchedule.objects.bulk_create(delivery_schedule_objects)
        return new_sales_order

    def update(self, instance, validated_data):
        
        fixed = instance.fixed
        validate_data_fixed = validated_data['fixed']

        if fixed and validate_data_fixed:
            raise ValidationError('Sales order has been fixed, data changes are not allowed')
        elif not fixed and validate_data_fixed or fixed and not validate_data_fixed :
            instance.fixed = validated_data['fixed']

        instance.code = validated_data['code']
        instance.date = validated_data['date']
        instance.save()
        
        return instance 
        
    class Meta:
        model = SalesOrder
        fields = ['id','code','customer','productorder_set','fixed','date','done']
        read_only_fields = ['productorder_set']

### Customer sales order management serializer



### Customer sales order read only serializer

class ProductOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
        
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','delivered','product','deliveryschedule_set','done']
        depth = 1

class SalesOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    productorder_set = ProductOrderReadOnlySerializer(many= True)
    class Meta:
        model = SalesOrder
        fields = ['id','code','productorder_set','fixed','done','date']


class CustomerSalesOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    marketing_salesorder_related = SalesOrderReadOnlySerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id','name','phone','address','marketing_salesorder_related']

### Sales order page

class ProductDeliverListSerializer(ModelSerializer):
    '''
    for get all delivered product related to particular sales order
    '''
    class Meta:
        model  = ProductDeliverCustomer
        exclude = ['product_order']
        depth = 2

class ProductOrderListSerializer(ModelSerializer):
    '''
    get
    '''
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
    productdelivercustomer_set = ProductDeliverListSerializer(many=True)
    class Meta:
        model = ProductOrder
        exclude = ['sales_order']
        depth = 1

class SalesOrderListSerializer(ModelSerializer):
    productordered = serializers.IntegerField(read_only=True)
    productdelivered = serializers.IntegerField(read_only=True)
    productorder_set = ProductOrderListSerializer(many= True)
    class Meta:
        model = SalesOrder
        fields = '__all__'
        depth = 1

### Sales order page

### Customer sales order read only serializer



### Customer delivery read only serializer

class DeliveryProductCustomerListSerializer(ModelSerializer):
    '''
    get
    '''
    class Meta:
        model = ProductDeliverCustomer
        fields = ['id','quantity','paid','product_order']
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
        fields = ['id','quantity','paid','product_order']
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

### Customer delivery read only serializer


### Customer delivery note management serializer

class DeliveryProductCustomerManagementSerializer(ModelSerializer):
    '''
    put post
    '''
    class Meta:
        model = ProductDeliverCustomer
        fields = ['id','paid']

class DeliveryNoteCustomerManagementSerializer(ModelSerializer):
    '''
    put post
    '''
    class Meta:
        model = DeliveryNoteCustomer
        fields = ['id','code','note']

### Customer delivery note management serializer

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







