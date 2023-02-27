from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,CreateModelViewSet,GetModelViewSet

from rest_framework.response import Response
from rest_framework import status

from math import ceil
import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q,Sum,F,Count
from django.shortcuts import get_object_or_404
from dateutil import rrule

from manager.shortcuts import invalid
from ppic.models import *

from purchasing.models import Supplier
from .serializer import *
from .utils import MultipartJsonParser
from marketing.models import Customer, SalesOrder
from .permissions import PpicPermission,CanManageWarehouse,CanManageDelivery,CanManageMaterial,CanManageProduct,CanManageProduction


def queryDebug(func):

    @functools.wraps(func)
    def inner_func(*args, **kwargs):

        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.2f}s")

        return result

    return inner_func





class MaterialViewSet(ReadOnlyModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = MaterialSerializer
    queryset = Material.objects.prefetch_related('ppic_requirementmaterial_related').select_related('warehousematerial')

class RequirementMaterialViewSet(CreateUpdateDeleteModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = RequirementMaterialManagement
    queryset = RequirementMaterial.objects.all()

class RequirementProductViewSet(CreateUpdateDeleteModelViewSet):
    permission_classes = [PpicPermission]
    serializer_class = RequirementProductManagement
    queryset = RequirementProduct.objects.all()
    
    

class WarehouseSubcontViewSet(GetModelViewSet):
    '''
    warehouse type (subcont) -> warehouse product -> product
    '''
    permission_classes = [PpicPermission]
    serializer_class = WarehouseTypeReadOnlySerializer
    queryset = WarehouseType.objects.prefetch_related(
        Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('process__process_type','process__product').select_related('product__customer','product__type').filter(Q(quantity__gt=0)))).filter(Q(id=2))

    

class UomConversionReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion uom
    '''
    permission_classes = [PpicPermission]
    serializer_class = ConversionUomReadOnlySerializer
    queryset = ConversionUom.objects.select_related('uom_input','uom_output')


class UomConversionManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management conversion of uom
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = ConversionUomManagementSerializer
    queryset = ConversionUom.objects.all()

class BasedConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of based conversion material
    '''
    permission_classes = [PpicPermission]
    serializer_class = BasedConversionReadOnlySerializer
    queryset = BasedConversionMaterial.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier')

class BasedConversionMaterialManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for management based conversion of material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = BasedConversionManagementSerializer
    queryset = BasedConversionMaterial.objects.all()

class ReportConversionMaterialReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve list of conversion material reports
    '''
    permission_classes = [PpicPermission]
    serializer_class = ConversionMaterialReportReadOnlySerializer
    queryset = ConversionMaterialReport.objects.select_related('material_input__uom','material_input__supplier','material_output__uom','material_output__supplier').order_by('-created')

class ReportConversionMaterialManagementViewSet(CreateModelViewSet):
    '''
    viewset for management report conversion of material ie: shearing material
    '''
    permission_classes = [PpicPermission,CanManageWarehouse]
    serializer_class = ConversionMaterialReportManagementSerializer
    queryset = ConversionMaterialReport.objects.all()


    


































