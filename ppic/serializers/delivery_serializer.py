from rest_framework.serializers import ModelSerializer,IntegerField,CharField

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Prefetch

from math import ceil

from manager.shortcuts import invalid

from ppic.models import DeliveryNoteCustomer,ProductDeliverCustomer,DeliveryNoteSubcont,ProductDeliverSubcont,RequirementMaterialSubcont,RequirementProductsubcont,ReceiptSubcontSchedule,Process,WarehouseMaterial,WarehouseProduct,Driver,Vehicle


class BaseDeliveryNoteCustomerSerializer(ModelSerializer):
    '''
    base deliveries customer serializer class
    '''
    note = CharField(allow_blank=True)

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code',instance.code)
        instance.note = validated_data.get('note',instance.note)
        instance.driver = validated_data.get('driver',instance.driver)
        instance.vehicle = validated_data.get('vehicle',instance.vehicle)
        instance.date = validated_data.get('date',instance.date)
        instance.last_update = timezone.now()
        instance.save()

        return instance
    
    class Meta:
        model = DeliveryNoteCustomer
        fields = '__all__'
        read_only_fields = ['last_update']

class BaseDeliveryNoteSubcontSerializer(ModelSerializer):
    '''
    seriz for management delivery note product SUBCONSTRUCTION
    '''
    note = CharField(allow_blank=True)

    def update(self, instance, validated_data):

        instance.code = validated_data.get('code',instance.code)
        instance.note = validated_data.get('note',instance.note)
        instance.driver = validated_data.get('driver',instance.driver)
        instance.vehicle = validated_data.get('vehicle',instance.vehicle)
        instance.date = validated_data.get('date',instance.date)
        instance.last_update = timezone.now()

        instance.save()

        return instance

    class Meta:
        model = DeliveryNoteSubcont
        fields= '__all__'
        read_only_fields = ['last_update']

class BaseProductDeliveryCustomerSerializer(ModelSerializer):
    '''
    base product shipped customer serializer class
    '''

    class Meta:
        model = ProductDeliverCustomer
        fields = '__all__'

class TwoDepthProductDeliverCustomerSerializer(BaseProductDeliveryCustomerSerializer):
    '''
    seriz for get data product delivery depth to 2 relations below
    '''

    class Meta(BaseProductDeliveryCustomerSerializer.Meta):
        depth = 2

class OneDepthDeliveryNoteCustomerSerializer(BaseDeliveryNoteCustomerSerializer):
    '''
    seriz for get data delivery note
        nested to its product shipped
    '''
    productdelivercustomer_set = TwoDepthProductDeliverCustomerSerializer(many=True)

    class Meta(BaseDeliveryNoteCustomerSerializer.Meta):
        depth = 1

class RequirementMaterialSubcontSerializer(ModelSerializer):
    '''
    serializer for get nested requirement material for delivery product subconstruction
    '''

    class Meta:
        model = RequirementMaterialSubcont
        fields = '__all__'
        depth = 2

class RequirementProductSubcontSerializer(ModelSerializer):
    '''
    serializer for get nested requirement product for delivery product subconstruction
    '''

    class Meta:
        model = RequirementProductsubcont
        fields ='__all__'
        depth = 2

class ReceiptSubcontScheduleReadOnlySerializer(ModelSerializer):
    '''
    a serializer for get nested schedule of product in subconstruction
    '''

    class Meta:
        model = ReceiptSubcontSchedule
        fields = '__all__'

class ProductDeliverSubcontReadOnlySerializer(ModelSerializer):
    '''
    a serializer for get and retrieve product that delivered to subconstruction
    '''
    requirementmaterialsubcont_set = RequirementMaterialSubcontSerializer(many=True)
    requirementproductsubcont_set = RequirementProductSubcontSerializer(many=True)
    received = IntegerField(read_only=True)
    receiptsubcontschedule_set = ReceiptSubcontScheduleReadOnlySerializer(many=True)

    class Meta:
        model = ProductDeliverSubcont
        fields = '__all__'
        depth = 2

class OneDepthDeliveryNoteSubcontSerializer(BaseDeliveryNoteSubcontSerializer):
    '''
    a serializer for get and retrieve delivery note subconstruction
    '''
    productdeliversubcont_set = ProductDeliverSubcontReadOnlySerializer(many=True)

    class Meta(BaseDeliveryNoteSubcontSerializer.Meta):
        depth = 1

class ProductDeliverySubcontManagementSerializer(ModelSerializer):
    '''
    seriz for management delivery product subcont
    '''
    description = CharField(allow_blank=True)
    requirementmaterialsubcont_set = RequirementMaterialSubcontSerializer(many=True,read_only=True)
    requirementproductsubcont_set = RequirementProductSubcontSerializer(many=True,read_only=True)

    def suffciency_req_material_check(self,req_materials,production_quantity:int):
        
        for req_material in req_materials:
            wh_material = req_material.material.warehousematerial
            stock_in_wh = wh_material.quantity
            used_material = (production_quantity / req_material.output) * req_material.input
            if used_material > stock_in_wh:
                invalid(f'Jumlah stok {req_material.material.name} tidak cukup')
 

    def sufficiency_req_product_check(self,req_products,production_quantity:int):
        
        for req_product in req_products:
            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.first()
            stock_in_whproduct = wh_product.quantity
            used_product = (production_quantity/req_product.output) * req_product.input
            if used_product > stock_in_whproduct:
                invalid(f'Jumlah stok produk {product.name} tidak cukup')

    def validate(self, attrs):

        product = attrs['product']
        process = attrs['process']
        order = process.order

        if order > 1:
            
            try:
                Process.objects.filter(order = order-1,product=product).prefetch_related(
                    Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()
            
            except ObjectDoesNotExist:
                invalid(f"Process wip{order-1} doesn't exists")

        if process not in product.ppic_process_related.all():
            invalid(f"This process doesn't belongs to wip of {product.name}")

        if process.process_type.id != 2:
            invalid('Delivery only allowed in the subconstruction process')

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

        if order > 1:
        
            prev_process = Process.objects.filter(order = order-1,product=product).prefetch_related(Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()
            warehouse_wip = prev_process.warehouseproduct_set.first()
            if quantity_delivery > warehouse_wip.quantity:
                invalid(f'Quantity stock of {product.name} is not enough to make this delivery')

        
        req_product = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_material = process.requirementmaterial_set.select_related('material__warehousematerial')

        self.suffciency_req_material_check(req_material,quantity_delivery)
        self.sufficiency_req_product_check(req_product,quantity_delivery)

        productDeliverSubcont = super().create(validated_data)

        if order > 1:

            prev_process = Process.objects.filter(order = order-1,product=product).prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()

            warehouse_wip = prev_process.warehouseproduct_set.first()
            warehouse_wip.quantity -= (quantity_delivery)
            warehouse_wip.save()
         
        warehouse_subcont = process.warehouseproduct_set.filter(warehouse_type = 2).get()
        warehouse_subcont.quantity += (quantity_delivery)
        warehouse_subcont.save()
        
        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))

        for req_material in req_materials:
            material = req_material.material
            wh_material = material.warehousematerial
            used_material = (quantity_delivery / req_material.output) * req_material.input

            wh_material.quantity -= used_material
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

        requirement_material_subcont = instance.requirementmaterialsubcont_set.select_related('material')
        requirement_product_subcont = instance.requirementproductsubcont_set.select_related('product')

        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_mats = [x.material for x in req_materials]
        req_prod = [x.product for x in req_products]


        for report in requirement_material_subcont:
            try:
                req_mats.remove(report.material)
            except:
                self.invalid_requirement()

        for report in requirement_product_subcont:
            try:
                req_prod.remove(report.product)
            except:
                self.invalid_requirement()

        if len(req_mats) > 0:
            self.invalid_requirement()
        if len(req_prod) > 0:
            self.invalid_requirement()

        return req_materials,req_products,requirement_material_subcont,requirement_product_subcont

    
    def invalid_requirement(self):

        return invalid('Cannot change delivery product subcont, because material requirements or product requirements in this subcont process have changed')

    def update(self, instance, validated_data):
        '''
        update product delivery subconstruction to customer, then update every requirement product, requirement material, and also update stock in warehouse
        '''
        
        prev_quantity_delivery = instance.quantity 
        quantity_delivery = validated_data['quantity'] 
        instance_product = instance.product
        process = instance.process
        req_materials,req_products,material_reports,product_reports = self.requirement_check(instance)
        order = process.order

        if quantity_delivery > prev_quantity_delivery:

            ## if new quantity to send is greater than previous, check availability rest quantity to send is sufficent or not
            rest_quantity_product_to_proceed = quantity_delivery - prev_quantity_delivery

            if order > 1:
            
                prev_process = Process.objects.filter(order = order-1,product=instance_product).prefetch_related(Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()
                warehouse_wip = prev_process.warehouseproduct_set.first()
                if rest_quantity_product_to_proceed > warehouse_wip.quantity:
                    invalid(f'Quantity stock of {instance_product.name} is not enough to make this delivery')

            
            req_product = process.requirementproduct_set.select_related('product').prefetch_related(
                Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
            
            req_material = process.requirementmaterial_set.select_related('material__warehousematerial')

            self.suffciency_req_material_check(req_material,rest_quantity_product_to_proceed)
            self.sufficiency_req_product_check(req_product,rest_quantity_product_to_proceed)


        total_quantity_received = 0
        for received_subcont in instance.subcontreceipt_set.all():
            ## check if product received from subcont is greater than quantity that want to update

            total_quantity_received += received_subcont.quantity
            if total_quantity_received > quantity_delivery:
                invalid('Error when updating product subconstruction')


        updated = {
            'wh_material':[],
            'wh_product':[],
            'material_reports':[],
            'product_reports':[],
        }

        product_delivery_subcont = super().update(instance, validated_data)
        
        if order > 1:
            
            prev_process = Process.objects.filter(order = order-1,product=instance_product).prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()

            warehouse_wip = prev_process.warehouseproduct_set.get()
            warehouse_wip.quantity += (prev_quantity_delivery)
            warehouse_wip.quantity -= (quantity_delivery)
            warehouse_wip.save()
        

        for req_material in req_materials:
            ## loop each requirement material that become requirement of this process subcont

            material = req_material.material
            wh_material = material.warehousematerial
            prev_used_material = (prev_quantity_delivery / req_material.output) * req_material.input

            current_used_material = (quantity_delivery / req_material.output) * req_material.input
            

            wh_material.quantity += prev_used_material
            wh_material.quantity -= current_used_material
            
            
            updated['wh_material'].append(wh_material)

            for report in material_reports.filter(material=material):
                report.quantity = current_used_material
                updated['material_reports'].append(report)
                

        for req_product in req_products:
            ## loop each requirement material that become requirement of this process subcont

            product = req_product.product
            wh_product = product.ppic_warehouseproduct_related.get()
            prev_used_product = ceil((prev_quantity_delivery / req_product.output) * req_product.input)
            used_product = ceil((quantity_delivery / req_product.output) * req_product.input)

            wh_product.quantity += prev_used_product
            wh_product.quantity -= used_product

            updated['wh_product'].append(wh_product)

            for report in product_reports.filter(product=product):
                report.quantity = used_product
                updated['product_reports'].append(report)
                


        wh_subcont = process.warehouseproduct_set.filter(warehouse_type = 2).get()
        wh_subcont.quantity -= prev_quantity_delivery
        wh_subcont.quantity += quantity_delivery
        
        updated['wh_product'].append(wh_subcont)

        WarehouseProduct.objects.bulk_update(updated['wh_product'],['quantity'])
        WarehouseMaterial.objects.bulk_update(updated['wh_material'],['quantity'])

        RequirementMaterialSubcont.objects.bulk_update(updated['material_reports'],['quantity'])
        RequirementProductsubcont.objects.bulk_update(updated['product_reports'],['quantity'])


        return product_delivery_subcont

    class Meta:
        model = ProductDeliverSubcont
        fields = '__all__'


class ProductDeliverCustomerManagementSerializer(ModelSerializer):
    '''
    seriz for management product delivery
    '''
    description = CharField(allow_blank=True)
    
    def validate_product_order(self,attrs):
        if attrs.delivered > attrs.ordered:
            invalid('Semua product yang dipesan telah dikirim')

        return attrs
    
    def validate(self, attrs):
        customer_from_delivery_note = attrs['delivery_note_customer'].customer
        customer_from_po = attrs['product_order'].sales_order.customer

        if customer_from_delivery_note != customer_from_po:
            invalid(f'This order is not from {customer_from_delivery_note.name} ')

        return super().validate(attrs)
    
    def fluence_stock(self,po,wh_product,quantity):

        wh_product.quantity -= quantity
        po.delivered += quantity
        po.save()
        wh_product.save()

    def fluence_stock_update(self,po,wh_product,old_quantity,new_quantity):
        
        wh_product.quantity += old_quantity
        po.delivered -= old_quantity

        self.fluence_stock(po,wh_product,new_quantity)

    def update(self, instance, validated_data):
        
        po = validated_data['product_order']
        rest_quantity_product_to_shipped = po.ordered - po.delivered
        wh_product = po.product.ppic_warehouseproduct_related.get(warehouse_type=1)

        if validated_data['quantity'] > (rest_quantity_product_to_shipped+instance.quantity):
            invalid('the number of shipments exceeds the number of orders')
        
        if validated_data['quantity'] > (wh_product.quantity+instance.quantity):
            invalid('Insufficient stock of finished goods to make delivery')

        validated_data.pop('schedules',None)
        instance_schedules = instance.schedules
        if instance_schedules is not None:
            instance_schedules.fulfilled_quantity -= instance.quantity
            instance_schedules.fulfilled_quantity += validated_data['quantity']
            instance_schedules.save()

        self.fluence_stock_update(instance.product_order,wh_product,instance.quantity,validated_data['quantity'])
        instance.quantity = validated_data.get('quantity',instance.quantity)
        instance.description = validated_data.get('description',instance.description)
        instance.save()

        return instance

    def create(self, validated_data):
        
        po = validated_data['product_order']
        rest_product_to_shipped = po.ordered - po.delivered
        wh_product = po.product.ppic_warehouseproduct_related.get(warehouse_type=1)

        if validated_data['quantity'] > rest_product_to_shipped:
            invalid('the number of shipments exceeds the number of orders')
        
        if validated_data['quantity'] > wh_product.quantity:
            invalid('Insufficient stock of finished goods to make delivery')

        self.fluence_stock(po,wh_product,validated_data['quantity'])
        schedules = validated_data.get('schedules',None)
        
        if schedules is not None:
            ## if product delivery inputted from schedule

            schedules.fulfilled_quantity += validated_data['quantity']
            schedules.save()

        return super().create(validated_data)

    class Meta:
        model = ProductDeliverCustomer
        fields = '__all__'

class BaseDriverSerializer(ModelSerializer):
    '''
    a serializer for crud driver, and count all delivery with each driver
    '''
    numbers_of_delivery_customer = IntegerField(read_only=True)
    numbers_of_delivery_subcont = IntegerField(read_only=True)
    
    class Meta:
        model = Driver
        fields = '__all__'

class BaseVehicleSerializer(ModelSerializer):
    '''
    a serializer for crud vehicle, and count all delivery related
    '''
    numbers_of_delivery_customer = IntegerField(read_only=True)
    numbers_of_delivery_subcont = IntegerField(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'

class OneDepthProductDeliverSubcontSerializer(ModelSerializer):
    '''
    a serializer for get all list of product that in subconstrucion
    '''
    received = IntegerField(read_only=True)
    
    class Meta:
        model = ProductDeliverSubcont
        fields = '__all__'
        depth = 1
