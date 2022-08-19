from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

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

class AbstractCreated(models.Model):
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

class AbstractDelivery(AbstractCode,AbstractCreated):
    note = models.TextField(default='Delivery Note')

    class Meta(AbstractCode.Meta,AbstractCreated.Meta):
        abstract = True

class AbstractType(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True


class Activity(AbstractType):
    pass


class UserActivity(AbstractCreated):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity,on_delete=models.CASCADE)
    descriptions = models.TextField()

    
