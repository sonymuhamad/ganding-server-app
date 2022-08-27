from rest_framework.permissions import AllowAny
from django.db.models import Prefetch
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .serializer import SupplierMrpReadOnlySerializer,SupplierPurchaseOrderReadOnlySerializer,PurchaseOrderManagementSerializer,MaterialOrderManagementSerializer,BaseSupplierSerializer

from ppic.models import Material,MaterialOrder

from .models import Supplier,PurchaseOrderMaterial

def invalid() -> None:
    raise ValidationError('delete failed due to data integrity || hapus data gagal')


def validate_mo(queryset):
    for mo in queryset:
            if mo.arrived > 0:
                invalid()

def validate_po(queryset):

    for po in queryset:
        if po.done:
            invalid()
        queryset_mo = po.materialorder_set.all() 
        validate_mo(queryset_mo)


class SupplierManagementViewSet(ModelViewSet):
    serializer_class = BaseSupplierSerializer
    permission_classes = [AllowAny]
    queryset = Supplier.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']

        queryset = Supplier.objects.prefetch_related(
            Prefetch('purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related('materialorder_set'))).prefetch_related(
                Prefetch('ppic_material_related',queryset=Material.objects.prefetch_related('ppic_requirementmaterial_related').prefetch_related('ppic_warehousematerial_related').filter(Q(ppic_requirementmaterials__isnull=False) | Q(ppic_warehousematerials__isnull=False) )))

        instance_supplier = get_object_or_404(queryset,pk=pk)
        queryset_po = instance_supplier.purchasing_purchaseordermaterial_related.all()

        validate_po(queryset_po)
        
        for material in instance_supplier.ppic_material_related.all():
            for requirementmaterial in material.ppic_requirementmaterial_related.all():
                if requirementmaterial.conversion > 0:
                    invalid()
            for whmaterial in material.ppic_warehousematerial_related.all():
                if whmaterial.quantity > 0:
                    invalid()

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
        
        if instance_po.done:
            invalid()
        
        instance_mo = instance_po.materialorder_set.all()
        validate_mo(instance_mo)

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
             invalid()
             
        return super().destroy(request, *args, **kwargs)
        

