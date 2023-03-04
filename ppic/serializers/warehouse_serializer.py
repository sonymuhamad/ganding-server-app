from rest_framework.serializers import ModelSerializer,CharField
from django.utils import timezone
from ppic.models import WarehouseMaterial,WarehouseProduct,WarehouseType,ReceiptSubcontSchedule,MaterialReceiptSchedule,ReceiptNoteSubcont,SubcontReceipt,DeliveryNoteMaterial,MaterialReceipt
from manager.shortcuts import invalid

class BaseWarehouseProductSerializer(ModelSerializer):
    '''
    base serializer class for warehouse product
    '''

    class Meta:
        model = WarehouseProduct
        fields = '__all__'

class BaseWarehouseMaterialSerializer(ModelSerializer):
    '''
    base serializer class for warehouse material
    '''

    class Meta:
        model = WarehouseMaterial
        fields = '__all__'

class OneDepthWarehouseProductSerializer(BaseWarehouseProductSerializer):
    '''
    one depth serializer class of warehouse product
    '''

    class Meta(BaseWarehouseProductSerializer.Meta):
        depth = 1

class TwoDepthWarehouseProductSerializer(BaseWarehouseProductSerializer):
    '''
    two depth warehouse product serializer class
    '''

    class Meta(BaseWarehouseProductSerializer.Meta):
        depth = 2

class OneDepthWarehouseMaterialSerializer(BaseWarehouseMaterialSerializer):
    '''
    one depth warehouse material serializer
    '''

    class Meta(BaseWarehouseMaterialSerializer.Meta):
        depth = 1

class WarehouseMaterialManagementSerializer(BaseWarehouseMaterialSerializer):
    '''
    warehouse material serializer class for update data
    '''    
    def validate_quantity(self,attrs):
        if attrs < 0:
            invalid('Cannot set stock material to negative number')
        return attrs

    class Meta(BaseWarehouseMaterialSerializer.Meta):
        read_only_fields = ['material']

class WarehouseProductManagementSerializer(BaseWarehouseProductSerializer):
    '''
    serializer for update stock product eg: wip,subcont,finishgood
    '''

    def validate_quantity(self,attrs):
        if attrs < 0 :
            invalid('Cannot set stock to negative number')
            
        return attrs

    class Meta(BaseWarehouseProductSerializer.Meta):
        read_only_fields = ['process','product','warehouse_type']

class WarehouseTypeReadOnlySerializer(ModelSerializer):
    '''    
    '''
    warehouseproduct_set = TwoDepthWarehouseProductSerializer(many=True)
    class Meta:
        model = WarehouseType
        fields = '__all__'


class ThreeDepthReceiptSubcontScheduleSerializer(ModelSerializer):
    '''
    a serializer for get list schedule of product in subconstruction
    '''
    class Meta:
        model = ReceiptSubcontSchedule
        fields = '__all__'
        depth = 3

class BaseMaterialReceiptScheduleSerializer(ModelSerializer):
    '''
    base material receipt schedule serialize
    '''

    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'

class ThreeDepthMaterialReceiptScheduleSerializer(BaseMaterialReceiptScheduleSerializer):
    '''
    '''
    class Meta(BaseMaterialReceiptScheduleSerializer.Meta):
        depth = 3


class BaseReceiptNoteSubcontSerializer(ModelSerializer):
    '''
    a serializer for crud receipt note subcont
    '''
    note = CharField(allow_blank=True)
    
    def update(self, instance, validated_data):

        instance.code = validated_data.get('code',instance.code)
        instance.note = validated_data.get('note',instance.note)
        instance.date = validated_data.get('date',instance.date)
        instance.image = validated_data.get('image',instance.image)
        instance.last_update = timezone.now()
        instance.save()

        return instance

    class Meta:
        model = ReceiptNoteSubcont
        fields = '__all__'
        read_only_fields = ['last_update']

class ThreeDepthSubcontReceiptSerializer(ModelSerializer):
    '''
    a nested serializer for get all product received from receipt note
    '''
   
    class Meta:
        model = SubcontReceipt
        fields ='__all__'
        depth = 3

class OneDepthReceiptNoteSubcontSerializer(BaseReceiptNoteSubcontSerializer):
    '''
    a serializer for get and retrieve receipt note subcont
    '''
    subcontreceipt_set = ThreeDepthSubcontReceiptSerializer(many=True)
    
    class Meta(BaseReceiptNoteSubcontSerializer.Meta):
        depth = 1

class DeliveryNoteMaterialSerializer(ModelSerializer):
    '''
    '''
    note = CharField(allow_blank=True)

    def update(self, instance, validated_data):

        instance.code = validated_data.get('code',instance.code)
        instance.note = validated_data.get('note',instance.note)
        instance.image = validated_data.get('image',instance.image)
        instance.last_update = timezone.now()
        instance.date = validated_data.get('date',instance.date)

        instance.save()

        return instance

    class Meta:
        model = DeliveryNoteMaterial
        fields = '__all__'
        read_only_fields = ['last_update']

class MaterialReceiptReadOnlySerializer(ModelSerializer):
    '''
    '''
    class Meta:
        model = MaterialReceipt
        fields = '__all__'
        depth = 3

class DeliveryNoteMaterialReadOnlySerializer(DeliveryNoteMaterialSerializer):
    '''
    '''
    materialreceipt_set = MaterialReceiptReadOnlySerializer(many=True)

    class Meta(DeliveryNoteMaterialSerializer.Meta):
        depth = 1

class SubcontReceiptManagementSerializer(ModelSerializer):
    '''
    a serializer for cud (create, read, update) subcont receipt or product received from receipt note subconstruction
    '''
    def validate_product_subcont(self,attrs):
        
        subcontReceived = attrs.subcontreceipt_set.all()
        tempQuantity = 0
        quantityShipped = attrs.quantity

        for subcontReceived in attrs.subcontreceipt_set.all():
            tempQuantity += subcontReceived.quantity
        
        if tempQuantity >= quantityShipped:
            invalid('All products that sent to the sub-construction have been received')

        return attrs
    
    def validate(self, attrs):

        supplier_product_subcont = attrs['product_subcont'].deliver_note_subcont.supplier
        supplierReceiptNote = attrs['receipt_note'].supplier
        delivered_product_subcont = attrs['product_subcont']
        
        productSubcont = delivered_product_subcont.product

        if supplierReceiptNote != supplier_product_subcont:
            ## check if supplier from receipt note is the same with supplier from product in subconstruction
            
            invalid(f'Subconstruction delivery of product {productSubcont.name} is not with {supplier_product_subcont.name}')

        return super().validate(attrs)

    def create(self, validated_data):
        
        product_shipped_subconstruction = validated_data['product_subcont']
        process = product_shipped_subconstruction.process
        quantityProduction = validated_data['quantity'] + validated_data['quantity_not_good']

        whProduct = process.warehouseproduct_set.exclude(warehouse_type=2).get()
        whSubcont = process.warehouseproduct_set.filter(warehouse_type=2).get()
        
        if quantityProduction > whSubcont.quantity:
            ## check availability for product in warehouse

            invalid(f'Quantity product received greater than product in subconstruction')

        whProduct.quantity += validated_data['quantity']
        whSubcont.quantity -= (quantityProduction)
        
        schedules = validated_data.get('schedules',None)
        if schedules is not None:
            ## if material receipt inputted by schedule, then set schedule

            schedules.fulfilled_quantity = validated_data['quantity']
            schedules.save()

        whProduct.save()
        whSubcont.save()

        return super().create(validated_data)
    
    
    def update(self, instance, validated_data):

        instance_product_shipped_subconstruction = instance.product_subcont
        process = instance_product_shipped_subconstruction.process
        
        whProduct = process.warehouseproduct_set.exclude(warehouse_type=2).get()
        whSubcont = process.warehouseproduct_set.filter(warehouse_type=2).get()
        
        if validated_data['quantity'] > instance.quantity:
            ## if new quantity to update is greater than previous, check availability for product in warehouse

            rest_product_to_received = validated_data['quantity'] - instance.quantity
            if rest_product_to_received > whSubcont.quantity:
                invalid(f'Quantity product received greater than product in subconstruction')

        whProduct.quantity -= instance.quantity 
        whSubcont.quantity += (instance.quantity + instance.quantity_not_good)

        instance_schedule = instance.schedules

        if whProduct.quantity < 0:
            invalid('Update failed, probably because this product has been used in production')
        
        if instance_product_shipped_subconstruction != validated_data['product_subcont']:
            invalid('Update failed, cannot change product subconstruction')
        
        whProduct.quantity += validated_data['quantity']
        whSubcont.quantity -= (validated_data['quantity']+validated_data['quantity_not_good'])

        if instance_schedule is not None:
            instance_schedule.fulfilled_quantity -= instance.quantity
            instance_schedule.fulfilled_quantity += validated_data['quantity']
            instance_schedule.save()

        
        validated_data.pop('schedules',None)
        
        whProduct.save()
        whSubcont.save()

        return super().update(instance, validated_data)
    
    class Meta:
        model = SubcontReceipt
        fields = '__all__'

class MaterialReceiptManagementSerializer(ModelSerializer):
    
    def validate_material_order(self,attrs):
        if attrs.arrived >= attrs.ordered:
                invalid('Semua material sudah datang')
        
        return attrs
    
    def validate(self, attrs):

        supplierDeliveryNoteMaterial = attrs['delivery_note_material'].supplier
        supplierPurchaseOrder = attrs['material_order'].purchase_order_material.supplier
        material = attrs['material_order'].material

        if supplierPurchaseOrder != supplierDeliveryNoteMaterial or material.supplier != supplierDeliveryNoteMaterial:
            invalid(f'{material.name} is not belongs to {supplierDeliveryNoteMaterial.name}')

        return super().validate(attrs)

    def create(self, validated_data):
        
        material_order = validated_data['material_order']
        material_order.arrived += validated_data['quantity']
        whmaterial = material_order.material.warehousematerial
        whmaterial.quantity += validated_data['quantity']
        
        schedules = validated_data.get('schedules',None)
        if schedules is not None:
            ## if material receipt inputted by schedule, then set schedule

            schedules.fulfilled_quantity = validated_data['quantity']
            schedules.save()

        whmaterial.save()
        material_order.save()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance_mo = instance.material_order
        instance_wh = instance_mo.material.warehousematerial

        instance_mo.arrived -= instance.quantity
        instance_wh.quantity -= instance.quantity
        instance_schedule = instance.schedules

        if instance_wh.quantity < 0:
            invalid('Edit failed, probably material already used in production')
        
        if instance.material_order != validated_data['material_order']:
            invalid('Update failed, cannot change material from material receipt')
        
        instance_mo.arrived += validated_data['quantity']
        instance_wh.quantity += validated_data['quantity']
        
        if instance_schedule is not None:
            instance_schedule.fulfilled_quantity -= instance.quantity
            instance_schedule.fulfilled_quantity += validated_data['quantity']
            instance_schedule.save()

        validated_data.pop('schedules',None)

        instance_mo.save()
        instance_wh.save()

        return super().update(instance, validated_data)

    class Meta:
        model = MaterialReceipt
        fields = '__all__'
