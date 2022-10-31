from rest_framework.serializers import ModelSerializer,StringRelatedField,ValidationError,PrimaryKeyRelatedField
from rest_framework import serializers
from purchasing.models import Supplier
from django.db.models import Q,Prefetch,Count
from math import ceil
from .models import *
from marketing.models import Customer
from manager.shortcuts import invalid
from django.utils import timezone

class DriverSerializer(ModelSerializer):
    class Meta:
        model = Driver
        fields = ['name']

class MachineSerializer(ModelSerializer):
    class Meta:
        model = Machine
        fields ='__all__'

class OperatorSerializer(ModelSerializer):
    class Meta:
        model = Operator
        fields ='__all__'

class CustomerListSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SupplierListSerializer(ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class UomListSerializer(ModelSerializer):
    materials = serializers.IntegerField()
    class Meta:
        model = UnitOfMaterial
        fields = '__all__'

class VehicleSerializer(ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['licence_part_number']
    
class ProductTypeSerializer(ModelSerializer):
    products = serializers.IntegerField(read_only=True)
    class Meta:
        model = ProductType
        fields = '__all__'

class ProcessTypeSerializer(ModelSerializer):
    amount_of_process = serializers.IntegerField(read_only=True)
    class Meta:
        model = ProcessType
        fields = '__all__'
        

class ProductListSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class MaterialListSerializer(ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'

##################
#### Product Read Only Seriz
class WarehouseProductReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseProduct
        fields = ['id','quantity','warehouse_type']
        depth = 1

class MaterialProductionSerializer(ModelSerializer):
    warehousematerial = StringRelatedField(read_only=True)
    class Meta:
        model = Material
        fields ='__all__'
        depth = 1

class ProductionSerializer(ModelSerializer):
    ppic_warehouseproduct_related = WarehouseProductReadOnlySerializer(many=True)
    class Meta:
        model = Product
        fields='__all__'
        depth = 1

class RequirementMaterialReadOnlySerializer(ModelSerializer):
    material = MaterialProductionSerializer()
    class Meta:
        model = RequirementMaterial
        exclude = ['process']
        depth = 2

class RequirementProductReadOnlySerializer(ModelSerializer):
    product = ProductionSerializer()
    class Meta:
        model = RequirementProduct
        exclude = ['process']
        depth = 1

class ProcessReadOnlySerializer(ModelSerializer):
    warehouseproduct_set = WarehouseProductReadOnlySerializer(many=True)
    requirementproduct_set = RequirementProductReadOnlySerializer(many=True)
    requirementmaterial_set = RequirementMaterialReadOnlySerializer(many=True)

    class Meta:
        model = Process
        fields = ['id','process_name','order','process_type','warehouseproduct_set','requirementproduct_set','requirementmaterial_set']
        depth = 1

class ProductOrderReadOnlySerializer(ModelSerializer):
    class Meta:
        model = ProductOrder
        exclude = ['product']
        depth = 1

class ProductReadOnlySerializer(ModelSerializer):
    ppic_process_related = ProcessReadOnlySerializer(many=True)

    class Meta:
        model = Product
        fields = '__all__'
        depth = 1

class ProductDetailSerializer(ModelSerializer):
    ppic_process_related = ProcessReadOnlySerializer(many=True)
    ppic_productorder_related = ProductOrderReadOnlySerializer(many=True)
    productordered = serializers.IntegerField()
    productdelivered = serializers.IntegerField()

    class Meta:
        model = Product
        fields = '__all__'
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

class RequirementProductManagement(ModelSerializer):
    
    class Meta:
        model = RequirementProduct
        exclude = ['process']

class RequirementMaterialManagement(ModelSerializer):
    class Meta:
        model = RequirementMaterial
        fields = '__all__'

class ProcessManagementSerializer(ModelSerializer):

    requirementproduct_set = RequirementProductManagement(many=True)
    requirementmaterial_set = RequirementMaterialManagementSerializer(many=True)
    class Meta:
        model = Process
        fields = ['id','process_name','process_type','requirementproduct_set','requirementmaterial_set']

class ProductManagementSerializer(ModelSerializer):
    '''
    this serializer is used to create product nested to process then to requirement material, requirement product, warehouse product,

    but for update, its just update data product, no more.
    
    i've just moved update process to update partial process in ProcessPartialManagementSerializer

    '''
    ppic_process_related = ProcessManagementSerializer(many=True)


    def search(self,product_in_process,manyProcess):
        
        for process in manyProcess:
            req_products = process.requirementproduct_set.all()

            for req_product in req_products:
                product = req_product.product
                if product == product_in_process:
                    raise ValidationError(f'Error in assembly product')
                
                manyProcessOfCertainProduct = product.ppic_process_related.prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product')))

                self.search(product_in_process,manyProcessOfCertainProduct)

    def update(self, instance, validated_data):
        '''
        update product
        '''       
        many_process = validated_data.pop('ppic_process_related')
        len_process = len(many_process)

        instance_old_process = instance.ppic_process_related.all()
        len_instance_process = len(instance_old_process)
        instance.last_update = timezone.now()
        instance.process = len_process
        instance.save(update_fields=['last_update','process'])

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

        for process in many_process:

            for req_product in process['requirementproduct_set']:

                if validated_data['product'] == req_product['product']:
                    invalid('Error in assembly product')
                
                manyProcess = req_product['product'].ppic_process_related.prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product')))

                self.search(validated_data['product'],manyProcess)

        instance_product = Product.objects.create(**validated_data,process=len_process)
        wh_type_subcont = WarehouseType.objects.get(pk=2)
        wh_type_fg = WarehouseType.objects.get(pk=1)

        for each_process in many_process:
            many_req_material = each_process.pop('requirementmaterial_set')
            many_req_product = each_process.pop('requirementproduct_set')
            instance_process = Process.objects.create(**each_process,product=instance_product,order=order)
            process_type = instance_process.process_type.id

            for req_material in many_req_material:
                req_material_bulk.append(RequirementMaterial(**req_material,process=instance_process))
            for req_product in many_req_product:
                req_product_bulk.append(RequirementProduct(**req_product,process=instance_process))
            
            wh_wip_type,created = WarehouseType.objects.get_or_create(id=order+2,name=f'Wip{order}')            

            wh_product = {
                'quantity':0,
                'process':instance_process,
                'product':instance_product,
                'warehouse_type':wh_type_fg if len_process == order else wh_wip_type,
            }

            if process_type == 2:
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
        read_only_fields = ['created','last_update']

class ProcessPartialManagementSerializer(ModelSerializer):
    '''
    seriz for management data process of every product
    '''

    requirementproduct_set = RequirementProductManagement(many=True)
    requirementmaterial_set = RequirementMaterialManagementSerializer(many=True)

    def search(self,product_in_process,manyProcess):

        for process in manyProcess:
            req_products = process.requirementproduct_set.all()

            for req_product in req_products:
                product = req_product.product
                if product == product_in_process:
                    raise ValidationError(f'Error in assembly product')
                
                manyProcessOfCertainProduct = product.ppic_process_related.prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product')))

                self.search(product_in_process,manyProcessOfCertainProduct)

    def validate(self, attrs):
        product = attrs['product']
        order = attrs['order']
        len_process = product.ppic_process_related.count()

        if order > (len_process + 1):
            invalid(f"Cannot add Wip{order} to this product ")

        return super().validate(attrs)

    def validate_order(self,attrs):

        if attrs == 0:
            invalid('Cannot set zero to wip manufacturing process')

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
        self.perform_update(obj['updated'],obj['instance'],['input','output','material','process'])
        
    def changed_product(self,obj:dict) -> None:
        self.perform_delete(obj['deleted'])
        self.perform_insert(obj['inserted'],obj['instance'])
        self.perform_update(obj['updated'],obj['instance'],['input','output','product','process'])

    def perform_changing(self,objs:dict) -> None:
        self.changed_product(objs['product'])
        self.changed_material(objs['material'])

    def create(self, validated_data):
        '''
        create process -> material requirements & product requirements & warehouse product
        '''

        inserted = {
            'req_materials':[],
            'req_products':[],
            'warehouseproduct':[]
        }

        for req_product in validated_data['requirementproduct_set']:
            ## check to prevent product that need each other in requirement
                            
            if validated_data['product'] == req_product['product']:
                invalid('Error in assembly product')
            
            manyProcess = req_product['product'].ppic_process_related.prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product')))

            self.search(validated_data['product'],manyProcess)

        many_req_material = validated_data.pop('requirementmaterial_set')
        many_req_product = validated_data.pop('requirementproduct_set')
        order = validated_data['order']
        product = validated_data['product']
        len_process = product.ppic_process_related.count()
        instance_process = Process.objects.create(**validated_data)
        process_type = instance_process.process_type.id
        wh_type_subcont = WarehouseType.objects.get(pk=2)
        wh_type_fg = WarehouseType.objects.get(pk=1)

        product.process = len_process + 1
        product.save()
        ## update number of entries process of product

        for req_material in many_req_material:
            ## insert material requirements

            inserted['req_materials'].append(RequirementMaterial(**req_material,process=instance_process))
        for req_product in many_req_product:
            ## insert product assembly requirements

            inserted['req_products'].append(RequirementProduct(**req_product,process=instance_process))
        
        wh_type_wip,created = WarehouseType.objects.get_or_create(id=order+2,name=f'Wip{order}')
        
        wh_product = {
            'quantity': 0,
            'process': instance_process,
            'product': validated_data['product'],
            'warehouse_type': wh_type_wip ,
        }

        if order > len_process and len_process != 0:
            ## if new process is the last process, change previous process to wip
            ## and set new process to finished good
        
            prev_process = product.ppic_process_related.get(order = (order-1))
            prev_wh_type = WarehouseType.objects.get(pk=order+1)
            prev_wh_product = prev_process.warehouseproduct_set.exclude(warehouse_type=2).get()
            prev_wh_product.warehouse_type = prev_wh_type
            prev_wh_product.save()
            wh_product['warehouse_type'] = wh_type_fg
            
        
        elif order > len_process and len_process == 0:
            ## if new process is the last process, and there is not previous process in wip
            wh_product['warehouse_type'] = wh_type_fg            


        if process_type == 2:
            inserted['warehouseproduct'].append(WarehouseProduct(**wh_product))

            wh_product['warehouse_type'] = wh_type_subcont
            inserted['warehouseproduct'].append(WarehouseProduct(**wh_product))
        else:
            inserted['warehouseproduct'].append(WarehouseProduct(**wh_product))

        RequirementMaterial.objects.bulk_create(inserted['req_materials'])
        RequirementProduct.objects.bulk_create(inserted['req_products'])
        WarehouseProduct.objects.bulk_create(inserted['warehouseproduct'])

        return instance_process

    def update(self, instance, validated_data):
        '''
        update process -> req material & req product & warehouse product
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
        }

        for req_product in validated_data['requirementproduct_set']:
            ## check to prevent product that need each other in requirement

            if instance.product == req_product['product']:
                invalid('Error in assembly product')
            
            manyProcess = req_product['product'].ppic_process_related.prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product')))

            self.search(instance.product,manyProcess)

        order = validated_data['order']
        process_type = validated_data['process_type']
        process_name = validated_data['process_name']
        ## updated data

        instance_order = instance.order
        instance_process_type = instance.process_type
        instance_product = instance.product
        len_process = instance_product.ppic_process_related.count()
        instance_wh_product = instance.warehouseproduct_set.all()
        
        many_req_material = validated_data.pop('requirementmaterial_set')
        len_req_material = len(many_req_material)
        many_req_product = validated_data.pop('requirementproduct_set')
        len_req_product = len(many_req_product)

        wh_type_wip,created = WarehouseType.objects.get_or_create(id=order+2,name=f'Wip{order}')
        
        wh_type_subcont = WarehouseType.objects.get(pk=2)
        wh_type_fg = WarehouseType.objects.get(pk=1)

        if instance_process_type != process_type:
            ## if there is changes in process type
            instance.process_type = process_type

            if instance_process_type.id == 2 and process_type.id != 2:
                ## if previous process type is subcont and update to non subcont

                whsubcont = instance_wh_product.get(warehouse_type=2)
                wh_not_subcont = instance_wh_product.exclude(warehouse_type=2).get()
                wh_not_subcont.quantity += whsubcont.quantity
                wh_not_subcont.save()
                whsubcont.delete()

            elif instance_process_type.id != 2 and process_type.id == 2:
                ## if previous process type is not subcont and update to subcont

                WarehouseProduct.objects.create(quantity=0,process=instance,product=instance_product,warehouse_type=wh_type_subcont)

        if order != instance_order:
            ## if there is changes in order
            instance.order = order ## save new order here

            if order > len_process and instance_order != len_process:
                ## if order of process is the last process, change previous process to wip
                prev_process = Process.objects.filter(order = order-1,product=instance_product).prefetch_related(
                        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type=1))).get()
                prev_wh_type = WarehouseType.objects.get(pk=order+1)
                prev_wh_product = prev_process.warehouseproduct_set.get()
                prev_wh_product.warehouse_type = prev_wh_type
                prev_wh_product.save()
                
                ## and set warehouse product of this process to finished good
                current_wh_product = instance_wh_product.get(warehouse_type__gt=2)
                current_wh_product.warehouse_type = wh_type_fg
                current_wh_product.save()
            
            elif order < len_process and instance_order > len_process:
                prev_instance_process = Process.objects.filter(order = instance_order-1,product=instance_product).prefetch_related(
                        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()
                prev_wh_product = prev_instance_process.warehouseproduct_set.get()
                prev_wh_product.warehouse_type = wh_type_fg
                prev_wh_product.save()

                current_wh_product = instance_wh_product.get(warehouse_type=1) ## fg
                current_wh_product.warehouse_type = wh_type_wip
                current_wh_product.save()

            elif order == len_process and instance_order > len_process or order > len_process and instance_order == len_process :
                ## changes of order that doens't impact to warehouse product type
                pass

            else:
                current_wh_product = instance_wh_product.get(warehouse_type__gt=2) ## fg
                current_wh_product.warehouse_type = wh_type_wip
                current_wh_product.save()

        instance.process_name = process_name
        instance.save()

        
        instance_req_material = instance.requirementmaterial_set.all()
        len_instance_req_material = len(instance_req_material) - 1

        instance_req_product = instance.requirementproduct_set.all()
        len_instance_req_product = len(instance_req_product) - 1
        
        m = 0
        for k in range(len_req_material):
            if k > len_instance_req_material:
                changed_data['material']['inserted'].append(RequirementMaterial(**many_req_material[k],process=instance))
            else:
                instance_req_material[k].input = many_req_material[k].get('input',instance_req_material[k].input)
                instance_req_material[k].output = many_req_material[k].get('output',instance_req_material[k].output)
                instance_req_material[k].material = many_req_material[k]['material']
                instance_req_material[k].process = instance                    
                changed_data['material']['updated'].append(instance_req_material[k])
            m += 1

        changed_data['material']['deleted'] = changed_data['material']['deleted'][:] + instance_req_material[m:]
        
        p = 0
        for j in range(len_req_product):
            if j > len_instance_req_product:
                changed_data['product']['inserted'].append(RequirementProduct(**many_req_product[j],process=instance))
            else:
                instance_req_product[j].input = many_req_product[j].get('input',instance_req_product[j].input)
                instance_req_product[j].output = many_req_product[j].get('output',instance_req_product[j].output)
                instance_req_product[j].product = many_req_product[j]['product']
                instance_req_product[j].process = instance                    
                changed_data['product']['updated'].append(instance_req_product[j])
            p += 1

        changed_data['product']['deleted'] = changed_data['product']['deleted'][:] + instance_req_product[p:]
        
        self.perform_changing(changed_data)
        
        return instance


    class Meta:
        model = Process
        fields= '__all__'


### Product management seriz
######

#########
##### material read only seriz

class RequirementReadOnlySerializer(ModelSerializer):

    class Meta:
        model = RequirementMaterial
        exclude=['material']
        depth = 2

class WarehouseMaterialReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseMaterial
        exclude  = ['material']

class MaterialDetailSerializer(ModelSerializer):
    ppic_requirementmaterial_related = RequirementReadOnlySerializer(many=True)
    warehousematerial = WarehouseMaterialReadOnlySerializer()
    uom = PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Material
        fields = '__all__'
        depth = 1

class MaterialListSerializer(ModelSerializer):
    ppic_requirementmaterial_related = RequirementReadOnlySerializer(many=True)
    warehousematerial = WarehouseMaterialReadOnlySerializer()
    class Meta:
        model = Material
        fields = '__all__'
        depth = 1

class MaterialSupplierReadOnlySerializer(ModelSerializer):
    ppic_material_related = MaterialListSerializer(many=True)
    class Meta:
        model = Supplier
        fields = '__all__'

#### material read only seriz
#########



###### Serializers for product







####### Serializers for material


class MaterialSerializer(ModelSerializer):

    def create(self, validated_data):
        instance = super().create(validated_data)
        WarehouseMaterial.objects.create(quantity=0,material=instance)
        return instance 
    
    def update(self, instance, validated_data):
        req_material = instance.ppic_requirementmaterial_related.all()
        wh_material = instance.warehousematerial

        if len(req_material) > 0:
            raise ValidationError('Tidak bisa mengubah data material yang menjadi kebutuhan produksi')
        if wh_material.quantity > 0:
            raise ValidationError('Tidak bisa mengubah data material yang memiliki stok di gudang')
        
        instance.last_update = timezone.now()
        instance.save(update_fields=["last_update"])

        return super().update(instance, validated_data)
    
    class Meta:
        model = Material
        fields = ['id','name','spec','length','width','thickness','uom','supplier','weight','image']

class ConversionUomReadOnlySerializer(ModelSerializer):
    class Meta:
        model = ConversionUom
        fields = '__all__'
        depth = 1

class ConversionUomManagementSerializer(ModelSerializer):

    def validate(self, attrs):
        input = attrs['uom_input']
        output = attrs['uom_output']

        if input == output:
            raise ValidationError(" It's forbidden to input conversion data from the same unit")

        uoms = ConversionUom.objects.filter(Q(uom_input = output) & Q(uom_output = input)).first()
        
        if uoms is None:
            return super().validate(attrs)
        raise ValidationError(f'{input.name} has become the basis of conversion of {output.name}')

    class Meta:
        model = ConversionUom
        fields = '__all__'

class BasedConversionReadOnlySerializer(ModelSerializer):
    class Meta:
        model = BasedConversionMaterial
        fields = '__all__'
        depth = 2

class BasedConversionManagementSerializer(ModelSerializer):

    def validate(self, attrs):
        input = attrs['material_input']
        unit_input  = input.uom
        output = attrs['material_output']
        unit_output = output.uom
        

        uoms = ConversionUom.objects.filter(Q(uom_input = unit_input) & Q(uom_output = unit_output)).first()

        if uoms is None:
            raise ValidationError('Tidak ada data konversi pada unit material tersebut')
        if input == output:
            raise ValidationError('Tidak bisa mengkonversi material yang sama')

        return super().validate(attrs)

    class Meta:
        model = BasedConversionMaterial
        fields = '__all__'

class ConversionMaterialReportReadOnlySerializer(ModelSerializer):
    class Meta:
        model = ConversionMaterialReport
        fields = '__all__'
        depth = 2

class ConversionMaterialReportManagementSerializer(ModelSerializer):
    
    def validate(self, attrs):
        '''
        validasi untuk kecukupan material
        '''
        input = attrs['material_input']
        output = attrs['material_output']
        uoms = BasedConversionMaterial.objects.filter(Q(material_input = input) & Q(material_output = output)).first()
        if uoms is None:
            raise ValidationError('Tidak ada data konversi pada kedua material tersebut')
        
        used_material = (attrs['quantity_output'] / uoms.quantity_output) * uoms.quantity_input
        stok = input.warehousematerial.quantity
        if used_material > stok:
            raise ValidationError(f'Stok material {input.name} tidak cukup')
        
        return super().validate(attrs)
    
    def create(self, validated_data):
        input = validated_data['material_input']
        output = validated_data['material_output']

        uoms = BasedConversionMaterial.objects.get(material_input = input, material_output=output)
        used_material = (validated_data['quantity_output'] / uoms.quantity_output) * uoms.quantity_input
        
        rest_material = ceil(used_material) - used_material

        if rest_material > 0:
            wh_scrap = WarehouseScrapMaterial.objects.filter(material=input).first()
            if wh_scrap is None:
                WarehouseScrapMaterial.objects.create(quantity = rest_material, material = input)
            else:
                wh_scrap.quantity += rest_material
                wh_scrap.save()
        
        wh_material_input = input.warehousematerial
        wh_material_input.quantity -= ceil(used_material)
        wh_material_input.save()

        wh_material_output = output.warehousematerial
        wh_material_output.quantity += validated_data['quantity_output']
        wh_material_output.save()

        validated_data['quantity_input'] = ceil(used_material)

        return super().create(validated_data)

    class Meta:
        model = ConversionMaterialReport
        fields = '__all__'
        read_only_fields = ['quantity_input']

class DetailMrpReadOnlySerializer(ModelSerializer):

    class Meta:
        model = DetailMrp
        fields = ['id','product','quantity','quantity_production']
        depth = 1

class MrpReadOnlySerializer(ModelSerializer):
    detailmrp_set = DetailMrpReadOnlySerializer(many=True)

    class Meta:
        model = MaterialRequirementPlanning
        fields = ['id','material','quantity','detailmrp_set']
        depth = 2

class DetailMrpManagementSerializer(ModelSerializer):
    class Meta:
        model = DetailMrp
        fields = ['id','product','quantity','quantity_production']

class MrpManagementSerializer(ModelSerializer):
    detailmrp_set = DetailMrpManagementSerializer(many=True)

    def validate_detailmrp_set(self,attrs):
        quantity_req = self.initial_data['quantity']
        temp = 0
        for detailmrp in attrs:
            temp += detailmrp['quantity']
        if temp > quantity_req:
            raise ValidationError('Jumlah kebutuhan berlebih dari jumlah permintaan')

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

    class Meta:
        model = MaterialRequirementPlanning
        fields = ['id','quantity','material','detailmrp_set']

class WarehouseMaterialManagementSerializer(ModelSerializer):
    class Meta:
        model = WarehouseMaterial
        fields = '__all__'
        read_only_fields = ['id','material']

class WarehouseMaterialReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseMaterial
        exclude = ['material']

class WarehouseScrapReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseScrapMaterial
        fields = ['id','material','quantity']
        depth = 2

class WarehouseScrapManagementSerializer(ModelSerializer):
    class Meta:
        model = WarehouseScrapMaterial
        fields = '__all__'

class MaterialUomReadOnlySerializer(ModelSerializer):
    warehousematerial = WarehouseMaterialReadOnlySerializer()
    class Meta:
        model = Material
        exclude = ['uom']
        depth = 1

class UomWarehouseMaterialSerializer(ModelSerializer):
    material_set = MaterialUomReadOnlySerializer(many=True)
    amount_of_material = serializers.IntegerField()
    class Meta:
        model = UnitOfMaterial
        fields = '__all__'

class UomManagementSerializer(ModelSerializer):
    class Meta:
        model = UnitOfMaterial
        fields = '__all__'


class StockWarehouseProductReadOnlySerializer(ModelSerializer):
    class Meta:
        model = WarehouseProduct
        exclude = ['warehouse_type']
        depth = 2

class WarehouseProductManagementSerializer(ModelSerializer):
    '''
    serializer for update stock product eg: wip,subcont,finishgood
    '''
    class Meta:
        model = WarehouseProduct
        fields = '__all__'
        read_only_fields = ['process','product','warehouse_type']

class WarehouseTypeReadOnlySerializer(ModelSerializer):
    warehouseproduct_set = StockWarehouseProductReadOnlySerializer(many=True)
    class Meta:
        model = WarehouseType
        fields = ['id','name','warehouseproduct_set']


class MaterialReceiptReadOnlySerializer(ModelSerializer):
    class Meta:
        model = MaterialReceipt
        exclude = ['delivery_note_material']
        depth = 2

class DeliveryNoteMaterialReadOnlySerializer(ModelSerializer):
    materialreceipt_set = MaterialReceiptReadOnlySerializer(many=True)
    class Meta:
        model = DeliveryNoteMaterial
        fields = '__all__'
        depth = 1

class SupplierDeliveryNoteReadOnlySerializer(ModelSerializer):
    ppic_deliverynotematerial_related = DeliveryNoteMaterialReadOnlySerializer(many=True)
    class Meta:
        model = Supplier
        fields = '__all__'
        depth = 1

class MaterialReceiptManagementSerializer(ModelSerializer):
    
    def validate_material_order(self,attrs):
        if attrs.done:
                raise ValidationError('Order tersebut sudah selesai')
        
        return attrs
    
    def validate(self, attrs):

        supplierDeliveryNoteMaterial = attrs['delivery_note_material'].supplier
        supplierPurchaseOrder = attrs['material_order'].purchase_order_material.supplier
        material = attrs['material_order'].material

        if supplierPurchaseOrder is not supplierDeliveryNoteMaterial or material.supplier is not supplierDeliveryNoteMaterial:
            raise ValidationError(f'{material.name} is not belongs to {supplierDeliveryNoteMaterial.name}')

        return super().validate(attrs)

    def create(self, validated_data):
        
        material_order = validated_data['material_order']
        material_order.arrived += validated_data['quantity']
        whmaterial = material_order.material.warehousematerial
        whmaterial.quantity += validated_data['quantity']
        
        schedules = validated_data.get('schedules',None)
        if schedules is not None:
            schedules.fulfilled_quantity = validated_data['quantity']
            schedules.save()

        if material_order.arrived >= material_order.ordered:
            material_order.done = True

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
            raise ValidationError('Edit data gagal, karena material sudah digunakan untuk produksi')
        
        if instance.material_order != validated_data['material_order']:
            raise ValidationError('Update failed, cannot change material from material receipt')
        
        instance_mo.arrived += validated_data['quantity']
        instance_wh.quantity += validated_data['quantity']
        
        if instance_schedule is not None:
            instance_schedule.fulfilled_quantity -= instance.quantity
            instance_schedule.fulfilled_quantity += validated_data['quantity']
            instance_schedule.save()

        if instance_mo.arrived >=instance_mo.ordered:
            instance_mo.done = True
        else:
            instance_mo.done = False

        validated_data.pop('schedules',None)

        instance_mo.save()
        instance_wh.save()

        return super().update(instance, validated_data)

    class Meta:
        model = MaterialReceipt
        fields = '__all__'

class DeliveryNoteMaterialManagementSerializer(ModelSerializer):
    note = serializers.CharField(allow_blank=True)
    class Meta:
        model = DeliveryNoteMaterial
        fields = '__all__'


class ProductDeliverCustomerReadOnlySerializer(ModelSerializer):
    '''
    seriz for get data product delivery depth to 2 relations below
    '''
    class Meta:
        model = ProductDeliverCustomer
        exclude = ['delivery_note_customer']
        depth = 2

class DeliveryNoteCustomerReadOnlySerializer(ModelSerializer):
    '''
    seriz for get data delivery note
    '''
    productdelivercustomer_set = ProductDeliverCustomerReadOnlySerializer(many=True)
    class Meta:
        model = DeliveryNoteCustomer
        exclude = ['customer']

class CustomerDeliveryNoteReadOnlySerializer(ModelSerializer):
    '''
    seriz for read data from customer -> delivery note -> product delivery
    '''
    ppic_deliverynotecustomer_related = DeliveryNoteCustomerReadOnlySerializer(many=True)
    class Meta:
        model = Customer
        fields = '__all__'

class DeliveryNoteCustomerManagementSerializer(ModelSerializer):
    '''
    seriz for management delivery note customer
    '''
    class Meta:
        model = DeliveryNoteCustomer
        fields = '__all__'


class ProductDeliverCustomerManagementSerializer(ModelSerializer):
    '''
    seriz for management product delivery
    '''    
    def validate_product_order(self,attrs):
        if attrs.done:
            raise ValidationError('Order tersebut sudah selesai')

        return attrs
    
    def validate(self, attrs):
        po = attrs['product_order']
        available_quantity_deliver = po.ordered - po.delivered
        wh_product = po.product.ppic_warehouseproduct_related.get(warehouse_type=1)

        if attrs['quantity'] > available_quantity_deliver:
            raise ValidationError('Jumlah pengiriman melebihi jumlah order')
        
        if attrs['quantity'] > wh_product.quantity:
            raise ValidationError('Stock finish good tidak cukup')

        return super().validate(attrs)

    def fluence_stock(self,po,wh_product,quantity):

        wh_product.quantity -= quantity
        po.delivered += quantity

        if po.delivered >= po.ordered:
            po.done = True
        else:
            po.done = False

        po.save()
        wh_product.save()

    def fluence_stock_update(self,po,wh_product,old_quantity,new_quantity):
        
        wh_product.quantity += old_quantity
        po.delivered -= old_quantity

        self.fluence_stock(po,wh_product,new_quantity)

    def update(self, instance, validated_data):
        if instance.paid:
            raise ValidationError('Pengiriman product sudah lunas')
        wh_product = instance.product_order.product.ppic_warehouseproduct_related.get(warehouse_type=1)
        validated_data.pop('schedules',None)
        instance_schedules = instance.schedules
        if instance_schedules is not None:
            instance_schedules.fulfilled_quantity -= instance.quantity
            instance_schedules.fulfilled_quantity += validated_data['quantity']
            instance_schedules.save()

        self.fluence_stock_update(instance.product_order,wh_product,instance.quantity,validated_data['quantity'])


        
        return super().update(instance, validated_data)

    def create(self, validated_data):
        po = validated_data['product_order']
        wh_product = po.product.ppic_warehouseproduct_related.get(warehouse_type=1)
        self.fluence_stock(po,wh_product,validated_data['quantity'])
        schedules = validated_data.get('schedules',None)
        if schedules is not None:
            schedules.fulfilled_quantity += validated_data['quantity']
            schedules.save()

        return super().create(validated_data)

    class Meta:
        model = ProductDeliverCustomer
        fields = '__all__'

class DeliveryNoteSubcontManagementSerializer(ModelSerializer):
    '''
    seriz for management delivery note product SUBCONSTRUCTION
    '''
    class Meta:
        model = DeliveryNoteSubcont
        fields= '__all__'

class ProductDeliverySubcontManagementSerializer(ModelSerializer):
    '''
    seriz for management delivery product subcont
    '''

    def suffciency_req_material_check(self,req_materials,production_quantity:int):
        
        for req_material in req_materials:
            wh_material = req_material.material.warehousematerial
            stock_in_wh = wh_material.quantity
            used_material = ceil((production_quantity / req_material.output) * req_material.input)
            if used_material > stock_in_wh:
                raise ValidationError(f'Jumlah stok {req_material.material.name} tidak cukup')
 

    def sufficiency_req_product_check(self,req_products,production_quantity:int):
        
        for req_product in req_products:
            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.first()
            stock_in_whproduct = wh_product.quantity
            used_product = (production_quantity/req_product.output) * req_product.input
            if used_product > stock_in_whproduct:
                raise ValidationError(f'Jumlah stok produk {product.name} tidak cukup')

    def validate(self, attrs):

        product = attrs['product']
        process = attrs['process']
        order = process.order
        quantity_delivery = attrs['quantity']

        if order > 1:
            prev_process = Process.objects.get(order = order-1, product = product)
            warehouse_wip = prev_process.warehouseproduct_set.filter(warehouse_type__gt = 2).first()
            
            if quantity_delivery > warehouse_wip.quantity:
                raise ValidationError(f'Quantity stok of {product.name} is not enough to make this delivery')

        if process not in product.ppic_process_related.all():
            raise ValidationError(f'Proses tersebut bukan bagian dari work in process product {product.name}')

        req_product = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_material = process.requirementmaterial_set.select_related('material__warehousematerial')
        

        self.suffciency_req_material_check(req_material,quantity_delivery)
        self.sufficiency_req_product_check(req_product,quantity_delivery)

        return super().validate(attrs)
    
    def create(self, validated_data):

        product = validated_data['product']
        process = validated_data['process']
        quantity_delivery = validated_data['quantity']
        order = process.order
        
        inserted = {
            'req_material_subcont':[],
            'req_product_subcont':[]
        }

        updated = {
            'wh_material':[],
            'wh_product':[]
        }

        productDeliverSubcont = super().create(validated_data)

        if order > 1:

            prev_process = Process.objects.filter(order = order-1,product=product).prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()

            warehouse_wip = prev_process.warehouseproduct_set.first()
            warehouse_wip.quantity -= (quantity_delivery)
            warehouse_wip.save()
         
        warehouse_subcont = process.warehouseproduct_set.filter(warehouse_type = 2).first()
        warehouse_subcont.quantity += (quantity_delivery)
        warehouse_subcont.save()
        
        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))

        for req_material in req_materials:
            material = req_material.material
            wh_material = material.warehousematerial
            used_material = (quantity_delivery / req_material.output) * req_material.input
            rest_material = ceil(used_material) - used_material
            
            if rest_material > 0:

                obj,created = WarehouseScrapMaterial.objects.get_or_create(material=material)
                obj.quantity += rest_material
                obj.save()

            wh_material.quantity -= ceil(used_material)
            updated['wh_material'].append(wh_material)
            inserted['req_material_subcont'].append(RequirementMaterialSubcont(quantity=used_material,material=material,product_subcont=productDeliverSubcont))

        for req_product in req_products:
            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.first()
            used_product = ceil((quantity_delivery / req_product.output) * req_product.input)

            wh_product.quantity -= used_product

            updated['wh_product'].append(wh_product)
            inserted['req_product_subcont'].append(RequirementProductsubcont(quantity=used_product,product=product,product_subcont=productDeliverSubcont))

        updated['wh_product'].append(warehouse_subcont)

        WarehouseProduct.objects.bulk_update(updated['wh_product'],['quantity'])
        WarehouseMaterial.objects.bulk_update(updated['wh_material'],['quantity'])

        RequirementMaterialSubcont.objects.bulk_create(inserted['req_material_subcont'])
        RequirementProductsubcont.objects.bulk_create(inserted['req_product_subcont'])

        return productDeliverSubcont

    
    def requirement_check(self,instance):
        
        '''
        check the product if its production report can be change or not, 
        including check this process requirement material as well as requirement product
        '''

        process = instance.process

        material_reports = instance.requirementmaterialsubcont_set.select_related('material')
        product_reports = instance.requirementproductsubcont_set.select_related('product')

        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_mats = [x.material for x in req_materials]
        req_prod = [x.product for x in req_products]


        for report in material_reports:
            try:
                req_mats.remove(report.material)
            except:
                self.invalid_requirement()

        for report in product_reports:
            try:
                req_prod.remove(report.product)
            except:
                self.invalid_requirement()

        if len(req_mats) > 0:
            self.invalid_requirement()
        if len(req_prod) > 0:
            self.invalid_requirement()

        return req_materials,req_products,material_reports,product_reports

    
    def invalid_requirement(self):

        return invalid('Cannot change delivery product subcont, because material requirements or product requirements in this subcont process have changed')

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    class Meta:
        model = ProductDeliverSubcont
        fields = '__all__'

class MaterialProductionReportReadOnlySerializer(ModelSerializer):
    class Meta:
        model = MaterialProductionReport
        exclude = ['production_report']
        depth = 2

class ProductProductionReportReadOnlySerializer(ModelSerializer):
    class Meta:
        model = ProductProductionReport
        exclude = ['production_report']
        depth = 2

class ProductionReportReadOnlySerializer(ModelSerializer):
    productproductionreport_set = ProductProductionReportReadOnlySerializer(many=True)
    materialproductionreport_set = MaterialProductionReportReadOnlySerializer(many=True)

    class Meta:
        model = ProductionReport
        fields = '__all__'
        depth = 2        



class ProductionReportManagementSerializer(ModelSerializer):


    def suffciency_req_material_check(self,req_materials,production_quantity:int):
        
        for req_material in req_materials:
            wh_material = req_material.material.warehousematerial
            stock_in_wh = wh_material.quantity
            used_material = ceil((production_quantity / req_material.output) * req_material.input)
            if used_material > stock_in_wh:
                raise ValidationError(f'Jumlah stok {req_material.material.name} tidak cukup')
 

    def sufficiency_req_product_check(self,req_products,production_quantity:int):
        
        for req_product in req_products:
            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.first()
            stock_in_whproduct = wh_product.quantity
            used_product = (production_quantity/req_product.output) * req_product.input
            if used_product > stock_in_whproduct:
                raise ValidationError(f'Jumlah stok produk {product.name} tidak cukup')

    def validate(self, attrs):

        product = attrs['product']
        process = attrs['process']
        order = process.order
        quantity_production = attrs['quantity'] + attrs['quantity_not_good']

        if order > 1:
            try:
                prev_process = Process.objects.get(order = order-1, product = product)
                warehouse_wip = prev_process.warehouseproduct_set.filter(warehouse_type__gt = 2).first()
                
                if quantity_production > warehouse_wip.quantity:
                    raise ValidationError(f'Quantity stok wip{product.name} is not enough for make production')
            except:
                invalid(f"Process wip{order-1} doesn't exists ")

        if process not in product.ppic_process_related.all():
            raise ValidationError(f'Invalid process')

        req_product = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_material = process.requirementmaterial_set.select_related('material__warehousematerial')
        
        self.suffciency_req_material_check(req_material,quantity_production)
        self.sufficiency_req_product_check(req_product,quantity_production)

        return super().validate(attrs)

    def validate_process(self,attrs):
        subcont_type = ProcessType.objects.get(pk=2)
        process_type = attrs.process_type
        if process_type == subcont_type:
            raise ValidationError('Cannot do production on subcont process')

        return attrs

    def validate_quantity(self,attrs):

        if attrs == 0:
            raise ValidationError('Cannot do production with zero quantity')

        return attrs

    def create(self, validated_data):

        product = validated_data['product']
        process = validated_data['process']
        quantity_production = validated_data['quantity'] + validated_data['quantity_not_good']
        order = process.order
        
        inserted = {
            'material_report':[],
            'product_report':[]
        }

        updated = {
            'wh_material':[],
            'wh_product':[]
        }

        production_report = super().create(validated_data)

        if order > 1:
            try:
                prev_process = Process.objects.filter(order = order-1,product=product).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()
                warehouse_wip = prev_process.warehouseproduct_set.first()
                warehouse_wip.quantity -= (quantity_production)
                warehouse_wip.save()
            except:
                invalid(f"Process wip{order-1} doesn't exists")

        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))

        for req_material in req_materials:
            material = req_material.material
            wh_material = material.warehousematerial
            used_material = (quantity_production / req_material.output) * req_material.input
            rest_material = ceil(used_material) - used_material
            
            if rest_material > 0:

                obj,created = WarehouseScrapMaterial.objects.get_or_create(material=material)
                obj.quantity += rest_material
                obj.save()

            wh_material.quantity -= ceil(used_material)
            updated['wh_material'].append(wh_material)
            inserted['material_report'].append(MaterialProductionReport(quantity=used_material,material=material,production_report=production_report))

        for req_product in req_products:
            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.first()
            used_product = ceil((quantity_production / req_product.output) * req_product.input)

            wh_product.quantity -= used_product

            updated['wh_product'].append(wh_product)
            inserted['product_report'].append(ProductProductionReport(quantity=used_product,product=product,production_report=production_report))

        wh_current_wip = process.warehouseproduct_set.exclude(warehouse_type = 2).first()
        wh_current_wip.quantity += validated_data['quantity']

        updated['wh_product'].append(wh_current_wip)

        WarehouseProduct.objects.bulk_update(updated['wh_product'],['quantity'])
        WarehouseMaterial.objects.bulk_update(updated['wh_material'],['quantity'])

        MaterialProductionReport.objects.bulk_create(inserted['material_report'])
        ProductProductionReport.objects.bulk_create(inserted['product_report'])

        return production_report
    
    def invalid_requirement(self):

        return invalid('Cannot change production report, because material requirements or product requirements in this process have changed')

    def requirement_check(self,instance):
        
        '''
        check the product if its production report can be change or not, 
        including check this process requirement material as well as requirement product
        '''

        process = instance.process

        material_reports = instance.materialproductionreport_set.select_related('material')
        product_reports = instance.productproductionreport_set.select_related('product')

        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_mats = [x.material for x in req_materials]
        req_prod = [x.product for x in req_products]


        for report in material_reports:
            try:
                req_mats.remove(report.material)
            except:
                self.invalid_requirement()

        for report in product_reports:
            try:
                req_prod.remove(report.product)
            except:
                self.invalid_requirement()

        if len(req_mats) > 0:
            self.invalid_requirement()
        if len(req_prod) > 0:
            self.invalid_requirement()

        return req_materials,req_products,material_reports,product_reports

    def update(self, instance, validated_data):
        
        '''
        update production report, and quantity that used for requirement product and requirement material also changed
        '''

        prev_quantity_production = instance.quantity + instance.quantity_not_good
        quantity_production = validated_data['quantity'] + validated_data['quantity_not_good']
        instance_product = instance.product
        process = instance.process
        req_materials,req_products,material_reports,product_reports = self.requirement_check(instance)
        order = process.order

        updated = {
            'wh_material':[],
            'wh_product':[],
            'material_reports':[],
            'product_reports':[],
        }

        production_report = super().update(instance, validated_data)
        production_report.last_update = timezone.now()
        production_report.save(update_fields=['last_update'])


        if order > 1:
            try:
                prev_process = Process.objects.filter(order = order-1,product=instance_product).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()

                warehouse_wip = prev_process.warehouseproduct_set.first()
                warehouse_wip.quantity += (prev_quantity_production)
                warehouse_wip.quantity -= (quantity_production)
                warehouse_wip.save()
            except:
                invalid(f"Process wip${order-1} doesn't exists ")

        for req_material in req_materials:
            material = req_material.material
            wh_material = material.warehousematerial
            prev_used_material = (prev_quantity_production / req_material.output) * req_material.input
            ceiled_prev_used_material = ceil(prev_used_material)
            prev_rest_material = ceiled_prev_used_material - prev_used_material

            current_used_material = (quantity_production / req_material.output) * req_material.input
            ceiled_current_used_material = ceil(current_used_material)
            current_rest_material = ceiled_current_used_material - current_used_material


            wh_material.quantity += ceiled_prev_used_material
            wh_material.quantity -= ceiled_current_used_material
            
            try:
                obj = WarehouseScrapMaterial.objects.get(material=material)
            except:
                obj = WarehouseScrapMaterial.objects.create(material=material,quantity=0)

            if current_rest_material > 0:
                if prev_rest_material > 0:
                    obj.quantity -= prev_rest_material
                    obj.quantity += current_rest_material
                else:
                    obj.quantity += current_rest_material
            else:
                if prev_rest_material > 0:
                    obj.quantity -= prev_rest_material
            obj.save()

            
            updated['wh_material'].append(wh_material)

            for report in material_reports.filter(material=material):
                report.quantity = ceiled_current_used_material
                updated['material_reports'].append(report)
                

        for req_product in req_products:
            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.first()
            prev_used_product = ceil((prev_quantity_production / req_product.output) * req_product.input)
            used_product = ceil((quantity_production / req_product.output) * req_product.input)

            wh_product.quantity += prev_used_product
            wh_product.quantity -= used_product

            updated['wh_product'].append(wh_product)

            for report in product_reports.filter(product=product):
                report.quantity = used_product
                updated['product_reports'].append(report)
                


        wh_current_wip = process.warehouseproduct_set.exclude(warehouse_type = 2).first()
        wh_current_wip.quantity -= instance.quantity
        wh_current_wip.quantity += validated_data['quantity']
        
        updated['wh_product'].append(wh_current_wip)

        WarehouseProduct.objects.bulk_update(updated['wh_product'],['quantity'])
        WarehouseMaterial.objects.bulk_update(updated['wh_material'],['quantity'])

        MaterialProductionReport.objects.bulk_update(updated['material_reports'],['quantity'])
        ProductProductionReport.objects.bulk_update(updated['product_reports'],['quantity'])

        return production_report
    



    class Meta:
        model = ProductionReport
        fields = '__all__'
        read_only_fields = ['last_update','created']



class MaterialOrderReadOnlySerializer(ModelSerializer):
    class Meta:
        model = MaterialOrder
        fields = '__all__'
        depth = 2


class MaterialReceiptScheduleReadOnlySerializer(ModelSerializer):
    class Meta:
        model = MaterialReceiptSchedule
        fields = '__all__'
        depth = 3


class ProcessProductionSerializer(ModelSerializer):
    warehouseproduct_set = WarehouseProductReadOnlySerializer(many=True)
    requirementproduct_set = RequirementProductReadOnlySerializer(many=True)
    requirementmaterial_set = RequirementMaterialReadOnlySerializer(many=True)
    production_quantity = serializers.IntegerField(read_only=True)
    class Meta:
        model = Process
        fields = '__all__'
        depth = 1

class ProductSerializer(ModelSerializer):
    ppic_process_related = ProcessProductionSerializer(many=True)
    class Meta:
        model = Product
        fields ='__all__'


