from pyexpat import model
from django.utils import timezone
from django.db import models
from marketing.models import AbstractCustomer,SalesOrder
from purchasing.models import AbstractSupplier,PurchaseOrderMaterial
from manager.models import AbstractCreated, AbstractQuantity,AbstractDelivery,AbstractCode,AbstractSchedule,AbstractType
# Create your models here.

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

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True

class Product(AbstractStuff,AbstractCode,AbstractCustomer):
    '''
    '''
    type = models.ForeignKey(ProductType,on_delete=models.CASCADE)
    process = models.PositiveSmallIntegerField()
    price = models.PositiveBigIntegerField(blank=True)
    
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
    delivered = models.PositiveBigIntegerField(default=0)
    done = models.BooleanField(default=False)


class DeliverySchedule(AbstractSchedule):
    '''
    schedule delivery for each product order
    '''
    product_order = models.ForeignKey(ProductOrder,on_delete=models.CASCADE)
    

class Material(AbstractStuff,AbstractSupplier):
    '''
    '''
    spec = models.CharField(max_length=150)
    length = models.FloatField(blank=True)
    width = models.FloatField(blank=True)
    thickness = models.FloatField(blank=True)
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
    quantity_input = models.PositiveIntegerField()
    material_input = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='report_material_inputs')
    quantity_output = models.PositiveIntegerField()
    material_output = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='report_material_outputs')
    last_update = models.DateTimeField(blank=True,null=True)
    

class WarehouseMaterial(AbstractWarehouse):
    '''
    every material stock are store in this table
    '''
    material = models.OneToOneField(Material,on_delete=models.CASCADE)
    

class WarehouseScrapMaterial(models.Model):
    '''
    leftover material of the productions
    '''
    material = models.OneToOneField(Material,on_delete=models.CASCADE)
    quantity = models.FloatField()

class Process(AbstractProduct):
    '''
    work in process
    '''
    process_type = models.ForeignKey(ProcessType,on_delete=models.CASCADE)
    process_name = models.CharField(max_length=150)
    order = models.PositiveIntegerField()
    class Meta(AbstractProduct.Meta):
        ordering = ['order']

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


class DeliveryNoteSubcont(AbstractDeliveryNote,AbstractSupplier):
    '''
    model to save all delivery note subcont to supplier,
    '''
    class Meta(AbstractDeliveryNote.Meta,AbstractSupplier.Meta):
        pass


class DeliveryNoteCustomer(AbstractDeliveryNote,AbstractCustomer):
    '''
    model to save delivery note product to supplier
    '''
    class Meta(AbstractCustomer.Meta,AbstractDeliveryNote.Meta):
        pass



class ProductDeliverSubcont(AbstractQuantity,AbstractProduct):
    '''
    model to handle all product subcont shipped on each delivery note
    '''
    deliver_note_subcont = models.ForeignKey(DeliveryNoteSubcont,on_delete=models.CASCADE)
    
    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass


class ProductDeliverCustomer(AbstractQuantity):
    '''
    model to handle all product shipped on each delivery note
    '''
    product_order = models.ForeignKey(ProductOrder,on_delete=models.CASCADE)
    delivery_note_customer = models.ForeignKey(DeliveryNoteCustomer,on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
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
    quantity_production = models.PositiveIntegerField() #quantity product that want to be producted
    
    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass

class MaterialOrder(AbstractMaterial):
    '''
    responsible for all data purchase material of every purchase order
    '''
    purchase_order_material = models.ForeignKey(PurchaseOrderMaterial,on_delete=models.CASCADE)
    ordered = models.PositiveBigIntegerField()
    arrived = models.PositiveBigIntegerField(default=0)
    done = models.BooleanField(default=False)


class MaterialReceiptSchedule(AbstractSchedule):
    '''
    schedule for material arrive
    '''
    material_order = models.ForeignKey(MaterialOrder,on_delete=models.CASCADE)


class DeliveryNoteMaterial(AbstractDelivery,AbstractSupplier):
    '''
    delivery note that inputted when material receipt
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


class ProductionReport(AbstractProduct,AbstractCreated,AbstractQuantity):
    '''
    report for every production
    '''
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    quantity_not_good = models.PositiveBigIntegerField(default=0)
    operator = models.ForeignKey(Operator,on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine,on_delete=models.CASCADE)
    last_update = models.DateTimeField(blank=True,null=True)

    class Meta(AbstractProduct.Meta,AbstractCreated.Meta,AbstractQuantity.Meta):
        pass

class MaterialProductionReport(AbstractQuantity,AbstractMaterial):
    '''
    hold data for quantity of material that used in particular production
    '''
    production_report = models.ForeignKey(ProductionReport,on_delete=models.CASCADE)

    class Meta(AbstractQuantity.Meta,AbstractMaterial.Meta):
        pass


class ProductProductionReport(AbstractQuantity,AbstractProduct):
    '''
    handle all data for quantity product that used in particular production
    '''
    production_report = models.ForeignKey(ProductionReport,on_delete=models.CASCADE)

    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass






