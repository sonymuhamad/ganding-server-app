from rest_framework.viewsets import CreateUpdateDeleteModelViewSet,ReadOnlyModelViewSet,RetrieveModelViewSet

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch,Count

from purchasing.permissions import PurchasingPermission,CanManageSupplier
from purchasing.models import Supplier,PurchaseOrderMaterial

from purchasing.shortcuts import validate_po
from manager.shortcuts import invalid

from ppic.models import Material,MaterialOrder

from purchasing.serializers.supplier_serializer import BaseSupplierSerializer,SupplierNestedPurchaseOrderSerializer

class SupplierManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud supplier
    '''
    permission_classes = [PurchasingPermission,CanManageSupplier]
    serializer_class = BaseSupplierSerializer
    queryset = Supplier.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']

        queryset = Supplier.objects.prefetch_related(
            Prefetch('purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related('materialorder_set'))).prefetch_related(
                Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')))

        instance_supplier = get_object_or_404(queryset,pk=pk)
        queryset_po = instance_supplier.purchasing_purchaseordermaterial_related.all()

        validate_po(queryset_po)
        
        for material in instance_supplier.ppic_material_related.all():
            
            for requirementmaterial in material.ppic_requirementmaterial_related.all():
                if requirementmaterial.input > 0:
                    invalid()
            
            if material.warehousematerial.quantity>0:
                invalid()

        return super().destroy(request, *args, **kwargs)


class SupplierViewSet(ReadOnlyModelViewSet):
    serializer_class = BaseSupplierSerializer
    queryset = Supplier.objects.annotate(number_of_material=Count(
        'ppic_materials',distinct=True)).annotate(number_of_purchase_order=Count(
            'purchasing_purchaseordermaterials',distinct=True))


class SupplierReadOnlyViewSet(RetrieveModelViewSet):
    '''
    a viewset for retrieve detail supplier nested to material, purchase order -> material order
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = SupplierNestedPurchaseOrderSerializer
    queryset = Supplier.objects.prefetch_related(
        Prefetch('ppic_material_related',queryset=Material.objects.select_related('uom','supplier','warehousematerial')),Prefetch(
            'purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related(
        Prefetch(
                'materialorder_set',queryset=MaterialOrder.objects.select_related('material','purchase_order_material','material__uom','material__supplier')))))

