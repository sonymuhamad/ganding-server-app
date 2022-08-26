from rest_framework.serializers import ModelSerializer,StringRelatedField,ValidationError
from .models import Supplier,PurchaseOrderMaterial

from ppic.models import MaterialRequirementPlanning,Material,MaterialOrder,DetailMrp,MaterialReceiptSchedule

class BaseSupplierSerializer(ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class BasePurchaseOrderMaterialSerializer(ModelSerializer):
    class Meta:
        model = PurchaseOrderMaterial
        fields = '__all__'

class BaseMaterialOrderSerializer(ModelSerializer):
    class Meta:
        model = MaterialOrder
        fields = '__all__'

class BaseMaterialReceiptScheduleSerializer(ModelSerializer):
    class Meta:
        model = MaterialReceiptSchedule
        exclude = ['material_order']


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
    ppic_materialrequirementplanning_related = MrpReadOnlySerializer(many=True)

    class Meta:
        model = Material
        fields = ['id','name','spec','length','width','thickness','uom','weight','image','ppic_materialrequirementplanning_related']
        
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

class MaterialReceiptScheduleReadOnlySerializer(BaseMaterialReceiptScheduleSerializer):
    class Meta(BaseMaterialReceiptScheduleSerializer.Meta):
        pass

class MaterialOrderReadOnlySerializer(BaseMaterialOrderSerializer):
    materialreceiptschedule_set = MaterialReceiptScheduleReadOnlySerializer(many=True)
    class Meta(BaseMaterialOrderSerializer.Meta):
        depth = 1

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


class MaterialReceiptScheduleManagementSerializer(BaseMaterialReceiptScheduleSerializer):
    class Meta(BaseMaterialReceiptScheduleSerializer.Meta):
        pass

class MaterialOrderManagementSerializer(BaseMaterialOrderSerializer):
    materialreceiptschedule_set = MaterialReceiptScheduleManagementSerializer(many=True)
    
    def validate(self, attrs):
        done = attrs.get('done',None)

        if done is True:
            raise ValidationError('Material order sudah selesai, data tidak bisa berubah')

        ordered = attrs['ordered']
        arrived = attrs.get('arrived',None)
        
        if arrived is None or arrived <= ordered:
            return super().validate(attrs)

        elif ordered < arrived:
            raise ValidationError('Jumlah kedatangan material melebihi pesanan material')


    def validate_materialreceiptschedule_set(self,attrs):
        
        initial_data = self.initial_data
        count = 0
        temp = 0
        for schedule in attrs:
            temp += schedule['quantity']
        if temp > initial_data['ordered']:
            raise ValidationError(f'Jumlah material pada jadwal kedatangan melebihi jumlah material pada pesanan {count}')
        count += 1
        
        return attrs

    def create(self, validated_data):
        schedules = validated_data.pop('materialreceiptschedule_set')
        instance_mo = MaterialOrder.objects.create(**validated_data)
        bulk_schedule = []

        for schedule in schedules:
            bulk_schedule.append(MaterialReceiptSchedule(**schedule,material_order=instance_mo))
        
        MaterialReceiptSchedule.objects.bulk_create(bulk_schedule)

        return instance_mo

    def update(self, instance, validated_data):
        data_schedules = validated_data.pop('materialreceiptschedule_set')
        len_data_schedule = len(data_schedules)
        deleted_schedule = []
        inserted_schedule = []
        updated_schedule = []

        instance_schedules = instance.materialreceiptschedule_set.all()
        len_instance_schedule = len(instance_schedules) - 1

        instance.ordered,instance.arrived,instance.material = validated_data['ordered'],validated_data['arrived'],validated_data['material']

        for i in range(len_data_schedule):
            if i > len_instance_schedule:
                inserted_schedule(MaterialReceiptSchedule(**data_schedules[i],material_order=instance))
            else:
                instance_schedules[i].quantity = data_schedules[i]['quantity']
                instance_schedules[i].date = data_schedules[i]['date']
                updated_schedule.append(instance_schedules[i])

        deleted_schedule = deleted_schedule[:] + instance_schedules[i+1:]


        MaterialReceiptSchedule.objects.bulk_create(inserted_schedule)
        MaterialReceiptSchedule.objects.bulk_update(updated_schedule,['quantity','date'])

        for schedule in deleted_schedule:
            schedule.delete()

        return super().update(instance, validated_data)

    class Meta(BaseMaterialOrderSerializer.Meta):
        pass

class PurchaseOrderManagementSerializer(BasePurchaseOrderMaterialSerializer):
    materialorder_set = MaterialOrderManagementSerializer(many=True)

    def validate(self, attrs):

        status = attrs.get('done',None)
        
        if status is None or status is True:
            return super().validate(attrs)
        else:
            raise ValidationError('Purchase order tersebut sudah selesai')
            
    def validate_materialorder_set(self,attrs):
        
        count = 0

        for materialorder in attrs:
            temp = 0
            for schedule in materialorder['materialreceiptschedule_set']:
                temp += schedule['quantity']
            if temp > materialorder['ordered']:
                raise ValidationError(f'Jumlah material pada jadwal kedatangan melebihi jumlah material pada pesanan {count}')
            count += 1
        return attrs

    def create(self, validated_data):
        material_orders = validated_data.pop('materialorder_set')
        instance_po = PurchaseOrderMaterial.objects.create(**validated_data)
        bulk_schedule = []

        for material_order in material_orders:
            schedules = material_order.pop('materialreceiptschedule_set')
            instance_mo = MaterialOrder.objects.create(**material_order,purchase_order_material=instance_po)
            for schedule in schedules:
                bulk_schedule.append(MaterialReceiptSchedule(**schedule,material_order=instance_mo))
        
        MaterialReceiptSchedule.objects.bulk_create(bulk_schedule)
        return instance_po 
        
    
    def update(self, instance, validated_data):
        '''
        edit code of purchase order
        '''

        instance.code = validated_data['code']
        instance.save()

        return instance

    class Meta(BasePurchaseOrderMaterialSerializer.Meta):
        pass



### purchase order material management serializer



















