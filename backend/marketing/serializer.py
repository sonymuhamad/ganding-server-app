from rest_framework.serializers import ModelSerializer,ValidationError,StringRelatedField
from .models import Customer, SalesOrder
from ppic.models import DeliverySchedule, Product, ProductOrder
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

class DeliveryScheduleManagementSerializer(ModelSerializer):
    class Meta:
        model = DeliverySchedule
        fields = ['id','quantity','date']

class ProductOrderManagementSerializer(ModelSerializer):
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
    def create(self, validated_data):
        
        schedule = validated_data.pop('deliveryschedule_set')
        product_order = ProductOrder.objects.create(**validated_data)
        DeliverySchedule.objects.bulk_create(schedule)

        return product_order 
        
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','product','deliveryschedule_set']

class SalesOrderManagementSerializer(ModelSerializer):
    productorder_set = ProductOrderManagementSerializer(many=True)

    def validate_productorder_set(self,attrs):

        count = 0

        for productorder in attrs:
            temp = 0
            for schedule in productorder['deliveryschedule_set']:
                temp += schedule['quantity']
            if temp > productorder['ordered']:
                raise ValidationError(f'quantity pada jadwal kedatangan melebihi quantity pada pesanan product {count}')
            count += 1

        return attrs

    def create(self, validated_data):
        print(validated_data)
        delivery_schedule_objects = [] 
        temp_product_orders = validated_data.pop('productorder_set')
        new_sales_order = SalesOrder.objects.create(**validated_data)
        
        for product_order in temp_product_orders:
            schedules = product_order.pop('deliveryschedule_set')
            new_product_order = ProductOrder.objects.create(sales_order=new_sales_order,**product_order)
            
            for schedule in schedules:
                delivery_schedule_objects.append(DeliverySchedule(**schedule,product_order=new_product_order))     

        DeliverySchedule.objects.bulk_create(delivery_schedule_objects)
        return new_sales_order
    
    def clear_record(self,lst:list)->None:
        for instance in lst:
            instance.delete()
        return 
    
    def update_many(self,object,lst_of_objects:list,fields:list) -> None:
        object.objects.bulk_update(lst_of_objects,fields)
        return 

    def insert_many(self,object,lst_of_objects:list) -> None:
        object.objects.bulk_create(lst_of_objects)
        return

    def update(self, instance, validated_data):

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

        
        for i in range(len_new_product_order):
            new_schedules = new_product_order[i].pop('deliveryschedule_set')
            len_new_schedules = len(new_schedules) 
            
            if i > len_old_product:
                instance_product_order = ProductOrder.objects.create(sales_order=instance,**new_product_order[i])
            else:
                instance_product_order = product_order_object[i]
                instance_product_order.ordered = new_product_order[i]['ordered']
                instance_product_order.product = new_product_order[i]['product']
                updated_product_order.append(instance_product_order)
                
                old_schedule = instance_product_order.deliveryschedule_set.all()
                len_old_schedule = len(old_schedule) - 1

            for j in range(len_new_schedules):
                
                if i > len_old_product:
                    insert_new_schedule.append(DeliverySchedule(**new_schedules[j],instance_product_order=instance_product_order))     

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

        ProductOrder.objects.bulk_update(updated_product_order,['ordered','product'])
        DeliverySchedule.objects.bulk_update(updated_schedule,['quantity','date'])
        DeliverySchedule.objects.bulk_create(insert_new_schedule)

        self.clear_record(deleted_schedule)
        self.clear_record(deleted_product_order)
        
        return instance 
        


    class Meta:
        model = SalesOrder
        fields = ['id','code','customer','productorder_set']





class ProductOrderReadOnlySerializer(ModelSerializer):
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)
        
    class Meta:
        model = ProductOrder
        fields = ['id','ordered','product','deliveryschedule_set']
        depth = 1

class SalesOrderReadOnlySerializer(ModelSerializer):
    productorder_set = ProductOrderReadOnlySerializer(many= True)

    class Meta:
        model = SalesOrder
        fields = ['id','code','customer','productorder_set']
        depth = 1