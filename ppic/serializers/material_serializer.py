from rest_framework.serializers import ModelSerializer,IntegerField
from django.utils import timezone

from ppic.models import Material,UnitOfMaterial,RequirementMaterial,MaterialRequirementPlanning,WarehouseMaterial,DetailMrp

from .warehouse_serializer import OneDepthWarehouseMaterialSerializer
from manager.shortcuts import invalid

class BaseMaterialSerializer(ModelSerializer):
    '''
    base material serializer class
    '''

    class Meta:
        model = Material
        fields = '__all__'
        read_only_fields = ['last_update']

class BaseMaterialRequirementPlanningSerializer(ModelSerializer):
    '''
    base mrp serializer class
    '''

    class Meta:
        model = MaterialRequirementPlanning
        fields = '__all__'

class BaseRequirementMaterialSerializer(ModelSerializer):
    '''
    base serializer class of requirement material
    '''

    class Meta:
        model = RequirementMaterial
        fields = '__all__'
        read_only_fields = ['process']

class RequirementMaterialSerializer(BaseRequirementMaterialSerializer):
    pass

class BaseUnitOfMaterialSerializer(ModelSerializer):
    '''
    base unit of material serializer class
    '''

    class Meta:
        model = UnitOfMaterial
        fields = '__all__'

class UnitOfMaterialSerializer(BaseUnitOfMaterialSerializer):
    '''
    extended unit of material
    '''

    amount_of_material = IntegerField(read_only=True)

class OneDepthMaterialNestedWarehouseSerializer(BaseMaterialSerializer):
    '''
    one depth material serializer nested to its warehouse
    '''

    warehousematerial = OneDepthWarehouseMaterialSerializer()
    total_order = IntegerField(read_only=True)

    class Meta(BaseMaterialSerializer.Meta):
        depth = 1

class TwoDepthRequirementMaterialSerializer(BaseRequirementMaterialSerializer):
    '''
    two depth requirement material serializer class
    '''

    material = OneDepthMaterialNestedWarehouseSerializer() 

    class Meta(BaseRequirementMaterialSerializer.Meta):
        depth = 2

class UnitOfMaterialNestedSerializer(UnitOfMaterialSerializer):
    '''
    unit of material serializer nested to material
    '''

    material_set = OneDepthMaterialNestedWarehouseSerializer(many=True)

class MaterialDetailSerializer(OneDepthMaterialNestedWarehouseSerializer):
    '''
    detail material serializer class
        nested to its requirement material 
    '''

    ppic_requirementmaterial_related = TwoDepthRequirementMaterialSerializer(many=True)
    rest_arrival = IntegerField(read_only=True)

class MaterialManagementSerializer(BaseMaterialSerializer):
    '''
    material serializer class for create, update data 
    '''

    def create(self, validated_data):
        instance = super().create(validated_data)
        WarehouseMaterial.objects.create(quantity=0,material=instance)
        return instance 
    
    def update(self, instance, validated_data):
        req_material = instance.ppic_requirementmaterial_related.all()
        wh_material = instance.warehousematerial

        if len(req_material) > 0:
            invalid('Tidak bisa mengubah data material yang menjadi kebutuhan produksi')
        if wh_material.quantity > 0:
            invalid('Tidak bisa mengubah data material yang memiliki stok di gudang')
        
        instance.last_update = timezone.now()
        instance.save(update_fields=["last_update"])

        return super().update(instance, validated_data)

class DetailMrpSerializer(ModelSerializer):
    '''
    '''
    
    class Meta:
        model = DetailMrp
        fields = '__all__'

class OneDepthDetailMrpSerializer(DetailMrpSerializer):
    '''
    '''
    class Meta(DetailMrpSerializer.Meta):
        depth = 1

class TwoDepthMrpSerializer(BaseMaterialRequirementPlanningSerializer):
    '''
    two depth material requirement planning serializer class
        extend to detailmrp and material 
    '''
    detailmrp_set = OneDepthDetailMrpSerializer(many=True)
    material = OneDepthMaterialNestedWarehouseSerializer()

    class Meta(BaseMaterialRequirementPlanningSerializer.Meta):
        depth = 2

class MrpManagementSerializer(BaseMaterialRequirementPlanningSerializer):
    '''
    mrp serializer class for create, update data
    '''
    detailmrp_set = DetailMrpSerializer(many=True)

    def validate_detailmrp_set(self,attrs):
        quantity_req = self.initial_data['quantity']
        temp = 0
        for detailmrp in attrs:
            temp += detailmrp['quantity']
        if temp > quantity_req:
            invalid('Jumlah kebutuhan berlebih dari jumlah permintaan')

        return attrs
    
    def update(self, instance, validated_data):
        detailmrps = validated_data.pop('detailmrp_set')
        len_detailmrps = len(detailmrps)

        instance_detailmrps = instance.detailmrp_set.all()
        len_instance_mrps = len(instance_detailmrps)
        
        instance.quantity = validated_data['quantity']
        instance.material = validated_data['material']
        instance.last_update = timezone.now()
        instance.save()
        
        deleted_detailMrp = []

        j = 0
        for i in range(len_detailmrps):
            if i > len_instance_mrps - 1:
                DetailMrp.objects.create(**detailmrps[i],mrp=instance)
            else:
                instance_detailmrps[i].quantity = detailmrps[i]['quantity']
                instance_detailmrps[i].quantity_production = detailmrps[i]['quantity_production']
                instance_detailmrps[i].product = detailmrps[i]['product']
                instance_detailmrps[i].save()
            j+=1
        
        deleted_detailMrp = deleted_detailMrp[:] + instance_detailmrps[j:]
        print(deleted_detailMrp)
        for deletedMrp in deleted_detailMrp:
            deletedMrp.delete()

        return instance

    def create(self, validated_data):
        detailmrps = validated_data.pop('detailmrp_set')
        instance = super().create(validated_data)
        
        for detailmrp in detailmrps:
            DetailMrp.objects.create(**detailmrp,mrp=instance)

        return instance

