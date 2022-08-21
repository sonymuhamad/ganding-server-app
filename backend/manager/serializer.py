from dataclasses import field
from rest_framework.serializers import ModelSerializer,StringRelatedField
from .models import UserActivity,Activity
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User,Group

from ppic.models import MaterialRequirementPlanning,DetailMrp,Product,WarehouseProduct,Process,ProductOrder,WarehouseWip
from marketing.models import SalesOrder


class ActivitySerializer(ModelSerializer):
    class Meta:
        model = Activity
        fields = ['name']

class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']

class AccessTokenSerializer(ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ['token','expires','scope','created']

class UserManagementSerializer(ModelSerializer):
    groups = GroupSerializer(many=True)
    
    class Meta:
        model = User
        fields = ['username','last_login','email','groups'] 
    
class UserSerializer(ModelSerializer):
    oauth2_provider_accesstoken = AccessTokenSerializer(many=True)
    groups = GroupSerializer(many=True)
    
    class Meta:
        model = User
        fields = ['last_login','username','email','oauth2_provider_accesstoken','groups']

class UserActivitySerializer(ModelSerializer):
   
    class Meta:
        model = UserActivity
        fields = ['user','activity','descriptions']
        depth = 2 # dive 2 relation trough useractivity

class DetailMrpSerializer(ModelSerializer):
    
    class Meta:
        model = DetailMrp
        fields = ['quantity','quantity_production','product']
        depth = 1

class ReportMrpSerializer(ModelSerializer):
    detailmrp_set =  DetailMrpSerializer(many=True) #related name

    class Meta:
        model = MaterialRequirementPlanning
        fields = ['material','quantity','detailmrp_set']
        depth = 1

class WarehouseWipSerializer(ModelSerializer):
    warehouse_type = StringRelatedField()
    class Meta:
        model = WarehouseWip
        fields = ['quantity','warehouse_type']

class WarehouseProductSerializer(ModelSerializer):
    warehouse_type = StringRelatedField()
    class Meta:
        model = WarehouseWip
        fields = ['quantity','warehouse_type']

class ProcessSerializer(ModelSerializer):
    warehousewip_set = WarehouseWipSerializer(many=True)
    class Meta:
        model= Process
        fields = ['process_name','order','process_type','product','warehousewip_set']
         

class ProductSerializer(ModelSerializer):
    ppic_warehouseproduct_related = WarehouseProductSerializer(many=True)
    ppic_process_related = ProcessSerializer(many=True)
    class Meta:
        model = Product
        fields = ['name','code','ppic_warehouseproduct_related','process','image','ppic_process_related']

class ProductOrderSerializer(ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = ProductOrder
        fields = ['ordered','delivered','product']

class ReportSalesOrderSerializer(ModelSerializer):
    productorder_set = ProductOrderSerializer(many=True)
    class Meta:
        model = SalesOrder
        fields = ['code','fixed','created','productorder_set']










