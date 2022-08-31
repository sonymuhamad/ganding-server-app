from rest_framework.serializers import ModelSerializer,ValidationError,StringRelatedField
from .models import Customer, SalesOrder
from ppic.models import DeliverySchedule, Product, ProductOrder,DeliveryNoteCustomer,ProductDeliverCustomer
from django.db.models import Prefetch

class SalesOrderSerializer(ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = ['id','fixed','code','customer']

class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id','name','email','phone','address']



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

    def validate_sales_order(self,attrs):
        if attrs.fixed or attrs.done:
            raise ValidationError('Sales order tersebut sudah fixed atau sudah selesai')
        return attrs
    
    def validate_done(self,attrs):
        if attrs:
            raise ValidationError('Product order tersebut sudah selesai')
        return attrs

    def validate(self, attrs):
        '''
        kalo quantity PRODUCT ORDERED lebih daripada DELIVERED, maka invalid
        '''
        delivered = attrs.get('delivered',0)
        if delivered > attrs['ordered']:
            raise ValidationError('Jumlah product terkirim lebih dari jumlah product pesanan')

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
        for i in range(len_schedules):
            if i > len_instance_schedules - 1:
                inserted_schedule.append(DeliverySchedule(**schedules[i],product_order=instance))
            else:
                instance_schedule = instance_schedules[i]
                instance_schedule.quantity = schedules[i]['quantity']
                instance_schedule.date = schedules[i]['date']
                updated_schedule.append(instance_schedule)
        
        deleted_schedule = deleted_schedule[:] + instance_schedules[l+i+1:]

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

    def validate(self, attrs):

        fixed = attrs.get('fixed',None)
        if fixed is None:
            return super().validate(attrs)
        else:
            if fixed == True:
                raise ValidationError('Sales order tersebut sudah fix, perubahan data tidak diizinkan')
            else:
                return super().validate(attrs)

    def validate_productorder_set(self,attrs):
        
        count = 0

        for productorder in attrs:
            temp = 0
            for schedule in productorder['deliveryschedule_set']:
                temp += schedule['quantity']
            if temp > productorder['ordered']:
                raise ValidationError(f'Jumlah product pada jadwal pengiriman melebihi jumlah product pada pesanan {count}')
            count += 1

        return attrs

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
    
    def clear_record(self,lst:list)->None:
        for instance in lst:
            instance.delete()
        return 

    def update(self, instance, validated_data):
        fixed = instance.fixed
        if fixed:
            raise ValidationError('Sales order tersebut sudah fix, perubahan data tidak diizinkan')

        old_product_order = instance.productorder_set.all()
        len_old_product = len(old_product_order) - 1 

        insert_new_schedule = []
        updated_schedule =[]
        deleted_schedule = []

        new_product_order = validated_data.pop('productorder_set')
        len_new_product_order = len(new_product_order)
        deleted_product_order = []
        updated_product_order = []
        
        instance.code = validated_data['code']
        instance.save()

        product_order_object = instance.productorder_set.all()

        i = 0
        for i in range(len_new_product_order):
            new_schedules = new_product_order[i].pop('deliveryschedule_set')
            len_new_schedules = len(new_schedules) 
            
            if i > len_old_product:
                instance_product_order = ProductOrder.objects.create(sales_order=instance,**new_product_order[i])
            else:
                instance_product_order = product_order_object[i]
                instance_product_order.ordered = new_product_order[i]['ordered']
                updated_product_order.append(instance_product_order)
                
                old_schedule = instance_product_order.deliveryschedule_set.all()
                len_old_schedule = len(old_schedule) - 1
            j = 0
            for j in range(len_new_schedules):
                
                if i > len_old_product:
                    insert_new_schedule.append(DeliverySchedule(**new_schedules[j],product_order=instance_product_order))     

                else:
                    if j > len_old_schedule:
                        insert_new_schedule.append(DeliverySchedule(**new_schedules[j],product_order=instance_product_order))
                    else:
                        instance_schedule = old_schedule[j]
                        instance_schedule.date = new_schedules[j]['date']
                        instance_schedule.quantity = new_schedules[j]['quantity']
                        updated_schedule.append(instance_schedule)

            deleted_schedule = deleted_schedule[:] + old_schedule[j+1:]         
        deleted_product_order = deleted_product_order[:] + old_product_order[i+1:]

        ProductOrder.objects.bulk_update(updated_product_order,['ordered'])
        DeliverySchedule.objects.bulk_update(updated_schedule,['quantity','date'])
        DeliverySchedule.objects.bulk_create(insert_new_schedule)

        self.clear_record(deleted_schedule)
        self.clear_record(deleted_product_order)
        
        return instance 
        


    class Meta:
        model = SalesOrder
        fields = ['id','code','customer','productorder_set','fixed']

### Customer sales order management serializer



### Customer sales order read only serializer

class ProductOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
        
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','delivered','product','deliveryschedule_set']
        depth = 1

class SalesOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    productorder_set = ProductOrderReadOnlySerializer(many= True)
    class Meta:
        model = SalesOrder
        fields = ['id','code','customer','productorder_set','fixed']


class CustomerSalesOrderReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    marketing_salesorder_related = SalesOrderReadOnlySerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id','name','phone','address','marketing_salesorder_related']

### Customer sales order read only serializer



### Customer delivery read only serializer

class DeliveryProductCustomerSerializer(ModelSerializer):
    '''
    get
    '''
    class Meta:
        model = ProductDeliverCustomer
        fields = ['id','quantity','paid','product_order']
        depth = 1

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















