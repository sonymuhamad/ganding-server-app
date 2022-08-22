from rest_framework.serializers import ModelSerializer,ValidationError
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
        fields = ['quantity','date']

class ProductOrderManagementSerializer(ModelSerializer):
    deliveryschedule_set = DeliveryScheduleManagementSerializer(many=True)

    def create(self, validated_data):
        
        schedule = validated_data.pop('deliveryschedule_set')
        product_order = ProductOrder.objects.create(**validated_data)
        DeliverySchedule.objects.bulk_create(schedule)

        return product_order 
        

    class Meta:
        model = ProductOrder
        fields = ['ordered','product','deliveryschedule_set']

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
        temp_delivery_schedule = [] #list 2 dimesion
        delivery_schedule_objects = []

        temp_product_orders = validated_data.pop('productorder_set')
        product_orders_objects = []
        
        for product_order in temp_product_orders:
            schedule = product_order.pop('deliveryschedule_set')
            temp_delivery_schedule.append(schedule)
        
        new_sales_order = SalesOrder.objects.create(**validated_data)

        for product_order in temp_product_orders:
            product_orders_objects.append(ProductOrder.objects.create(sales_order=new_sales_order,**product_order))    


        for i in range(len(temp_delivery_schedule)):
            for j in range(len(temp_delivery_schedule[i])):
                delivery_schedule_objects.append(DeliverySchedule(**temp_delivery_schedule[i][j],product_order=product_orders_objects[i]))

        # print(delivery_schedule_objects)
        DeliverySchedule.objects.bulk_create(delivery_schedule_objects)
        
        return new_sales_order
        
    
    

    class Meta:
        model = SalesOrder
        fields = ['code','customer','productorder_set']

