from rest_framework.serializers import ModelSerializer,StringRelatedField,ValidationError

# from .models import DeliveryNoteCustomer, DeliveryNoteSubcont, DeliverySchedule, DetailMrp, Driver, Material, MaterialOrder, MaterialReceipt, MaterialRequirementPlanning, Process, Product, ProductDeliverCustomer, ProductDeliverSubcont, ProductOrder, RequirementMaterial, RequirementProduct, Vehicle, WarehouseMaterial, WarehouseProduct,MaterialReceiptSchedule,DeliveryNoteMaterial

from .models import *
from marketing.models import Customer
from manager.shortcuts import invalid

class DriverSerializer(ModelSerializer):
    class Meta:
        model = Driver
        fields = ['name']

class VehicleSerializer(ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['licence_part_number']


##################
#### Product Read Only Seriz
class WarehouseProductReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseProduct
        fields = ['id','quantity','warehouse_type']
        depth = 1

class RequirementMaterialReadOnlySerializer(ModelSerializer):
    class Meta:
        model = RequirementMaterial
        fields = ['id','conversion','material']
        depth = 1

class RequirementProductReadOnlySerializer(ModelSerializer):
    class Meta:
        model = RequirementProduct
        fields = ['id','conversion','product']
        depth = 1

class ProcessReadOnlySerializer(ModelSerializer):
    warehouseproduct_set = WarehouseProductReadOnlySerializer(many=True)
    requirementproduct_set = RequirementProductReadOnlySerializer(many=True)
    requirementmaterial_set = RequirementMaterialReadOnlySerializer(many=True)

    class Meta:
        model = Process
        fields = ['id','process_name','order','process_type','warehouseproduct_set','requirementproduct_set','requirementmaterial_set']
        depth = 1

class ProductReadOnlySerializer(ModelSerializer):
    ppic_process_related = ProcessReadOnlySerializer(many=True)

    class Meta:
        model = Product
        fields = ['id','code','name','weight','image','process','price','ppic_process_related','type']
        depth = 1

class ProductCustomerReadOnlySerializer(ModelSerializer):
    ppic_product_related = ProductReadOnlySerializer(many=True)

    class Meta:
        model = Customer
        fields = ['id','name','email','phone','address','ppic_product_related']

#### Product read only seriz
######



#######
### product management seriz

class WarehouseProductManagementSerializer(ModelSerializer):
    class Meta:
        model = WarehouseProduct
        fields = '__all__'

class RequirementMaterialManagementSerializer(ModelSerializer):
    class Meta:
        model = RequirementMaterial
        exclude = ['process']

class RequirementProductManagementSerializer(ModelSerializer):
    class Meta:
        model = RequirementProduct
        exclude = ['process']

class ProcessManagementSerializer(ModelSerializer):
    
    requirementproduct_set = RequirementProductManagementSerializer(many=True)
    requirementmaterial_set = RequirementMaterialManagementSerializer(many=True)
    class Meta:
        model = Process
        fields = ['id','process_name','process_type','requirementproduct_set','requirementmaterial_set']

class ProductManagementSerializer(ModelSerializer):
    ppic_process_related = ProcessManagementSerializer(many=True)

    def validate_ppic_process_related(self,attrs):
        len_attrs = len(attrs)
        if len_attrs == 0:
            invalid('Product setidaknya memiliki satu proses')
        
        requirementmaterial = attrs[0]['requirementmaterial_set']
        len_requirement_material = len(requirementmaterial)
        if len_requirement_material == 0:
            invalid('Proses pertama setidaknya memiliki satu kebutuhan material')
        
        return attrs

    def update(self, instance, validated_data):
        '''
        update product
        '''
        return super().update(instance, validated_data)

    def create(self, validated_data):
        '''
        create product -> process -> requirement material & requirement product & warehouse product
        '''
        many_process = validated_data.pop('ppic_process_related')
        len_process = len(many_process)

        req_material_bulk = []
        req_product_bulk = []
        whproduct_bulk = []
        order = 1

        instance_product = Product.objects.create(**validated_data,process=len_process)
        wh_type_subcont = WarehouseType.objects.get(id=2)

        for each_process in many_process:
            many_req_material = each_process.pop('requirementmaterial_set')
            many_req_product = each_process.pop('requirementproduct_set')
            instance_process = Process.objects.create(**each_process,product=instance_product,order=order)
            process_type = instance_process.process_type.name

            for req_material in many_req_material:
                req_material_bulk.append(RequirementMaterial(**req_material,process=instance_process))
            for req_product in many_req_product:
                req_product_bulk.append(RequirementProduct(**req_product,process=instance_process))
            
            wh_wip_type,created = WarehouseType.objects.get_or_create(id=order+2,name=f'Wip{order}')
            
            wh_product = {
                'quantity':0,
                'process':instance_process,
                'product':instance_product,
                'warehouse_type':wh_wip_type,
            }

            if process_type == 'subcont' or process_type == 'Subcont':
                whproduct_bulk.append(WarehouseProduct(**wh_product))

                wh_product['warehouse_type'] = wh_type_subcont
                whproduct_bulk.append(WarehouseProduct(**wh_product))
            else:
                whproduct_bulk.append(WarehouseProduct(**wh_product))

            order += 1

        RequirementMaterial.objects.bulk_create(req_material_bulk)
        RequirementProduct.objects.bulk_create(req_product_bulk)
        WarehouseProduct.objects.bulk_create(whproduct_bulk)

        return instance_product

    class Meta:
        model = Product
        exclude = ['process']


### Product management seriz
######






###### Serializers for product

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

class ProductionReportSerializer(ModelSerializer):
    class Meta:
        model = ProductionReport
        fields = ['product','created','quantity','process','quantity_not_good','operator','machine']




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


class MaterialProductionReport(ModelSerializer):
    class Meta:
        model = MaterialProductionReport
        fields = ['material','quantity','production_report']











