from rest_framework.viewsets import ReadOnlyModelViewSet

from django.db.models import Prefetch

from purchasing.permissions import PurchasingPermission

from ppic.serializer import MaterialListSerializer as PpicMaterialListSerializer
from ppic.models import Material,RequirementMaterial


class MaterialDetailListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for handling request for list of materials
    '''
    permission_classes = [PurchasingPermission]
    serializer_class = PpicMaterialListSerializer
    queryset = Material.objects.prefetch_related(
        Prefetch('ppic_requirementmaterial_related',queryset=RequirementMaterial.objects.select_related('process','process__process_type','process__product'))).select_related('warehousematerial','uom','supplier')


