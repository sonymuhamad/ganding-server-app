from rest_framework.serializers import ModelSerializer
from .models import Supplier,PurchaseOrderMaterial

class SupplierSerializer(ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['name','email','phone','address']

class PurchaseOrderMaterialSerializer(ModelSerializer):
    class Meta:
        model = PurchaseOrderMaterial
        fields = ['code','supplier']



