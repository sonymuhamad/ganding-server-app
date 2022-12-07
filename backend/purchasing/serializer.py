from rest_framework.serializers import ModelSerializer
from .models import Supplier,PurchaseOrderMaterial
from rest_framework import serializers
from ppic.models import *
from manager.shortcuts import invalid
from datetime import date



class BaseSupplierSerializer(ModelSerializer):
    '''
    a serializer for crud supplier
    '''
    number_of_material = serializers.IntegerField(read_only=True)
    number_of_purchase_order = serializers.IntegerField(read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

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
    ppic_materialrequirementplanning_related = MrpReadOnlySerializer(many=True)

    class Meta:
        model = Material
        fields = '__all__'
        
class SupplierMrpReadOnlySerializer(BaseSupplierSerializer):
    '''
    get
    '''
    ppic_material_related = MaterialReadOnlySerializer(many=True)
    class Meta(BaseSupplierSerializer.Meta):
        fields = '__all__'

### material requirement planning read only serializer


############
### purchase order material read only serializer

class MaterialReceiptScheduleReadOnlySerializer(ModelSerializer):
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'
        depth = 3

class MaterialOrderReadOnlySerializer(BaseMaterialOrderSerializer):
    class Meta(BaseMaterialOrderSerializer.Meta):
        depth = 2

class PurchaseOrderReadOnlySerializer(BasePurchaseOrderMaterialSerializer):
    materialorder_set = MaterialOrderReadOnlySerializer(many=True)

    class Meta(BasePurchaseOrderMaterialSerializer.Meta):
        pass

class SupplierPurchaseOrderReadOnlySerializer(BaseSupplierSerializer):
    purchasing_purchaseordermaterial_related = PurchaseOrderReadOnlySerializer(many=True)
    class Meta(BaseSupplierSerializer.Meta):
        pass

### purchase order material read only serializer



###########
### purchase order material management serializer


class MaterialReceiptScheduleManagementSerializer(ModelSerializer):
    '''
    a serializer for management schedule receipt of material
    '''
    def validate_date(self,attrs):
        
        if attrs < date.today():
            invalid('Could not enter a schedule for the past')
        
        return attrs
    
    def validate_material_order(self,attrs):

        if attrs.arrived >= attrs.ordered:
            invalid('This order already finished')

        if attrs.purchase_order_material.done:
            invalid('This purchase order already closed')

        return attrs
    
    def update(self, instance, validated_data):
        
        if instance.fulfilled_quantity > 0:
            invalid('Cannot change a schedule that already has material arrivals')
        
        instance.date = validated_data.get('date',instance.date)
        instance.quantity = validated_data.get('quantity',instance.quantity)
        return instance
        
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'

class MaterialOrderManagementSerializer(BaseMaterialOrderSerializer):
    '''
    a serializer for cud material order
    '''
    def validate(self, attrs):

        if attrs['purchase_order_material'].done:
            invalid('This purchase order already closed')
        
        supplier_from_purchase_order = attrs['purchase_order_material'].supplier
        material = attrs['material']
        supplier_from_material = material.supplier

        if supplier_from_material != supplier_from_purchase_order:
            invalid(f'Material {material.name} is not belong to {supplier_from_purchase_order.name}')
    
        return super().validate(attrs)

    def update(self, instance, validated_data):
        
        instance.ordered = validated_data.get('ordered',instance.ordered)
        if instance.ordered <= instance.arrived:
            instance.done = True
        instance.save()
        return instance

    class Meta(BaseMaterialOrderSerializer.Meta):
        pass

class StatusPurchaseOrderManagementSerializer(ModelSerializer):
    '''
    a serializer to handle just status changed of purchase order material
    '''

    def update(self, instance, validated_data):
        '''
        just update status of purchase order
        '''
        validated_data_done = validated_data.get('done')
        if validated_data_done:
            for mo in instance.materialorder_set.all():
                ## recheck all material order is already completed
                
                if mo.ordered > mo.arrived:
                    invalid('Cannot change status purchase order material to Complete, due to there are still orders in progress')
        
        instance.done = validated_data_done
        instance.save()
        return instance

    class Meta:
        model = PurchaseOrderMaterial
        fields = ['id','done']

class PurchaseOrderManagementSerializer(BasePurchaseOrderMaterialSerializer):


    def update(self, instance, validated_data):
        '''
        edit code of purchase order
        '''

        if instance.done:
            invalid('This purchase order already done')

        instance.code = validated_data.get('code',instance.code)
        instance.date = validated_data.get('date',instance.date)

        instance.save()
        return instance

    class Meta(BasePurchaseOrderMaterialSerializer.Meta):
        pass



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

class MaterialListSerializer(ModelSerializer):
    '''
    a serializer for get material, for add material order in detail purchase order page
    '''
    class Meta:
        model = Material
        fields = '__all__'
        depth = 1

class MaterialUsageAndOrderSerializer(serializers.Serializer):
    '''
    a serializer fro get material usage on each month
    '''
    date = serializers.DateField()
    total_order = serializers.IntegerField(read_only=True)
    total_usage = serializers.IntegerField(read_only=True)
    
    
class MaterialReceiptListSerializer(ModelSerializer):
    '''
    a serializer for get all received material,
    '''
    class Meta:
        model = MaterialReceipt
        fields = '__all__'
        depth = 3













