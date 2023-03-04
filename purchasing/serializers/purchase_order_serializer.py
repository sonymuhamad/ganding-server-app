from rest_framework.serializers import ModelSerializer,IntegerField,Serializer,DateField
from datetime import date

from manager.shortcuts import invalid
from purchasing.models import PurchaseOrderMaterial
from ppic.models import MaterialOrder,MaterialReceiptSchedule,Product,Material

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

class TwoDepthMaterialOrderSerializer(ModelSerializer):
    '''
    two depth material order serializer class
    '''
    
    class Meta:
        model = MaterialOrder
        fields = '__all__'
        depth = 2

class MaterialReceiptScheduleReadOnlySerializer(ModelSerializer):
    '''
    '''
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'
        depth = 3

class MaterialOrderReadOnlySerializer(TwoDepthMaterialOrderSerializer):
    '''
    '''
    materialreceiptschedule_set = MaterialReceiptScheduleReadOnlySerializer(many=True)
    total_receipt_schedule = IntegerField(read_only=True)
    
class PurchaseOrderReadOnlySerializer(ModelSerializer):
    '''
    '''
    materialorder_set = MaterialOrderReadOnlySerializer(many=True)

    class Meta:
        model = PurchaseOrderMaterial
        fields = '__all__'
        depth = 1

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

class MaterialReceiptScheduleManagementSerializer(ModelSerializer):
    '''
    a serializer for management schedule receipt of material
    '''

    def date_validation(self,scheduleDate = date.today()):
        if scheduleDate < date.today():
            invalid('Could not enter a schedule for the past')
    
    def create(self, validated_data):
        self.date_validation(validated_data.get('date',None))

        return super().create(validated_data)
    
    def validate_material_order(self,attrs):

        if attrs.arrived >= attrs.ordered:
            invalid('This order already finished')

        if attrs.purchase_order_material.done:
            invalid('This purchase order already closed')

        return attrs
    
    def update(self, instance, validated_data):
        
        if instance.fulfilled_quantity > 0:
            invalid('Cannot change a schedule that already has material arrivals')
        
        scheduleDate = validated_data.get('date',None)
        if scheduleDate != instance.date:
            self.date_validation(scheduleDate)

        instance.date = validated_data.get('date',instance.date)
        instance.quantity = validated_data.get('quantity',instance.quantity)
        instance.save()
        return instance
        
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'

class MaterialOrderManagementSerializer(ModelSerializer):
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

    class Meta:
        model = MaterialOrder
        fields = '__all__'

class MaterialUsageAndOrderSerializer(Serializer):
    '''
    a serializer fro get material usage on each month
    '''
    date = DateField()
    total_order = IntegerField(read_only=True)
    total_usage = IntegerField(read_only=True)
