from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet
from .serializer import CustomerDetailReadOnlySerializer, CustomerSerializer, SalesOrderListSerializer,SalesOrderManagementSerializer, SalesOrderReadOnlySerializer,DeliveryCustomerSerializer,DeliveryProductCustomerManagementSerializer,CustomerSalesOrderReadOnlySerializer,ProductOrderManagementSerializer
from rest_framework import response,status,permissions
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404

import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q,Sum

from manager.shortcuts import invalid
from .models import Customer, SalesOrder
from ppic.models import Product, ProductOrder,ProductDeliverCustomer,DeliveryNoteCustomer,Process,WarehouseProduct



def validate_productorder(queryset_po)-> None:
    for productorder in queryset_po:
        if productorder.delivered > 0:
            invalid()
            
def validate_so(queryset) -> None:
    for so in queryset:
        if so.done:
            invalid()
        queryset_productorder = so.productorder_set.all()
        validate_productorder(queryset_productorder)
        


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


class CustomerViewset(ModelViewSet):
    '''
    viewset for handling customer management (get,retrieve,post,put)
    '''
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        queryset = Customer.objects.prefetch_related(
            Prefetch('marketing_salesorder_related',queryset=SalesOrder.objects.prefetch_related('productorder_set'))).prefetch_related(
                Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related('ppic_requirementproduct_related').prefetch_related('ppic_warehouseproduct_related').filter(Q(ppic_requirementproducts__isnull=False) | Q(ppic_warehouseproducts__isnull=False) )))

        instance_customer = get_object_or_404(queryset,pk=pk)
        
        queryset_so = instance_customer.marketing_salesorder_related.all()
        validate_so(queryset_so)

        for product in instance_customer.ppic_product_related.all():
            for requirementproduct in product.ppic_requirementproduct_related.all():
                if requirementproduct.conversion > 0:
                    invalid()
            for whproduct in product.ppic_warehouseproduct_related.all():
                if whproduct.quantity > 0:
                    invalid()

        return super().destroy(request, *args, **kwargs)        
        
class SalesOrderManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for handling insert and update data from salesorder -> productorder -> deliveryschedule
    '''
    serializer_class = SalesOrderManagementSerializer
    queryset = SalesOrder.objects.prefetch_related(
        Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product'))).select_related('customer')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_so = get_object_or_404(self.queryset,pk=pk)
        
        if instance_so.done:
            invalid()

        queryset_productorder = instance_so.productorder_set.all()
        validate_productorder(queryset_productorder)

        return super().destroy(request, *args, **kwargs)

class ProductOrderManagementViewSet(ModelViewSet):
    serializer_class = ProductOrderManagementSerializer
    queryset = ProductOrder.objects.prefetch_related('deliveryschedule_set')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_po = get_object_or_404(self.queryset,pk=pk)

        if instance_po.delivered > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)

class SalesOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get all data from customer -> salesorder -> productorder -> deliveryschedule of product order
    '''
    serializer_class = CustomerSalesOrderReadOnlySerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('marketing_salesorder_related',queryset=SalesOrder.objects.prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product')))))

class SalesOrderListReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = SalesOrderListSerializer
    queryset = SalesOrder.objects.prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product'))).annotate(productordered=Sum('productorder__ordered')).annotate(productdelivered=Sum('productorder__delivered'))
            

class CustomerDetailReadOnlyViewSet(ReadOnlyModelViewSet):

    serializer_class = CustomerDetailReadOnlySerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('marketing_salesorder_related',queryset=SalesOrder.objects.prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product'))))).prefetch_related(
        Prefetch('ppic_deliverynotecustomer_related',queryset=DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order'))))).prefetch_related(
        Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type')))))))

class DeliveryNoteReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get all data from customer -> deliverynote -> productdelivery -> productorder
    '''
    serializer_class = DeliveryCustomerSerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_deliverynotecustomer_related',queryset=DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order')))))


class ProductDeliveryManagementSerializer(ModelViewSet):
    '''
    viewset for edit paid status of delivery product
    '''
    serializer_class = DeliveryProductCustomerManagementSerializer
    queryset = ProductDeliverCustomer.objects.all()



