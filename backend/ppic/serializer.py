from ast import Mod
from rest_framework.serializers import ModelSerializer
from .models import DeliveryNoteCustomer, DeliveryNoteSubcont, DeliverySchedule, DetailMrp, Driver, Material, MaterialOrder, MaterialReceipt, MaterialRequirementPlanning, Process, Product, ProductDeliverCustomer, ProductDeliverSubcont, ProductOrder, RequirementMaterial, RequirementProduct, Vehicle, WarehouseMaterial, WarehouseProduct,MaterialReceiptSchedule,DeliveryNoteMaterial
from . import models

class DriverSerializer(ModelSerializer):
    class Meta:
        model = Driver
        fields = ['name']

class VehicleSerializer(ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['licence_part_number']


###### Serializers for product

class ProductSerializer(ModelSerializer):

    class Meta:
        model = Product
        fields = ['name','customer','type','process','price','code','weight','image']


class ProductOrderSerializer(ModelSerializer):
    class Meta:
        model = ProductOrder
        fields = ['sales_order','product','ordered','delivered']

class WarehouseSerializer(ModelSerializer):
    class Meta:
        model = WarehouseProduct
        fields = ['warehouse_type','product','quantity']

class DeliveryScheduleSerializer(ModelSerializer):
    class Meta:
        model = DeliverySchedule
        fields = ['product_order','date','quantity']

class RequirementProductSerializer(ModelSerializer):
    class Meta:
        model = RequirementProduct
        fields = ['process','product','conversion']

class ProcessSerializer(ModelSerializer):
    class Meta:
        model = Process
        fields = ['process_type','process_name','order','product']

class DeliveryNoteSubcontSerializer(ModelSerializer):
    class Meta:
        model = DeliveryNoteSubcont
        fields = ['driver','vehicle','code','created','note','supplier']

class ProductDeliverSubcontSerializer(ModelSerializer):
    class Meta:
        model = ProductDeliverSubcont
        fields = ['product','quantity','deliver_note_subcont']

class DeliveryNoteCustomerSerializer(ModelSerializer):
    class Meta:
        model = DeliveryNoteCustomer
        fields = ['driver','vehicle','code','created','note','customer']

class ProductDeliverCustomerSerializer(ModelSerializer):
    class Meta:
        model = ProductDeliverCustomer
        fields = ['product_order','quantity','delivery_note_customer','paid']





####### Serializers for material


class MaterialSerializer(ModelSerializer):

    class Meta:
        model = Material
        fields = ['name','spec','length','width','thickness','uom','supplier','weight','image']

class MrpSerializer(ModelSerializer):

    class Meta:
        model = MaterialRequirementPlanning
        fields = ['material','quantity']

class DetailMrpSerializer(ModelSerializer):

    class Meta:
        model = DetailMrp
        fields = ['product','mrp','quantity_production']

class WarehouseMaterialSerializer(ModelSerializer):
    class Meta:
        model = WarehouseMaterial
        fields = ['warehouse_type','material','quantity']

class RequirementMaterialSerializer(ModelSerializer):
    class Meta:
        model = RequirementMaterial
        fields = ['process','material','conversion']


class MaterialReceiptSchedule(ModelSerializer):
    class Meta:
        model = MaterialReceiptSchedule
        fields = ['material_order','date','quantity']

class MaterialOrderSerializer(ModelSerializer):
    class Meta:
        model = MaterialOrder
        fields = ['purchase_order_material','orderd','arrived','material']

class MaterialReceiptSerializer(ModelSerializer):
    class Meta:
        model = MaterialReceipt
        fields = ['quantity','delivery_note_material','material_order']

class DeliveryNoteMaterial(ModelSerializer):
    class Meta:
        model = DeliveryNoteMaterial
        fields = ['code','created','note','supplier']













