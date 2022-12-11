from rest_framework.serializers import ModelSerializer,StringRelatedField
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User,Group

from ppic.models import MaterialRequirementPlanning,DetailMrp,Product,WarehouseProduct,Process,ProductOrder,Material,MaterialOrder,MaterialReceiptSchedule,DeliveryNoteCustomer,ProductDeliverCustomer

from marketing.models import SalesOrder,Customer

from purchasing.models import Supplier,PurchaseOrderMaterial


class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = ['id','name']

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

'''
serializer for material requirement planning
'''

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












