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


class AbstractWarehouse(AbstractQuantity):
    warehouse_type = models.ForeignKey(WarehouseType,on_delete=models.CASCADE)

    class Meta:
        abstract = True



class AbstractStuff(models.Model):
    name = models.CharField(max_length=255)
    weight = models.FloatField()
    image = models.ImageField(upload_to="images/",blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True

class Product(AbstractStuff,AbstractCode,AbstractCustomer):
    type = models.ForeignKey(ProductType,on_delete=models.CASCADE)
    process = models.PositiveSmallIntegerField()
    price = models.PositiveBigIntegerField(blank=True)
    
    class Meta(AbstractCode.Meta,AbstractStuff.Meta,AbstractCustomer.Meta):
        pass

class AbstractProduct(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss",)

    class Meta:
        abstract = True

class WarehouseProduct(AbstractWarehouse,AbstractProduct):
    
    class Meta(AbstractWarehouse.Meta,AbstractProduct.Meta):
        unique_together = [['warehouse_type','product']]

class ProductOrder(AbstractProduct):
    sales_order = models.ForeignKey(SalesOrder,on_delete=models.CASCADE)
    ordered = models.PositiveBigIntegerField()
    delivered = models.PositiveBigIntegerField()


class DeliverySchedule(AbstractSchedule):
    product_order = models.ForeignKey(ProductOrder,on_delete=models.CASCADE)
    

class Material(AbstractStuff,AbstractSupplier):
    spec = models.CharField(max_length=150)
    length = models.FloatField()
    width = models.FloatField()
    thickness = models.FloatField()
    uom = models.ForeignKey(UnitOfMaterial,on_delete=models.CASCADE)
    
    class Meta(AbstractStuff.Meta,AbstractSupplier.Meta):
        pass

class AbstractMaterial(models.Model):
    material = models.ForeignKey(Material,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s_related",related_query_name="%(app_label)s_%(class)ss",)

    class Meta:
        abstract = True


class WarehouseMaterial(AbstractWarehouse,AbstractMaterial):
   
    class Meta(AbstractWarehouse.Meta,AbstractMaterial.Meta):
        unique_together = [['warehouse_type','material']]


class Process(AbstractProduct):
    process_type = models.ForeignKey(ProcessType,on_delete=models.CASCADE)
    process_name = models.CharField(max_length=150)
    order = models.PositiveIntegerField()


class AbstractRequirement(models.Model):
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    conversion = models.FloatField()
    
    class Meta:
        abstract = True

class RequirementProduct(AbstractRequirement,AbstractProduct):
    
    class Meta(AbstractRequirement.Meta,AbstractProduct.Meta):
        pass

class RequirementMaterial(AbstractRequirement,AbstractMaterial):
    
    class Meta(AbstractRequirement.Meta,AbstractMaterial.Meta):
        pass


class AbstractDeliveryNote(AbstractDelivery):
    driver = models.ForeignKey(Driver,on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle,on_delete=models.CASCADE)

    class Meta:
        abstract = True


class DeliveryNoteSubcont(AbstractDeliveryNote,AbstractSupplier):
    
    class Meta(AbstractDeliveryNote.Meta,AbstractSupplier.Meta):
        pass


class DeliveryNoteCustomer(AbstractDeliveryNote,AbstractCustomer):
    
    class Meta(AbstractCustomer.Meta,AbstractDeliveryNote.Meta):
        pass



class ProductDeliverSubcont(AbstractQuantity,AbstractProduct):
    deliver_note_subcont = models.ForeignKey(DeliveryNoteSubcont,on_delete=models.CASCADE)
    
    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass


class ProductDeliverCustomer(AbstractQuantity):
    product_order = models.ForeignKey(ProductOrder,on_delete=models.CASCADE)
    delivery_note_customer = models.ForeignKey(DeliveryNoteCustomer,on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)


class MaterialRequirementPlanning(AbstractQuantity,AbstractMaterial):
    
    class Meta(AbstractQuantity.Meta,AbstractMaterial.Meta):
        pass

class DetailMrp(AbstractQuantity,AbstractProduct):
    mrp = models.ForeignKey(MaterialRequirementPlanning,on_delete=models.CASCADE)
    quantity_production = models.PositiveIntegerField()
    
    class Meta(AbstractQuantity.Meta,AbstractProduct.Meta):
        pass

class MaterialOrder(AbstractMaterial):
    purchase_order_material = models.ForeignKey(PurchaseOrderMaterial,on_delete=models.CASCADE)
    ordered = models.PositiveBigIntegerField()
    arrived = models.PositiveBigIntegerField()


class MaterialReceiptSchedule(AbstractSchedule):
    material_order = models.ForeignKey(MaterialOrder,on_delete=models.CASCADE)


class DeliveryNoteMaterial(AbstractDelivery,AbstractSupplier):
    
    class Meta(AbstractDelivery.Meta,AbstractSupplier.Meta):
        pass


class MaterialReceipt(AbstractQuantity):
    delivery_note_material = models.ForeignKey(DeliveryNoteMaterial,on_delete=models.CASCADE)
    material_order = models.ForeignKey(MaterialOrder,on_delete=models.CASCADE)


class ProductionReport(AbstractProduct,AbstractCreated,AbstractQuantity):
    process = models.ForeignKey(Process,on_delete=models.CASCADE)
    quantity_not_good = models.PositiveBigIntegerField()
    operator = models.ForeignKey(Operator,on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine,on_delete=models.CASCADE)

    class Meta(AbstractProduct.Meta,AbstractCreated.Meta,AbstractQuantity.Meta):
        pass

class MaterialProductionReport(AbstractQuantity,AbstractMaterial):
    production_report = models.ForeignKey(ProductionReport,on_delete=models.CASCADE)

    class Meta(AbstractQuantity.Meta,AbstractMaterial.Meta):
        pass









