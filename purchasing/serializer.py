from rest_framework.serializers import ModelSerializer
from .models import Supplier,PurchaseOrderMaterial
from rest_framework import serializers
from ppic.models import *
from manager.shortcuts import invalid
from datetime import date




class BasePurchaseOrderMaterialSerializer(ModelSerializer):
    class Meta:
        model = PurchaseOrderMaterial
        fields = '__all__'
        read_only_fields = ['created']
        depth = 1

class BaseMaterialOrderSerializer(ModelSerializer):
    class Meta:
        model = MaterialOrder
        fields = '__all__'

### purchase order material read only serializer



###########
### purchase order material management serializer




### purchase order material management serializer


class MaterialSerializer(ModelSerializer):
    '''
    nested material from supplier
    '''
    warehousematerial = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Material
        fields = '__all__'
        depth = 1

class MaterialOrderSerializer(ModelSerializer):
    '''
    nested material order from purchase order material
    '''
    class Meta:
        model = MaterialOrder
        exclude= ['purchase_order_material']
        depth = 2

class PurchaseOrderMaterialSerializer(ModelSerializer):
    '''
    nested purchase order from supplier
    '''
    number_of_material_order = serializers.IntegerField(read_only=True)
    materialorder_set = MaterialOrderSerializer(many=True)
    class Meta:
        model = PurchaseOrderMaterial
        exclude = ['supplier']

class SupplierReadOnlySerializer(ModelSerializer):
    '''
    a serializer for get supplier nested to material, purchase order -> material ordered
    '''
    ppic_material_related = MaterialSerializer(many=True)
    purchasing_purchaseordermaterial_related = PurchaseOrderMaterialSerializer(many=True)
    class Meta:
        model = Supplier
        fields ='__all__'

class RequirementMaterialListSerializer(ModelSerializer):
    '''
    a serializer class provide data requirement material used in production
    '''
    class Meta:
        model = RequirementMaterial
        exclude = ['material']
        depth = 2

class RequirementMaterialSubcontListSerializer(ModelSerializer):
    '''
    a serializer class provide data requirement material used in product subconstruction
    '''
    class Meta:
        model = RequirementMaterialSubcont
        exclude = ['material']
        depth = 2

class MaterialListSerializer(ModelSerializer):
    '''
    a serializer for get material, for add material order in detail purchase order page
    '''
    ppic_requirementmaterial_related = RequirementMaterialListSerializer(many=True)
    ppic_requirementmaterialsubcont_related = RequirementMaterialSubcontListSerializer(many=True)
    class Meta:
        model = Material
        fields = '__all__'
        depth = 1

    
    
class MaterialReceiptListSerializer(ModelSerializer):
    '''
    a serializer for get all received material,
    '''
    class Meta:
        model = MaterialReceipt
        fields = '__all__'
        depth = 3












