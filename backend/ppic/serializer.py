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
    
    def perform_delete(self, lst:list) -> None:
        for instance in lst:
            instance.delete()
    
    def perform_insert(self, lst:list, cls) -> None:
        cls.objects.bulk_create(lst)
    
    def perform_update(self, lst:list, cls, fields:list) -> None:
        cls.objects.bulk_update(lst,fields)

    def changed_material(self,obj:dict) -> None:
        self.perform_delete(obj['deleted'])
        self.perform_insert(obj['inserted'],obj['instance'])
        self.perform_update(obj['updated'],obj['instance'],['conversion','material','process'])
        
    def changed_product(self,obj:dict) -> None:
        self.perform_delete(obj['deleted'])
        self.perform_insert(obj['inserted'],obj['instance'])
        self.perform_update(obj['updated'],obj['instance'],['conversion','product','process'])
    
    def changed_warehouseproduct(self,obj:dict) -> None:
        self.perform_delete(obj['deleted'])
        self.perform_insert(obj['inserted'],obj['instance'])
        self.perform_update(obj['updated'],obj['instance'],['quantity','warehouse_type'])
    
    def changed_process(self,obj:dict) -> None:
        
        temp = 0
        for process in obj['deleted']:
            qty_wh = process.warehouseproduct_set.exclude(warehouse_type = 2).get().quantity
            temp += qty_wh
        
        last_wh = obj['updated'][-1].warehouseproduct_set.exclude(warehouse_type = 2 ).get() 
        last_wh.quantity += temp
        last_wh.save()
        
        ##### take all quantity deleted from warehouseproduct to updated warehouseproduct
        
        self.perform_delete(obj['deleted'])
        self.perform_update(obj['updated'],obj['instance'],['process_name','order','process_type'])

    def perform_changing(self,objs:dict) -> None:
        self.changed_product(objs['product'])
        self.changed_material(objs['material'])
        self.changed_warehouseproduct(objs['warehouseproduct'])
        self.changed_process(objs['process'])

    def update(self, instance, validated_data):
        '''
        update product -> process -> req material & req product & warehouse product
        '''
       
        changed_data = {
            'material': {
                'instance':RequirementMaterial,
                'deleted':[],
                'inserted':[],
                'updated':[]
            },
            'product': {
                'instance':RequirementProduct,
                'deleted':[],
                'inserted':[],
                'updated':[]
            },
            'warehouseproduct': {
                'instance':WarehouseProduct,
                'deleted':[],
                'inserted':[],
                'updated':[]
            },
            'process': {
                'instance':Process,
                'deleted':[],
                'updated':[]
            }
        }

        wh_type_subcont = WarehouseType.objects.get(id=2)
        wh_type_fg = WarehouseType.objects.get(id=1)

        many_process = validated_data.pop('ppic_process_related')
        len_process = len(many_process)

        instance_old_process = instance.ppic_process_related.all()
        len_instance_process = len(instance_old_process)

        instance.code = validated_data['code']
        instance.name = validated_data['name']
        instance.weight = validated_data['weight']
        instance.process = len_process
        instance.price = validated_data['price']
        instance.type = validated_data['type']
        instance.save() # perform update product
        order = 1

        for i in range(len_process):
            
            req_material = many_process[i].pop('requirementmaterial_set')
            len_material = len(req_material)

            req_product = many_process[i].pop('requirementproduct_set')
            len_product = len(req_product)
            
            if i > len_instance_process - 1:
                instance_process = Process.objects.create(**many_process[i],product=instance,order=order)
                new_process_type = instance_process.process_type.id
            else:
                instance_process = instance_old_process[i]
                old_process_type = instance_process.process_type.id

                instance_process.process_name = many_process[i]['process_name']
                instance_process.order = order
                instance_process.process_type = many_process[i]['process_type']
                # instance_process.save()
                changed_data['process']['updated'].append(instance_process)
                
                new_process_type = many_process[i]['process_type'].id

            instance_req_material = instance_process.requirementmaterial_set.all()
            len_instance_req_material = len(instance_req_material)

            instance_req_product = instance_process.requirementproduct_set.all()
            len_instance_req_product = len(instance_req_product)
            
            k = 0
            for k in range(len_material):
                if k > len_instance_req_material:
                    changed_data['material']['inserted'].append(RequirementMaterial(**req_material[k],process=instance_process))
                else:
                    instance_req_material[k].conversion = req_material[k]['conversion']
                    instance_req_material[k].material = req_material[k]['material']
                    instance_req_material[k].process = instance_process                    
                    changed_data['material']['updated'].append(instance_req_material[k])

            changed_data['material']['deleted'] = changed_data['material']['deleted'][:] + instance_req_material[k+1:]
            
            j = 0
            for j in range(len_product):
                if j > len_instance_req_product:
                    changed_data['product']['inserted'].append(RequirementProduct(**req_product[j],process=instance_process))
                else:
                    instance_req_product[j].conversion = req_product[j]['conversion']
                    instance_req_product[j].product = req_product[j]['product']
                    instance_req_product[j].process = instance_process                    
                    changed_data['product']['updated'].append(instance_req_product[j])

            changed_data['product']['deleted'] = changed_data['product']['deleted'][:] + instance_req_product[j+1:]

            wh_product = {
                'quantity':0,
                'process':instance_process,
                'product':instance,
            }

            wh_type_wip,created = WarehouseType.objects.get_or_create(id=order+2,name=f'Wip{order}')


            if i > len_instance_process - 1: # kalo prosesnya yang LAMA dah abis berarti insert
                if new_process_type == 2: # kalo proses itu SUBCONT
                        wh_product['warehouse_type'] = wh_type_subcont
                        changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
                
                if i == len_process - 1: # kalo proses barunya proses TERAKHIR
                    wh_product['warehouse_type'] = wh_type_fg
                    changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
                else: # kalo proses barunya bukan yang TERAKHIR
                    wh_product['warehouse_type'] = wh_type_wip
                    changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
            
            else: # asumsikan proses lama nya masih ada berarti update
                if i == len_process - 1: # proses barunya yang TERAKHIR
                    if i == len_instance_process - 1: # proses lama juga TERAKHIR
                        fg = instance_process.warehouseproduct_set.get(warehouse_type=1)
                        
                        if old_process_type == 2 and new_process_type != 2: # kalo proses lamanya itu subcont
                            subcont = instance_process.warehouseproduct_set.get(warehouse_type=2)
                            fg.quantity += subcont.quantity
                            changed_data['warehouseproduct']['deleted'].append(subcont)

                        elif old_process_type !=2 and new_process_type == 2:
                            wh_product['warehouse_type'] = wh_type_subcont
                            changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
                            
                        changed_data['warehouseproduct']['updated'].append(fg)

                    else: # proses lamanya BUKAN yang TERAKHIR
                        wip = instance_process.warehouseproduct_set.get(warehouse_type=order+2)
                        wip.warehouse_type = wh_type_fg
                        
                        if old_process_type == 2 and new_process_type != 2: # kalo proses lamanya itu subcont
                            subcont = instance_process.warehouseproduct_set.get(warehouse_type=2)
                            wip.quantity += subcont.quantity
                            changed_data['warehouseproduct']['deleted'].append(subcont)

                        elif old_process_type !=2 and new_process_type == 2:
                            wh_product['warehouse_type'] = wh_type_subcont
                            changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
                        
                        changed_data['warehouseproduct']['updated'].append(wip)
                
                else: # kalo proses baru BUKAN prosesnya yang TERAKHIR
                    if i == len_instance_process - 1: # prosesnya yang lama TERAKHIR
                        fg = instance_process.warehouseproduct_set.get(warehouse_type=1)
                        fg.warehouse_type = wh_type_wip

                        if old_process_type == 2 and new_process_type != 2: # kalo proses lamanya itu subcont
                            subcont = instance_process.warehouseproduct_set.get(warehouse_type=2)
                            fg.quantity += subcont.quantity
                            changed_data['warehouseproduct']['deleted'].append(subcont)    
                            
                        elif old_process_type !=2 and new_process_type == 2:
                            wh_product['warehouse_type'] = wh_type_subcont
                            changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
                            
                        changed_data['warehouseproduct']['updated'].append(fg)

                    else: #proses lama juga BUKAN yang TERAKHIR
                        wip = instance_process.warehouseproduct_set.get(warehouse_type=order+2)

                        if old_process_type == 2 and new_process_type != 2: # kalo proses lamanya itu subcont
                            subcont = instance_process.warehouseproduct_set.get(warehouse_type=2)
                            wip.quantity += subcont.quantity
                            changed_data['warehouseproduct']['deleted'].append(subcont)

                        elif old_process_type !=2 and new_process_type == 2:
                            wh_product['warehouse_type'] = wh_type_subcont
                            changed_data['warehouseproduct']['inserted'].append(WarehouseProduct(**wh_product))
                            
                        changed_data['warehouseproduct']['updated'].append(wip)

            order += 1

        changed_data['process']['deleted'] = changed_data['process']['deleted'][:] + instance_old_process[i+1:]


        self.perform_changing(changed_data)

        return instance

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











