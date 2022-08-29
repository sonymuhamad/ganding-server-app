from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q
from django.shortcuts import get_object_or_404


from manager.shortcuts import invalid
from ppic.models import Process, Product, RequirementMaterial, RequirementProduct, WarehouseProduct
from .serializer import ProductCustomerReadOnlySerializer,ProductManagementSerializer
from marketing.models import Customer


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


class ProductCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductCustomerReadOnlySerializer
    permission_classes = [AllowAny]
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))))).select_related('type')))

    @queryDebug
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ProductManagementViewSet(ModelViewSet):
    serializer_class = ProductManagementSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        queryset = Product.objects.prefetch_related('ppic_productorder_related').prefetch_related('ppic_warehouseproduct_related').prefetch_related('ppic_requirementproduct_related')

        instance_product = get_object_or_404(queryset,pk=pk)
        
        for productorder in instance_product.ppic_productorder_related.all():
            if productorder.delivered > 0:
                invalid()

        for whproduct in instance_product.ppic_warehouseproduct_related.all():
            if whproduct.quantity > 0:
                invalid()

        for requirement_product in instance_product.ppic_requirementproduct_related.all():
            if requirement_product.conversion > 0:
                invalid()

        return super().destroy(request, *args, **kwargs)






