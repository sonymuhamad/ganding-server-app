from ast import arg
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from .serializer import CustomerSerializer,SalesOrderManagementSerializer, SalesOrderReadOnlySerializer
from .models import Customer, SalesOrder
from ppic.models import Product, ProductOrder
from rest_framework import response,status,permissions
from django.db.models import Prefetch

from django.db import connection, reset_queries
import time
import functools
from django.db.models import Prefetch


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
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        tes = self.integrity_check(kwargs)

        if not tes:
            return super().destroy(request, *args, **kwargs)        
        return response.Response({'error':'there is still an order from this customer'},status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def integrity_check(self,data):
        id = data['pk']
        customer = Customer.objects.get(id=id)
        salesorder = SalesOrder.objects.filter(done=0,customer=customer).first()
        return salesorder

class SalesOrderManagementViewSet(ModelViewSet):
    serializer_class = SalesOrderManagementSerializer
    permission_classes = [permissions.AllowAny]
    queryset = SalesOrder.objects.prefetch_related(Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product'))).select_related('customer')

class SalesOrderReadOnlyViewSet(ReadOnlyModelViewSet):
    serializer_class = SalesOrderReadOnlySerializer
    permission_classes = [permissions.AllowAny]
    queryset = SalesOrder.objects.prefetch_related(Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product'))).select_related('customer')

