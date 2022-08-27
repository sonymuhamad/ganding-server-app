from rest_framework.permissions import AllowAny
from django.db.models import Prefetch
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .serializer import SupplierMrpReadOnlySerializer,SupplierPurchaseOrderReadOnlySerializer,PurchaseOrderManagementSerializer,MaterialOrderManagementSerializer,BaseSupplierSerializer

from ppic.models import Material,MaterialOrder

from .models import Supplier,PurchaseOrderMaterial


class SupplierManagementViewSet(ModelViewSet):
    serializer_class = BaseSupplierSerializer
    permission_classes = [AllowAny]
    queryset = Supplier.objects.all()

    def invalid(self) -> None:
        raise ValidationError('delete failed due to data integrity || hapus data gagal')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']

        queryset = Supplier.objects.prefetch_related(
            Prefetch('purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related('materialorder_set'))).prefetch_related(
                Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related('ppic_requirementmaterial_related').prefetch_related('ppic_warehousematerial_related').filter(Q(ppic_requirementmaterials__isnull=False) | Q(ppic_warehousematerials__isnull=False) )))

        instance_supplier = get_object_or_404(queryset,pk=pk)
        
        for po in instance_supplier.purchasing_purchaseordermaterial_related.all():
            if po.done:
                self.invalid()
            for mo in po.materialorder_set.all():
                if mo.arrived > 0:
                    self.invalid()
        
        for material in instance_supplier.ppic_material_related.all():
            for requirementmaterial in material.ppic_requirementmaterial_related.all():
                if requirementmaterial.conversion > 0:
                    self.invalid()
            for whmaterial in material.ppic_warehousematerial_related.all():
                if whmaterial.quantity > 0:
                    self.invalid()

        return super().destroy(request, *args, **kwargs)


class MrpReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = SupplierMrpReadOnlySerializer
    permission_classes = [AllowAny]

    queryset = Supplier.objects.prefetch_related(
        Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related('ppic_materialrequirementplanning_related').filter(ppic_materialrequirementplannings__isnull=False)))


class PurchaseOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = SupplierPurchaseOrderReadOnlySerializer
    permission_classes = [AllowAny]

    queryset = Supplier.objects.prefetch_related(
        Prefetch('purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related(
            Prefetch('materialorder_set',queryset=MaterialOrder.objects.select_related('material').prefetch_related('materialreceiptschedule_set')))))


class PurchaseOrderManagementViewSet(ModelViewSet):
    serializer_class = PurchaseOrderManagementSerializer
    permission_classes = [AllowAny]

    queryset = PurchaseOrderMaterial.objects.prefetch_related(
            Prefetch('materialorder_set',queryset=MaterialOrder.objects.select_related('material').prefetch_related('materialreceiptschedule_set')))
    
    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_po = self.queryset
        instance_po = get_object_or_404(instance_po,pk=pk)

        instance_mos = instance_po.materialorder_set.all()
        
        for mo in instance_mos:
            if mo.arrived > 0:
                raise ValidationError('hapus data gagal, sudah ada kedatangan pada purchase order tersebut')

        return super().destroy(request, *args, **kwargs)


class MaterialOrderManagementViewSet(ModelViewSet):
    serializer_class = MaterialOrderManagementSerializer
    permission_classes = [AllowAny]

    queryset = MaterialOrder.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_mos = self.queryset
        instance_mo = get_object_or_404(instance_mos,pk=pk)

        if instance_mo.arrived > 0:
             raise ValidationError('hapus data gagal, sudah ada kedatangan pada pesanan material tersebut')

        return super().destroy(request, *args, **kwargs)
        

