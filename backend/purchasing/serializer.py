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

    
class MaterialReceiptScheduleReadOnlySerializer(ModelSerializer):
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'
        depth = 3

class MaterialOrderReadOnlySerializer(BaseMaterialOrderSerializer):
    materialreceiptschedule_set = MaterialReceiptScheduleReadOnlySerializer(many=True)
    total_receipt_schedule = serializers.IntegerField(read_only=True)
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
        instance.save()
        return instance
        
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'

class MaterialOrderManagementSerializer(BaseMaterialOrderSerializer):
    '''
    a serializer for cud material order
    '''

    def check_requirement_production(self,material:Material,product:Product):

        reqMaterial = material.ppic_requirementmaterial_related.filter(process__product__exact=product).exists()

        return reqMaterial

    def check_requrirement_production_subcont(self,material:Material,product:Product):
        reqMaterialSubcont = material.ppic_requirementmaterialsubcont_related.filter(product_subcont__product__exact=product).exists()
        
        return reqMaterialSubcont

    def validate(self, attrs):

        if attrs['purchase_order_material'].done or attrs['purchase_order_material'].closed:
            invalid('Purchase order ini telah selesai atau ditutup')
        
        supplier_from_purchase_order = attrs['purchase_order_material'].supplier
        material = attrs['material']
        supplier_from_material = material.supplier
        to_product = attrs.get('to_product',None)
        if supplier_from_material != supplier_from_purchase_order:
            invalid(f'Material {material.name} is not belong to {supplier_from_purchase_order.name}')

        if to_product is not None:
            if not self.check_requirement_production(material,to_product) and not self.check_requrirement_production_subcont(material,to_product):
                invalid(f'Material tersebut bukan untuk produksi ${to_product.name}')

        return super().validate(attrs)

    def update(self, instance, validated_data):
        
        instance.ordered = validated_data.get('ordered',instance.ordered)
        instance.price = validated_data.get('price',instance.price)
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
                    invalid('Masih ada material yang belum datang')
        
        instance.done = validated_data_done
        instance.save()
        return instance

    class Meta:
        model = PurchaseOrderMaterial
        fields = ['id','done']

class CloseStatusPurchaseOrderSerializer(ModelSerializer):
    '''
    a serialzier to change status closed of purchase order material
    '''

    def update(self, instance, validated_data):

        if not instance.done:
            invalid('Purchase order belum selesai')
        
        instance.closed = validated_data.get('closed',instance.closed)
        instance.save()
        return instance
        
    class Meta:
        model = PurchaseOrderMaterial
        fields = ['id','closed']

class PurchaseOrderManagementSerializer(ModelSerializer):

    def create(self, validated_data):
        print(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        '''
        edit code of purchase order
        '''

        if instance.done:
            invalid('Purchase order ini telah selesai atau telah ditutup')

        instance.code = validated_data.get('code',instance.code)
        instance.date = validated_data.get('date',instance.date)
        instance.tax = validated_data.get('tax',instance.tax)
        instance.description = validated_data.get('description',instance.description)
        instance.discount = validated_data.get('discount',instance.discount)
        instance.save()

        return instance

    class Meta:
        model = PurchaseOrderMaterial
        fields = '__all__'



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












