from rest_framework.serializers import ModelSerializer,IntegerField,Serializer
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Prefetch

from math import ceil

from ppic.models import Machine,Operator,MaterialProductionReport,ProductProductionReport,ProductionReport,Process,ProcessType,WarehouseMaterial,WarehouseProduct,ReceiptSubcontSchedule

from manager.shortcuts import invalid



class MachineSerializer(ModelSerializer):
    '''
    a serializer for crud machine, and count all production related
    '''
    numbers_of_production = IntegerField(read_only=True)
    
    class Meta:
        model = Machine
        fields ='__all__'

class OperatorSerializer(ModelSerializer):
    '''
    a serializer for crud operator, and count all production related
    '''
    numbers_of_production = IntegerField(read_only=True)
    
    class Meta:
        model = Operator
        fields ='__all__'

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
    '''
    serializer class of production report
    '''
    productproductionreport_set = ProductProductionReportReadOnlySerializer(many=True)
    materialproductionreport_set = MaterialProductionReportReadOnlySerializer(many=True)

    class Meta:
        model = ProductionReport
        fields = '__all__'
        depth = 2        

class ProductionReportManagementSerializer(ModelSerializer):
    '''
    a serializer for cud (create,update,delete) production report, and affect to all inventory(requirement material, requirement product) related with particular process of product
    '''

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
                Process.objects.get(order = order-1, product = product)

            except ObjectDoesNotExist :
                invalid(f"Process wip{order-1} doesn't exists ")

        if process not in product.ppic_process_related.all():
            invalid(f'Invalid process')

        return super().validate(attrs)

    def validate_process(self,attrs):
        subcont_type = ProcessType.objects.get(pk=2)
        process_type = attrs.process_type
        if process_type == subcont_type:
            invalid('Cannot do production on subcont process')

        return attrs

    def validate_quantity(self,attrs):

        if attrs == 0:
            invalid('Cannot do production with zero quantity')

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

        if order > 1:
        
            prev_process = Process.objects.get(order = order-1, product = product)
            warehouse_wip = prev_process.warehouseproduct_set.filter(warehouse_type__gt = 2).get()
            
            if quantity_production > warehouse_wip.quantity:
                invalid(f'Quantity stok wip{product.name} is not enough for make production')

        
        req_product = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
        
        req_material = process.requirementmaterial_set.select_related('material__warehousematerial')
        
        self.suffciency_req_material_check(req_material,quantity_production)
        self.sufficiency_req_product_check(req_product,quantity_production)

        production_report = super().create(validated_data)

        if order > 1:
            
            prev_process = Process.objects.filter(order = order-1,product=product).prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()
            warehouse_wip = prev_process.warehouseproduct_set.get()
            warehouse_wip.quantity -= (quantity_production)
            warehouse_wip.save()
            

        req_materials = process.requirementmaterial_set.select_related('material__warehousematerial')
        req_products = process.requirementproduct_set.select_related('product').prefetch_related(
            Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))

        for req_material in req_materials:
            material = req_material.material
            wh_material = material.warehousematerial
            used_material = (quantity_production / req_material.output) * req_material.input

            wh_material.quantity -= used_material
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
        prev_quantity = instance.quantity
        current_quantity = validated_data['quantity']
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

        
        if quantity_production > prev_quantity_production:

            ## if new quantity to produce is greater than previous, check availability of inventory(requirement material, requirement product) for the rest of product to produce
            rest_quantity_to_produce = quantity_production - prev_quantity_production

            if order > 1:
                    prev_process = Process.objects.get(order = order-1, product = instance_product)
                    warehouse_wip = prev_process.warehouseproduct_set.filter(warehouse_type__gt = 2).get()
                    
                    if rest_quantity_to_produce > warehouse_wip.quantity:
                        invalid(f'Quantity stok wip {instance_product.name} is not enough for make production')
            
            req_product = process.requirementproduct_set.select_related('product').prefetch_related(
                Prefetch('product__ppic_warehouseproduct_related',queryset = WarehouseProduct.objects.filter(warehouse_type = 1)))
            
            req_material = process.requirementmaterial_set.select_related('material__warehousematerial')
            
            self.suffciency_req_material_check(req_material,rest_quantity_to_produce)
            self.sufficiency_req_product_check(req_product,rest_quantity_to_produce)



        production_report = super().update(instance, validated_data)
        production_report.last_update = timezone.now()
        production_report.save(update_fields=['last_update'])


        if order > 1:
            
            prev_process = Process.objects.filter(order = order-1,product=instance_product).prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.filter(warehouse_type__gt=2))).get()

            warehouse_wip = prev_process.warehouseproduct_set.get()
            warehouse_wip.quantity += (prev_quantity_production)
            warehouse_wip.quantity -= (quantity_production)
            warehouse_wip.save()
        

        for req_material in req_materials:
            material = req_material.material
            wh_material = material.warehousematerial
            prev_used_material = (prev_quantity_production / req_material.output) * req_material.input
            
            current_used_material = (quantity_production / req_material.output) * req_material.input

            wh_material.quantity += prev_used_material
            wh_material.quantity -= current_used_material
            
            updated['wh_material'].append(wh_material)

            for report in material_reports.filter(material=material):
                report.quantity = current_used_material
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
        wh_current_wip.quantity -= prev_quantity
        wh_current_wip.quantity += current_quantity
        
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

class ReceiptSubcontScheduleManagementSerializer(ModelSerializer):
    '''
    a serializer for cud SCHEDULE product that shipped in subconstruction
    '''
    class Meta:
        model = ReceiptSubcontSchedule
        fields = '__all__'
    
    def validate(self, attrs):

        productSubconstruction = attrs['product_subcont']
        tempQuantityReceived = 0
        quantity = attrs['quantity']

        for receivedProductSubcont in productSubconstruction.subcontreceipt_set.all():
            tempQuantityReceived += receivedProductSubcont.quantity

        numberLeftToSchedule = productSubconstruction.quantity - tempQuantityReceived

        if quantity > numberLeftToSchedule:
            invalid(f'Cannot make arrival schedule with amount of {quantity}')

        return super().validate(attrs)

    def update(self, instance, validated_data):
        if instance.fulfilled_quantity > 0:
            invalid('Jadwal tersebut sudah selesai')
        return super().update(instance, validated_data)

class MonthlyProductionReportSerializer(Serializer):
    '''
    a serializer for get total quantity production on every month
    '''
    date__year = IntegerField()
    date__month = IntegerField()
    total_production = IntegerField()
