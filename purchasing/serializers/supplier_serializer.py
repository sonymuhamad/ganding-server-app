from rest_framework.serializers import ModelSerializer,IntegerField

from purchasing.models import Supplier

from .purchase_order_serializer import PurchaseOrderReadOnlySerializer
from ppic.serializers.material_serializer import OneDepthMaterialNestedWarehouseSerializer

class BaseSupplierSerializer(ModelSerializer):
    '''
    a serializer for crud supplier
    '''
    number_of_material = IntegerField(read_only=True)
    number_of_purchase_order = IntegerField(read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

class SupplierNestedPurchaseOrderSerializer(BaseSupplierSerializer):
    '''
    extended supplier to purchase order -> material order
    '''

    purchasing_purchaseordermaterial_related = PurchaseOrderReadOnlySerializer(many=True,read_only=True)
    ppic_material_related = OneDepthMaterialNestedWarehouseSerializer(many=True)

