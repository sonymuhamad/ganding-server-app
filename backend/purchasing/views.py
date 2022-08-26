from rest_framework.permissions import AllowAny
from django.db.models import Prefetch
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet

from .serializer import SupplierMrpReadOnlySerializer,SupplierPurchaseOrderReadOnlySerializer,PurchaseOrderManagementSerializer,MaterialOrderManagementSerializer

from ppic.models import Material,MaterialRequirementPlanning,DetailMrp,MaterialOrder,MaterialReceiptSchedule

from .models import Supplier,PurchaseOrderMaterial


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

    queryset = PurchaseOrderMaterial.objects.all()


class MaterialOrderManagementViewSet(ModelViewSet):
    serializer_class = MaterialOrderManagementSerializer
    permission_classes = [AllowAny]

    queryset = MaterialOrder.objects.all()
