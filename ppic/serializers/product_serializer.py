from rest_framework.serializers import ModelSerializer,IntegerField
from django.db.models import Prefetch,QuerySet
from django.utils import timezone

from manager.shortcuts import invalid

from ppic.models import Product,ProductType,Process,ProcessType,RequirementProduct,RequirementMaterial,WarehouseProduct,WarehouseType
from .warehouse_serializer import OneDepthWarehouseProductSerializer,BaseWarehouseProductSerializer
from .material_serializer import OneDepthMaterialNestedWarehouseSerializer,RequirementMaterialSerializer,TwoDepthRequirementMaterialSerializer
from marketing.serializers.sales_order_serializer import OneDepthProductOrderSerializer


class BaseProductTypeSerializer(ModelSerializer):
    '''
    base product type serializer class
    '''

    class Meta:
        model = ProductType
        fields = '__all__'

class BaseProductSerializer(ModelSerializer):
    '''
    base product serializer class
    '''

    class Meta:
        model = Product
        fields = '__all__'

class BaseProcessTypeSerializer(ModelSerializer):
    '''
    baser process type serializer class
    '''

    class Meta:
        model = ProcessType
        fields = '__all__'

class BaseProcessSerializer(ModelSerializer):
    '''
    base serializer class of process
    '''

    class Meta:
        model = Process
        fields = '__all__'

class BaseRequirementProductSerializer(ModelSerializer):
    '''
    base serializer class of requirement product
    '''

    class Meta:
        model = RequirementProduct
        fields = '__all__'
        read_only_fields = ['process']

class RequirementProductSerializer(BaseRequirementProductSerializer):
    pass

class OneDepthProductSerializer(BaseProductSerializer):
    '''
    one depth product serializer class
    '''
    total_stock = IntegerField(read_only=True)

    class Meta(BaseProductSerializer.Meta):
        depth = 1

class OneDepthProductNestedWarehouseSerializer(OneDepthProductSerializer):
    '''
    one depth product serializer class nested to warehouse
    '''
    ppic_warehouseproduct_related = OneDepthWarehouseProductSerializer(many=True)
    total_order = IntegerField(read_only=True)

class OneDepthRequirementProductSerializer(BaseRequirementProductSerializer):
    '''
    one depth requirement product serializer class
    '''
    product = OneDepthProductNestedWarehouseSerializer()

    class Meta(BaseRequirementProductSerializer.Meta):
        depth = 1

class OneDepthProcessNestedWarehouseSerializer(BaseProcessSerializer):
    '''
    one depth process serializer class nested to warehouseproduct
    '''
    warehouseproduct_set = OneDepthWarehouseProductSerializer(many=True,read_only=True)

    class Meta(BaseProcessSerializer.Meta):
        depth = 1

class OneDepthProcessNestedSerializer(OneDepthProcessNestedWarehouseSerializer):
    '''
    one depth process serializer class nested to warehouseproduct, requirement product, requirement material
    '''
    requirementmaterial_set = TwoDepthRequirementMaterialSerializer(many=True)
    requirementproduct_set = OneDepthRequirementProductSerializer(many=True)
    production_quantity = IntegerField(read_only=True)

class OneDepthProductNestedProcessSerializer(OneDepthProductSerializer):
    '''
    one depth product serializer class nested to process
    '''
    ppic_process_related = OneDepthProcessNestedSerializer(many=True)

class OneDepthProductNestedProcessAndOrderSerializer(OneDepthProductNestedProcessSerializer):
    '''
    one depth product serializer class nested to product order, process.
        extend fields product ordered, and product delivered
    '''
    ppic_productorder_related = OneDepthProductOrderSerializer(many=True)
    productordered = IntegerField(read_only=True)
    productdelivered = IntegerField(read_only=True)

class ProcessTypeSerializer(BaseProcessTypeSerializer):
    '''
    extended process type serializer class
    '''
    amount_of_process = IntegerField(read_only=True)

class ProductTypeSerializer(BaseProductTypeSerializer):
    '''
    extended product type serializer class
    '''
    products = IntegerField(read_only=True)

class ProcessManagementSerializer(BaseProcessSerializer):
    '''
    process serializer class for create, update data process
        nested to warehouse is needed for generating data warehouse when send response to client-app
    '''

    requirementmaterial_set = RequirementMaterialSerializer(many=True)
    requirementproduct_set = RequirementProductSerializer(many=True)
    warehouseproduct_set = BaseWarehouseProductSerializer(many=True,read_only=True)
    
    def search(self,product_in_process:Product,manyProcess:QuerySet):
        # recursion method to find if there is any requirement product assembly with this product in process

        for process in manyProcess.filter(requirementproduct__isnull=False):
            # loop through process that only have requirement product to check

            req_products = process.requirementproduct_set.all()
            if req_products.filter(product=product_in_process):
                invalid('Error in product assembly')

            for req_product in req_products:
                product = req_product.product
                
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

class ProcessSerializer(BaseProcessSerializer):
    '''
    process serializer class for managing data process when insert product
    '''
    
    requirementmaterial_set = RequirementMaterialSerializer(many=True)
    requirementproduct_set = RequirementProductSerializer(many=True)

    class Meta(BaseProcessSerializer.Meta):
        read_only_fields = ['product','order']

class ProductManagementSerializer(BaseProductSerializer):
    '''
    this serializer is used to create product nested to process then to requirement material, requirement product, warehouse product,
    '''
    
    ppic_process_related= ProcessSerializer(many=True)

    def search(self,product_in_process,manyProcess):
        
        for process in manyProcess:
            req_products = process.requirementproduct_set.all()

            for req_product in req_products:
                product = req_product.product
                if product == product_in_process:
                    invalid(f'Error in assembly product')
                
                manyProcessOfCertainProduct = product.ppic_process_related.prefetch_related(Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product')))

                self.search(product_in_process,manyProcessOfCertainProduct)

    def update(self, instance, validated_data):
        '''
        update product
        '''       
        many_process = validated_data.pop('ppic_process_related')
        len_process = len(many_process)

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
    
    class Meta(BaseProductSerializer.Meta):
        read_only_fields = ['process','last_update']


class OneDepthProductNestedOrderSerializer(OneDepthProductSerializer):
    '''
    '''
    ppic_productorder_related = OneDepthProductOrderSerializer(many=True)
    rest_order = IntegerField(read_only=True) 