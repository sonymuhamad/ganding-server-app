from rest_framework.serializers import ModelSerializer,StringRelatedField,IntegerField,Serializer,DateField
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User,Group,Permission

from ppic.models import MaterialRequirementPlanning,DetailMrp,Product,WarehouseProduct,Process,ProductOrder,Material,MaterialOrder,MaterialReceiptSchedule,DeliveryNoteCustomer,ProductDeliverCustomer

from marketing.models import SalesOrder,Customer

from purchasing.models import Supplier,PurchaseOrderMaterial
from .shortcuts import invalid,get_default_password
from ppic.serializer import ProductListSerializer,MaterialListReadOnlySerializer



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



class DetailMrpSerializer(ModelSerializer):
    
    class Meta:
        model = DetailMrp
        fields = ['quantity','quantity_production','product']
        depth = 1

class ReportMrpSerializer(ModelSerializer):
    '''
    plant manager -> report mrp
    '''
    detailmrp_set =  DetailMrpSerializer(many=True) #related name

    class Meta:
        model = MaterialRequirementPlanning
        fields = ['material','quantity','detailmrp_set']
        depth = 1


'''
serializer for sales order
'''

class WarehouseProductSerializer(ModelSerializer):
    warehouse_type = StringRelatedField()
    class Meta:
        model = WarehouseProduct
        fields = ['quantity','warehouse_type']

class ProcessSerializer(ModelSerializer):
    warehouseproduct_set = WarehouseProductSerializer(many=True)
    class Meta:
        model= Process
        fields = ['process_name','order','process_type','product','warehouseproduct_set']
         

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

class CustomerSalesOrderSerializer(ModelSerializer):
    '''
    plant manager -> report sales order -> data product
    '''
    marketing_salesorder_related = ReportSalesOrderSerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id','name','email','phone','address','marketing_salesorder_related']


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



'''
serializer for delivery note
'''
class ProductOrderSerializer(ModelSerializer):
    product = StringRelatedField()
    class Meta:
        model = ProductOrder
        fields = ['ordered','delivered','product','sales_order']

class ProductDeliveryNoteCustomerSerializer(ModelSerializer):

    class Meta:
        model = ProductDeliverCustomer
        fields = ['quantity','paid','product_order']
        depth = 2

class DeliveryNoteCustomerSerializer(ModelSerializer):
    productdelivercustomer_set = ProductDeliveryNoteCustomerSerializer(many=True)
    class Meta:
        model = DeliveryNoteCustomer
        fields = ['code','created','driver','vehicle','productdelivercustomer_set']
        depth = 1


class CustomerDeliveryNoteSerializer(ModelSerializer):
    ppic_deliverynotecustomer_related = DeliveryNoteCustomerSerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id','name','email','phone','address','ppic_deliverynotecustomer_related']



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


