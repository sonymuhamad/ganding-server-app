from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,RetrieveModelViewSet,UpdateModelViewSet,GetModelViewSet

from .serializer import *
from django.shortcuts import get_object_or_404

import functools
import time
from django.db import connection, reset_queries
from django.db.models import Prefetch,Q,Sum,F,Count
from datetime import date, datetime
import calendar

from manager.shortcuts import invalid
from .models import Customer, SalesOrder,Invoice
from ppic.models import Product, ProductOrder,ProductDeliverCustomer,DeliveryNoteCustomer,Process,WarehouseProduct,RequirementProduct,RequirementMaterial

from ppic.serializer import ProductReadOnlySerializer,ProductDeliverCustomerReadOnlySerializer,ProductListSerializer

from .permissions import MarketingPermission,CanManageCustomer,CanManageSalesOrder,CanManageInvoice
from rest_framework.response import Response
from dateutil import rrule
from rest_framework.permissions import AllowAny
from rest_framework import status

from ppic.serializer import ProductOrderListSerializer


def validate_productorder(queryset_po)-> None:
    for productorder in queryset_po:
        if productorder.delivered > 0 or productorder.ordered > 0:
            invalid()
            
def validate_so(queryset) -> None:
    for so in queryset:
        if so.closed:
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

class CustomerManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud customer
    '''
    permission_classes = [MarketingPermission,CanManageCustomer]
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
      

class CustomerViewset(ReadOnlyModelViewSet):
    '''
    viewset for handling customer  (get,retrieve)
    '''
    permission_classes = [MarketingPermission]
    serializer_class = CustomerSerializer
    queryset = Customer.objects.annotate(total_sales_order=Count('marketing_salesorders',distinct=True),total_product=Count('ppic_products',distinct=True)).prefetch_related(Prefetch('ppic_product_related',queryset=Product.objects.select_related('customer','type').annotate(total_order=Sum('ppic_productorders__ordered',filter=Q(ppic_productorders__sales_order__fixed=True),default=0)).order_by('-total_order')))

    
    def generate_data_from_queryset(self):

        data = []

        for cust in self.queryset:
            most_ordered_product = cust.ppic_product_related.first()
            temp_data = {
                'id':cust.pk,
                'name':cust.name,
                'email':cust.email,
                'phone':cust.phone,
                'address':cust.address,
                'total_product':cust.total_product,
                'total_sales_order':cust.total_sales_order,
                'most_ordered_product':most_ordered_product
            }
            data.append(temp_data)

        return data

    def list(self, request, *args, **kwargs):

        validate_data = self.generate_data_from_queryset()

        serializer = self.get_serializer(validate_data,many=True)
        return Response(serializer.data)

class SalesOrderManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    viewset for handling insert and update data from salesorder -> productorder -> deliveryschedule
    '''
    permission_classes = [MarketingPermission,CanManageSalesOrder]
    serializer_class = SalesOrderManagementSerializer
    queryset = SalesOrder.objects.prefetch_related(
        Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('product'))).select_related('customer')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_so = get_object_or_404(self.queryset,pk=pk)
        
        if instance_so.closed:
            invalid('Sales order telah ditutup')

        queryset_productorder = instance_so.productorder_set.all()
        validate_productorder(queryset_productorder)

        return super().destroy(request, *args, **kwargs)

class ProductOrderManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud product ordered
    '''
    permission_classes = [MarketingPermission,CanManageSalesOrder]
    serializer_class = ProductOrderManagementSerializer
    queryset = ProductOrder.objects.prefetch_related('deliveryschedule_set').select_related('sales_order')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_po = get_object_or_404(self.queryset,pk=pk)

        if instance_po.delivered > 0 or instance_po.sales_order.fixed :
            invalid()

        return super().destroy(request, *args, **kwargs)

class ProductDetailViewSet(RetrieveModelViewSet):
    '''
    a viewset for retrieve product detail for marketing->customer->product detail page
    '''
    permission_classes = [MarketingPermission]
    serializer_class = ProductReadOnlySerializer
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type'))).select_related('type')


class SalesOrderListReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get sales order nested to product order
    '''
    permission_classes = [MarketingPermission]
    serializer_class = SalesOrderListSerializer
    queryset = SalesOrder.objects.prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.select_related('product').annotate(total_deliver=Sum('productdelivercustomer__quantity',default=0)).prefetch_related(Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__driver','delivery_note_customer__customer','delivery_note_customer__vehicle'))))).select_related('customer').annotate(productordered=Sum('productorder__ordered',default=0)).annotate(productdelivered=Sum('productorder__delivered',default=0)).order_by('-date')

            
class ProductCustomerViewSet(ReadOnlyModelViewSet):
    permission_classes = [MarketingPermission]
    serializer_class = ProductListSerializer
    queryset = Product.objects.select_related('customer','type').annotate(total_stock=Sum('ppic_warehouseproducts__quantity'))

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset = self.queryset.filter(customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset,many=True)
        return Response(serializer.data)

class CustomerDetailReadOnlyViewSet(ReadOnlyModelViewSet):

    permission_classes = [MarketingPermission]
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
    
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class DeliveryNoteListViewSet(ReadOnlyModelViewSet):
    '''
    for delivery note page
    '''
    permission_classes = [MarketingPermission]
    serializer_class = DeliveryNoteCustomerListSerializer
    queryset = DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','schedules','schedules__product_order'))).select_related('vehicle','customer','driver').order_by('-created')

class PendingDeliveryNoteListViewSet(ReadOnlyModelViewSet):
    '''
    for dashboard page  `delivery note that invoice status is pending`
    '''
    permission_classes = [MarketingPermission]
    serializer_class = DeliveryNoteCustomerListSerializer
    queryset = DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','schedules','schedules__product_order'))).select_related('vehicle','customer','driver').distinct()

class DeliveryNoteReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get all data from customer -> deliverynote -> productdelivery -> productorder
    '''
    permission_classes = [MarketingPermission]
    serializer_class = DeliveryCustomerSerializer
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_deliverynotecustomer_related',queryset=DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order')))))

class InvoiceManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud invoice
    '''
    permission_classes = [MarketingPermission,CanManageInvoice]
    serializer_class = InvoiceManagementSerializer
    queryset = Invoice.objects.select_related('sales_order')

    def destroy(self, request, *args, **kwargs):
        
        instance = self.get_object()

        if instance.closed or instance.done:
            invalid()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvoiceReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for readonly invoice
    '''
    permission_classes = [MarketingPermission]
    serializer_class = InvoiceReadOnlySerializer
    queryset = Invoice.objects.select_related('sales_order','sales_order__customer').prefetch_related(
        Prefetch('sales_order__productorder_set',queryset=ProductOrder.objects.select_related('product','product__customer','product__type')))


class SalesOrderDoneListViewSet(GetModelViewSet):
    '''
    a viewset for get all sales order that already done, which can be the basis of making the invoice 
    '''
    permission_classes = [MarketingPermission]
    serializer_class = SalesOrderReadOnlyFromInvoiceSerializer
    queryset = SalesOrder.objects.select_related('customer').prefetch_related(
        Prefetch('productorder_set',ProductOrder.objects.select_related('product','product__customer','product__type'))).filter(closed=True,invoice__isnull=True)



class ReportProductOrderViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get total ordered product each month, retrieve means for particular customer
    '''
    permission_classes = [MarketingPermission]
    serializer_class = ReportProductOrderSerializer
    queryset = ProductOrder.objects.filter(Q(sales_order__fixed=True),sales_order__date__lte=date.today()).values('sales_order__date__year','sales_order__date__month').annotate(total_order=Sum('ordered')).order_by('sales_order__date__year','sales_order__date__month')

    def generate_date_from_queryset(self,queryset) -> dict:

        store_data = {}

        for data in queryset:
            year = data['sales_order__date__year']
            month = data['sales_order__date__month']
            store_data[date(year,month,1)] = data['total_order']
        
        return store_data

    def generate_data_from_dates(self,first_date,last_date,data_report,generated_data):
        
        for dt in rrule.rrule(rrule.MONTHLY,dtstart=first_date,until=last_date):
                current_date = date(dt.year,dt.month,1)
                current_total_order = generated_data.get(current_date,0)
                data_report.append({
                    'date':current_date,
                    'total_order':current_total_order
                })

    def list(self, request, *args, **kwargs):
        return self.generate_data_and_return(self.queryset)

    def generate_data_and_return(self,queryset):
        
        first_monthly_order = queryset.first()
        last_monthly_order = queryset.last()
        data_report = []

        if queryset.count() > 0:
            generated_data = self.generate_date_from_queryset(queryset)

            first_year = first_monthly_order['sales_order__date__year']
            first_month = first_monthly_order['sales_order__date__month']

            last_year = last_monthly_order['sales_order__date__year']
            last_month = last_monthly_order['sales_order__date__month']

            first_date = date(first_year,first_month,1)
            last_date = date(last_year,last_month,1)

            self.generate_data_from_dates(first_date,last_date,data_report,generated_data)

        serializer = self.get_serializer(data_report,many=True)
        return Response(serializer.data)



    def retrieve(self, request, *args, **kwargs):
        
        pk = int(kwargs['pk'])

        queryset = ProductOrder.objects.filter(Q(sales_order__fixed=True),sales_order__date__lte=date.today(),sales_order__customer__pk__exact=pk).values('sales_order__date__year','sales_order__date__month').annotate(total_order=Sum('ordered')).order_by('sales_order__date__year','sales_order__date__month')
        
        return self.generate_data_and_return(queryset)

class InProgressProductOderViewSet(GetModelViewSet):
    '''
    a viewset provide endpoint to get in progress order
    '''
    serializer_class = ProductOrderListSerializer
    permission_classes = [MarketingPermission]
    queryset = ProductOrder.objects.select_related('product','sales_order','product__customer','product__type','sales_order__customer').filter(Q(delivered__lt=F('ordered')),Q(sales_order__fixed=True)&Q(sales_order__closed=False)).order_by('pk')


class FinishedSalesOrderViewSet(GetModelViewSet):
    '''
    a viewset provide endpoint to get sales order that already finished, but not closed yet.
    '''
    permission_classes = [MarketingPermission]
    serializer_class = SalesOrderReadOnlyFromInvoiceSerializer
    queryset = SalesOrder.objects.select_related('customer').prefetch_related(
        Prefetch('productoder_set',ProductOrder.objects.select_related('product','product__customer','product__type'))).filter(Q(closed=False),productorder__delivered__gte=F('productorder__ordered'))


class DeliveryScheduleReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset provide endpoint to get a list of delivery schedules
    '''
    permission_classes = [MarketingPermission]
    serializer_class = DeliveryScheduleReadOnlySerializer
    
    unfilter_queryset = DeliverySchedule.objects.select_related('product_order','product_order__product','product_order__sales_order','product_order__product__customer','product_order__product__type','product_order__sales_order__customer')
    
    queryset = unfilter_queryset.filter(fulfilled_quantity=0)

    def retrieve(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])

        filtered_queryset_by_sales_order = self.unfilter_queryset.filter(product_order__sales_order__id__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_sales_order,many=True)

        return Response(serializer.data)

class DeliveryScheduleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud data delivery schedule
    '''
    permission_classes = [MarketingPermission,CanManageSalesOrder]
    serializer_class = DeliveryScheduleManagementSerializer
    queryset = DeliverySchedule.objects.select_related('product_order','product_order__sales_order','product_order__product')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_so = get_object_or_404(self.queryset,pk=pk)
        
        if instance_so.fulfilled_quantity > 0:
            invalid()

        return super().destroy(request, *args, **kwargs)


class ProductDeliverCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset class provide get data product delivery, and retrieve product delivery by its sales order
    '''
    serializer_class = ProductDeliverCustomerReadOnlySerializer
    permission_classes = [MarketingPermission]
    queryset = ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver')

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset_by_sales_order = self.queryset.filter(product_order__sales_order__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_sales_order,many=True)
        return Response(serializer.data)

class CustomerProductDeliverCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset class provide get data product delivery, and retrieve product delivery by its sales order
    '''
    serializer_class = ProductDeliverCustomerReadOnlySerializer
    permission_classes = [MarketingPermission]
    queryset = ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver')

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset_by_sales_order = self.queryset.filter(delivery_note_customer__customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_sales_order,many=True)
        return Response(serializer.data)


class CustomerPendingInvoiceReadOnlyViewSet(RetrieveModelViewSet):
    '''
    a viewset for readonly invoice
    '''
    permission_classes = [MarketingPermission]
    serializer_class = InvoiceReadOnlySerializer
    queryset = Invoice.objects.select_related('sales_order','sales_order__customer').prefetch_related(
        Prefetch('sales_order__productorder_set',queryset=ProductOrder.objects.select_related('product','product__customer','product__type'))).filter(done=False)

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset_by_customer = self.queryset.filter(sales_order__customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_customer,many=True)
        return Response(serializer.data)












