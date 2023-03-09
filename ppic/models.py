from django.utils import timezone
from django.db import models
from marketing.models import AbstractCustomer,SalesOrder
from purchasing.models import AbstractSupplier,PurchaseOrderMaterial
from manager.models import AbstractCreated, AbstractQuantity,AbstractDelivery,AbstractCode,AbstractSchedule,AbstractType

from datetime import date

class Driver(models.Model):
    name = models.CharField(max_length=200)

class Vehicle(models.Model):
    license_part_number = models.CharField(max_length=50)


class Operator(AbstractType):
    pass

class Machine(AbstractType):
    pass

class ProductType(AbstractType):
    pass

class UnitOfMaterial(AbstractType):
    pass



class WarehouseType(AbstractType):
    pass

class ProcessType(AbstractType):
    pass

class AbstractWarehouse(models.Model):
    quantity = models.PositiveBigIntegerField(default=0)
    class Meta:
        abstract = True

    def __str__(self) -> str:
        return str(self.quantity)


class AbstractStuff(AbstractCreated):
    name = models.CharField(max_length=255)
    weight = models.FloatField(blank=True)
    image = models.ImageField(upload_to="images/",blank=True)
    last_update = models.DateTimeField(blank=True,null=True)
    price = models.PositiveBigIntegerField(default=0)

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True

class ProductManager(models.Manager):
    '''
    manager for product model
    '''
    def get_queryset_related(self) -> models.QuerySet:
        '''
        method for get related data of product by select_related
        '''
        return self.select_related('customer','type')

class Product(AbstractStuff,AbstractCode,AbstractCustomer):
    '''
    '''
    objects = ProductManager()

    type = models.ForeignKey(ProductType,on_delete=models.CASCADE)
    process = models.PositiveSmallIntegerField()
    
    class Meta(AbstractCode.Meta,AbstractStuff.Meta,AbstractCustomer.Meta):
        pass

class AbstractProduct(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss",)

    class Meta:
        abstract = True

class ProductOrder(AbstractProduct):
    '''
    '''
    sales_order = models.ForeignKey(SalesOrder,on_delete=models.CASCADE)
    ordered = models.PositiveBigIntegerField()
    price = models.PositiveBigIntegerField(default=0)
    delivered = models.PositiveBigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.price is None or self.price == 0:
            self.price = self.product.price
        super(ProductOrder, self).save(*args, **kwargs)

class DeliveryScheduleManager(models.Manager):
    '''
    extend default manager for delivery schedule
    '''
    def get_queryset_three_depth_related(self) -> models.QuerySet:
        '''
        method that return queryset with three depth relations
        '''
        return self.select_related('product_order','product_order__product','product_order__product__customer','product_order__product__type','product_order__sales_order','product_order__sales_order__customer')

class DeliverySchedule(AbstractSchedule):
    '''
    schedule delivery for each product order
    '''
    objects = DeliveryScheduleManager()

    product_order = models.ForeignKey(ProductOrder,on_delete=models.CASCADE)

class MaterialManager(models.Manager):
    '''
    extend manager of material model
    '''

    def get_queryset_related(self) -> models.QuerySet:
        return self.select_related('uom','supplier','warehousematerial')

class Material(AbstractStuff,AbstractSupplier):
    '''
    '''
    objects = MaterialManager()

    spec = models.CharField(max_length=150)
    length = models.FloatField(blank=True,null=True)
    width = models.FloatField(blank=True,null=True)
    thickness = models.FloatField(blank=True,null=True)
    berat_jenis = models.FloatField(blank=True,null=True)
    uom = models.ForeignKey(UnitOfMaterial,on_delete=models.CASCADE)
    
    class Meta(AbstractStuff.Meta,AbstractSupplier.Meta):
        pass

class AbstractMaterial(models.Model):
    material = models.ForeignKey(Material,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss",)

    class Meta:
        abstract = True

class ConversionUom(models.Model):
    uom_input = models.ForeignKey(UnitOfMaterial,on_delete=models.CASCADE,related_name='uom_inputs')
    uom_output = models.ForeignKey(UnitOfMaterial,on_delete=models.CASCADE,related_name='uom_outputs')
    
    class Meta:
        unique_together = [['uom_input','uom_output']]

class BasedConversionMaterial(models.Model):
    quantity_input = models.PositiveIntegerField()
    material_input = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='based_material_inputs')
    quantity_output = models.PositiveIntegerField()
    material_output = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='based_material_outputs')
    
    class Meta:
        unique_together = [['material_input','material_output']]

class ConversionMaterialReport(AbstractCreated):
    quantity_input = models.FloatField()
    material_input = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='report_material_inputs')
    quantity_output = models.PositiveIntegerField()
    material_output = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='report_material_outputs')
    last_update = models.DateTimeField(blank=True,null=True)
    

class WarehouseMaterial(models.Model):
    '''
    every material stock are store in this table
    '''
    quantity = models.FloatField(default=0)
    material = models.OneToOneField(Material,on_delete=models.CASCADE)
    def __str__(self) -> str:

        return str(self.quantity)
    
class Process(AbstractProduct):
    '''
    work in process
    '''
    process_type = models.ForeignKey(ProcessType,on_delete=models.CASCADE)
    process_name = models.CharField(max_length=150)
    order = models.PositiveIntegerField()
    class Meta(AbstractProduct.Meta):
        ordering = ['order']
        unique_together = [['order','product']]

class WarehouseProduct(AbstractWarehouse,AbstractProduct):
    '''
    '''
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    warehouse_type = models.ForeignKey(WarehouseType,on_delete=models.CASCADE)
    class Meta(AbstractWarehouse.Meta,AbstractProduct.Meta):
        unique_together = [['warehouse_type','process']]

class AbstractRequirement(models.Model):
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    input = models.PositiveBigIntegerField(default=1)
    output = models.PositiveBigIntegerField(default=1)
    class Meta:
        abstract = True

class RequirementProduct(AbstractRequirement,AbstractProduct):
    class Meta(AbstractRequirement.Meta,AbstractProduct.Meta):
        pass

class RequirementMaterial(AbstractRequirement,AbstractMaterial):
    class Meta(AbstractRequirement.Meta,AbstractMaterial.Meta):
        pass


class AbstractDeliveryNote(AbstractDelivery):
    '''
    abstract class for every delivery note, prevent reinvent the wheel
    '''
    driver = models.ForeignKey(Driver,on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle,on_delete=models.CASCADE)

    class Meta:
        abstract = True

class DeliveryNoteSubcontManager(models.Manager):
    '''
    '''
    def get_queryset_related(self) -> models.QuerySet:
        return self.select_related('supplier','vehicle','driver')

class DeliveryNoteSubcont(AbstractDeliveryNote,AbstractSupplier):
    '''
    model to save all delivery note subcont to supplier,
    '''
    objects = DeliveryNoteSubcontManager()

    class Meta(AbstractDeliveryNote.Meta,AbstractSupplier.Meta):
        pass

class DeliveryNoteCustomerManager(models.Manager):
    '''
    '''
    def get_queryset_related(self) -> models.QuerySet:
        return self.select_related('customer','vehicle','driver')

class DeliveryNoteCustomer(AbstractDeliveryNote,AbstractCustomer):
    '''
    model to save delivery note product to supplier
    '''

    objects = DeliveryNoteCustomerManager()

    class Meta(AbstractCustomer.Meta,AbstractDeliveryNote.Meta):
        pass



class ProductDeliverSubcont(AbstractQuantity,AbstractProduct):
    '''
    model to handle all product subcont shipped on each delivery note
    '''
    deliver_note_subcont = models.ForeignKey(DeliveryNoteSubcont,on_delete=models.CASCADE)
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    description = models.TextField(default='')
    
    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass

class RequirementProductsubcont(AbstractProduct,AbstractQuantity):
    '''
    '''
    product_subcont = models.ForeignKey(ProductDeliverSubcont,on_delete=models.CASCADE)
    class Meta(AbstractProduct.Meta,AbstractQuantity.Meta):
        pass

class RequirementMaterialSubcont(AbstractMaterial):
    '''
    '''
    quantity = models.FloatField()
    product_subcont = models.ForeignKey(ProductDeliverSubcont,on_delete=models.CASCADE)
    class Meta(AbstractMaterial.Meta,AbstractQuantity.Meta):
        pass

class ReceiptSubcontSchedule(AbstractSchedule):
    '''
    schedule for receipt of product SUBCONSTRUCTION
    '''
    product_subcont = models.ForeignKey(ProductDeliverSubcont,on_delete=models.CASCADE)

class ProductDeliverCustomerManager(models.Manager):
    '''
    extend default manager for product deliver customer
    '''
    def get_queryset_two_depth_related(self)->models.QuerySet:
        '''
        method that return queryset with two depth relations
        '''
        return self.select_related('product_order','product_order__product','product_order__sales_order','delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver')

class ProductDeliverCustomer(AbstractQuantity):
    '''
    model to handle all product shipped on each delivery note
    '''
    objects = ProductDeliverCustomerManager()

    product_order = models.ForeignKey(ProductOrder,on_delete=models.CASCADE)
    delivery_note_customer = models.ForeignKey(DeliveryNoteCustomer,on_delete=models.CASCADE)
    description = models.TextField(default='')
    schedules = models.OneToOneField(DeliverySchedule,blank=True,null=True,on_delete=models.SET_NULL)

class MaterialRequirementPlanning(AbstractQuantity,AbstractMaterial,AbstractCreated):
    '''
    all requirement material for production
    '''
    last_update = models.DateTimeField(blank=True,null=True)
    class Meta(AbstractQuantity.Meta,AbstractMaterial.Meta,AbstractCreated.Meta):
        pass

class DetailMrp(AbstractQuantity,AbstractProduct):
    '''
    quantity stands for quantity of material that will used in particular product
    '''

    mrp = models.ForeignKey(MaterialRequirementPlanning,on_delete=models.CASCADE)
    quantity_production = models.PositiveIntegerField(default=0) #quantity product that want to be producted
    
    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass

class MaterialOrderManager(models.Manager):
    '''
    extend default manager for material order
    '''
    def get_queryset_two_depth_related(self) -> models.query:
        '''
        get queryset for material order two depth of relations
        '''
        return self.select_related('material','purchase_order_material','material__uom','material__supplier','purchase_order_material__supplier')

class MaterialOrder(AbstractMaterial):
    '''
    responsible for all data purchase material of every purchase order
    '''
    objects = MaterialOrderManager()

    purchase_order_material = models.ForeignKey(PurchaseOrderMaterial,on_delete=models.CASCADE)
    ordered = models.PositiveBigIntegerField()
    to_product = models.ForeignKey(Product,on_delete=models.CASCADE,blank=True,null=True)
    price = models.PositiveBigIntegerField(default=0)
    arrived = models.PositiveBigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.price is None or self.price == 0:
            self.price = self.material.price
        super(MaterialOrder, self).save(*args, **kwargs)

class MaterialReceiptScheduleManager(models.Manager):
    '''
    manager for material receipt schedules
    '''
    def get_queryset_three_depth_related(self) -> models.QuerySet:
        '''
        method to get 3 deep dive of material receipt schedule
        '''
        return self.select_related('material_order','material_order__material','material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier')

class MaterialReceiptSchedule(AbstractSchedule):
    '''
    schedule for material arrive
    '''

    objects = MaterialReceiptScheduleManager()

    material_order = models.ForeignKey(MaterialOrder,on_delete=models.CASCADE)


class DeliveryNoteMaterial(AbstractDelivery,AbstractSupplier):
    '''
    receipt note
    '''
    image = models.ImageField(upload_to="images/",blank=True)
    class Meta(AbstractDelivery.Meta,AbstractSupplier.Meta):
        pass


class MaterialReceipt(AbstractQuantity):
    '''
    material receipt even its in schedule or not
    '''
    delivery_note_material = models.ForeignKey(DeliveryNoteMaterial,on_delete=models.CASCADE)
    material_order = models.ForeignKey(MaterialOrder,on_delete=models.CASCADE)
    schedules = models.OneToOneField(MaterialReceiptSchedule,blank=True,null=True,on_delete=models.SET_NULL)

class ReceiptNoteSubcont(AbstractDelivery,AbstractSupplier):
    '''
    receipt note for product subconstruction
    '''
    image = models.ImageField(upload_to='images/',blank=True)
    class Meta(AbstractDelivery.Meta,AbstractSupplier.Meta):
        pass

class SubcontReceipt(AbstractQuantity):
    '''
    table for all product received from subconstruction
    '''
    receipt_note = models.ForeignKey(ReceiptNoteSubcont,on_delete=models.CASCADE)
    product_subcont = models.ForeignKey(ProductDeliverSubcont,on_delete=models.CASCADE)
    schedules = models.OneToOneField(ReceiptSubcontSchedule,blank=True,null=True,on_delete=models.SET_NULL)
    quantity_not_good = models.PositiveBigIntegerField(default=0)


class ProductionReport(AbstractProduct,AbstractCreated,AbstractQuantity):
    '''
    report for every production
    '''
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    quantity_not_good = models.PositiveBigIntegerField(default=0)
    operator = models.ForeignKey(Operator,on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine,on_delete=models.CASCADE)
    last_update = models.DateTimeField(blank=True,null=True)
    date = models.DateField(default=date.today)

    class Meta(AbstractProduct.Meta,AbstractCreated.Meta,AbstractQuantity.Meta):
        pass

class MaterialProductionReport(AbstractMaterial):
    '''
    hold data for quantity of material that used in particular production
    '''
    quantity = models.FloatField()
    production_report = models.ForeignKey(ProductionReport,on_delete=models.CASCADE)

    class Meta(AbstractMaterial.Meta):
        pass


class ProductProductionReport(AbstractQuantity,AbstractProduct):
    '''
    handle all data for quantity product that used in particular production
    '''
    production_report = models.ForeignKey(ProductionReport,on_delete=models.CASCADE)

    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass






