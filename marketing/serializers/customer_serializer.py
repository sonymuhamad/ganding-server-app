'''
this file provide serializer class for handle all request of customer 
'''

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from marketing.models import Customer,Invoice


class BaseCustomerSerializer(ModelSerializer):
    '''
    a serializer base class of customer
    '''
    
    class Meta:
        model = Customer
        fields = '__all__'

class CustomerSerializer(BaseCustomerSerializer):
    '''
    a extended serializer for managing handle request crud of customer
    '''
    total_product = serializers.IntegerField(read_only=True)
    total_sales_order = serializers.IntegerField(read_only=True)
