from rest_framework.serializers import ModelSerializer,StringRelatedField
from .models import Supplier,PurchaseOrderMaterial

from ppic.models import MaterialRequirementPlanning,Material,MaterialOrder,DetailMrp,MaterialReceiptSchedule

class SupplierSerializer(ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['name','email','phone','address']

class PurchaseOrderMaterialSerializer(ModelSerializer):
    class Meta:
        model = PurchaseOrderMaterial
        fields = ['code','supplier']


### material requirement planning read only serializer

class DetailMrpReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    class Meta:
        model = DetailMrp
        fields = ['id','quantity','quantity_production','product']
        depth = 1

class MrpReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    detailmrp_set = DetailMrpReadOnlySerializer(many=True)
    class Meta:
        model = MaterialRequirementPlanning
        fields = ['id','quantity','detailmrp_set']


class MaterialReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    uom = StringRelatedField()
    materialrequirementplanning_set = MrpReadOnlySerializer(many=True)

    class Meta:
        model = Material
        fields = ['id','name','spec','length','width','thickness','uom','weight','image','materialrequirementplanning_set']
        
class SupplierReadOnlySerializer(ModelSerializer):
    '''
    get
    '''
    ppic_material_related = MaterialReadOnlySerializer(many=True)

    class Meta:
        model = Supplier
        fields = ['id','name','email','phone','address','ppic_material_related']

### material requirement planning read only serializer




