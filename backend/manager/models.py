from django.db import models
from django.utils import timezone

# Create your models here.

class AbstractCustomerVendor(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.PositiveBigIntegerField()
    address = models.TextField()

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True

class AbstractQuantity(models.Model):
    quantity = models.PositiveBigIntegerField()
    
    def __str__(self) -> str:
        return self.quantity
    
    class Meta:
        abstract = True


class AbstractSchedule(AbstractQuantity):
    date = models.DateField()
    
    class Meta:
        abstract = True


class AbstractCode(models.Model):
    code = models.CharField(max_length=255,unique=True)

    def __str__(self) -> str:
        return self.code

    class Meta:
        abstract = True


class AbstractDelivery(AbstractCode):
    created = models.DateTimeField(default=timezone.now)
    note = models.TextField(default='Delivery Note')

    class Meta:
        abstract = True

