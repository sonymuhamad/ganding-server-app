from rest_framework.serializers import ModelSerializer,StringRelatedField,IntegerField,Serializer,DateField,FloatField
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User,Group,Permission

from ppic.models import MaterialRequirementPlanning,DetailMrp,Product,WarehouseProduct,Process,ProductOrder,Material,MaterialOrder,MaterialReceiptSchedule,DeliveryNoteCustomer,ProductDeliverCustomer,Operator,Machine

from marketing.models import SalesOrder,Customer

from purchasing.models import Supplier,PurchaseOrderMaterial
from .shortcuts import invalid,get_default_password
from ppic.serializer import ProductListSerializer,MaterialListReadOnlySerializer
from math import ceil



class GroupSerializer(ModelSerializer):
    '''
    a serializer for get nested groups from each user
    '''
    class Meta:
        model = Group
        fields = ['id','name']

class AccessTokenSerializer(ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ['token','expires','scope','created']
    
class UserSerializer(ModelSerializer):
    oauth2_provider_accesstoken = AccessTokenSerializer(many=True)
    groups = GroupSerializer(many=True)
    
    class Meta:
        model = User
        fields = ['id','last_login','username','email','oauth2_provider_accesstoken','groups']

class PermissionReadOnlySerializer(ModelSerializer):
    '''
    nested serializer for permission from user
    '''
    class Meta:
        model = Permission
        fields = '__all__'
        depth = 1

class UserReadOnlySerializer(ModelSerializer):
    '''
    a serializer for get and retrieve user
    '''
    groups = GroupSerializer(many=True)
    user_permissions = PermissionReadOnlySerializer(many=True)
    class Meta:
        model = User
        fields = ['id','last_login','username','email','groups','user_permissions']


class UserManagementSerializer(ModelSerializer):
    '''
    a serializer for management data user
    '''

    def create(self, validated_data):
        password = get_default_password()
        new_user = User.objects.create(username=validated_data['username'],password=password,email=validated_data['email'])

        return new_user

    class Meta:
        model = User
        fields = ['id','username','last_login','email'] 
        read_only_fields = ['last_login']

class UserGroupManagementSerializer(ModelSerializer):
    '''
    a serializer for add,and delete group from user
    '''
    class Meta:
        model = Group
        fields = '__all__'


class UserListSerializer(ModelSerializer):
    '''
    a serializer for get just list of user
    '''

    class Meta:
        model = User
        fields = ['id','username','email','last_login']

class GroupReadOnlySerializer(ModelSerializer):
    '''
    a serializer for get nested groups from each user
    '''
    number_of_user = IntegerField(read_only=True)
    user_set = UserListSerializer(many=True)
    class Meta:
        model = Group
        fields = '__all__'

'''
serializer for schedule material receipt
'''
class MaterialReceiptScheduleSerializer(ModelSerializer):

    class Meta:
        model = MaterialReceiptSchedule
        fields = ['quantity','date']

class MaterialSerializer(ModelSerializer):
    uom = StringRelatedField()
    class Meta:
        model = Material
        fields = ['name','weight','image','spec','length','width','thickness','uom']

class MaterialOrderSerializer(ModelSerializer):
    material = MaterialSerializer()
    materialreceiptschedule_set = MaterialReceiptScheduleSerializer(many=True)
    class Meta:
        model = MaterialOrder
        fields = ['ordered','arrived','material','materialreceiptschedule_set']

class PurchaseOrderMaterialSerializer(ModelSerializer):
    materialorder_set = MaterialOrderSerializer(many=True)

    class Meta:
        model = PurchaseOrderMaterial
        fields = ['code','created','materialorder_set']


class SupplierSerializer(ModelSerializer):
    '''
    plant manager -> material receipt report
    '''
    purchasing_purchaseordermaterial_related = PurchaseOrderMaterialSerializer(many=True)

    class Meta:
        model = Supplier
        fields = ['name','email','phone','address','purchasing_purchaseordermaterial_related']


class ReportOrderEachMonthReadOnlySerializer(Serializer):
    '''
    a serializer class for get total quantity order of all product each month
    '''
    order_date = DateField()
    total_order = IntegerField()

class ReportCustomerOrderReadOnlySerializer(ModelSerializer):
    '''
    a serializer class for get all customer and its total product order, and what is the most ordered product,
    sort by total product order
    '''
    customer_total_order = IntegerField()
    most_ordered_product = ProductListSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = '__all__'


class PercentageSerializer(Serializer):
    '''
    a serialzier class for get presentage of delivery timeliness
    ''' 
    percentage = IntegerField()
    total_schedule = IntegerField()
    total_schedule_on_time = IntegerField()
    unscheduled = IntegerField()

class ReportSupplierOrderReadOnlySerializer(ModelSerializer):
    '''
    a serializer class for get all supplier and its total material order, and what is the most ordered material, then sort by total material order
    '''
    supplier_total_order = IntegerField()
    most_ordered_material = MaterialListReadOnlySerializer(read_only=True)
    
    class Meta:
        model = Supplier
        fields = '__all__'


class ReportProductionReadOnlySerializer(Serializer):
    '''
    a serializer class for get data quantity production and quantity not good of production each month
    '''
    production_date = DateField()
    total_good_production = IntegerField()
    total_not_good_production = IntegerField()


class OperatorReadOnlySerializer(ModelSerializer):
    '''
    a serializer class for get all data operator and its total times production, success percentage when production, and avg of each production
    '''
    avg_production = FloatField()
    good_percentage = IntegerField()
    times_do_production = IntegerField()
    total_goods_produced = IntegerField()

    def to_representation(self, instance):
        '''
        ceil avg production
        '''

        ret = super().to_representation(instance)
        ret['avg_production'] = ceil(ret['avg_production'])

        return ret

    class Meta:
        model = Operator
        fields = '__all__'


class MachineReadOnlySerializer(ModelSerializer):
    '''
    a serializer class for get all data machine and its total times production, success percentage when produce, and avg of each do production
    '''
    avg_production = FloatField()
    good_percentage = IntegerField()
    times_do_production = IntegerField()
    total_goods_produced = IntegerField()

    
    def to_representation(self, instance):
        '''
        ceil avg production
        '''
        ret = super().to_representation(instance)
        ret['avg_production'] = ceil(ret['avg_production'])

        return ret


    class Meta:
        model = Machine
        fields = '__all__'


