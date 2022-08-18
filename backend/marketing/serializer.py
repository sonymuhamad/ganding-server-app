from rest_framework.serializers import ModelSerializer
from .models import Customer, SalesOrder
from ppic.models import Product

class CustomerSerializer(ModelSerializer):
   
    class Meta:
        model = Customer
        fields = ['name','email','phone','address']


class SalesOrderSerializer(ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = ['fixed','code','customer']



