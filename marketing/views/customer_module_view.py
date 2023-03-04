from rest_framework.viewsets import ReadOnlyModelViewSet,RetrieveModelViewSet,CreateUpdateDeleteModelViewSet
from django.db.models import Count,Q,Sum,Prefetch,QuerySet
from rest_framework.response import Response

from marketing.permissions import MarketingPermission,CanManageCustomer
from marketing.models import Customer,SalesOrder,Invoice

from ppic.models import Product,ProductDeliverCustomer,ProductOrder

from manager.shortcuts import invalid
from django.shortcuts import get_object_or_404
from marketing.shortcuts import validate_so

from marketing.serializers.customer_serializer import CustomerSerializer
from marketing.serializers.invoice_serializer import InvoiceNestedSalesOrderSerializer

from ppic.serializers.delivery_serializer import TwoDepthProductDeliverCustomerSerializer
from ppic.serializers.product_serializer import OneDepthProductSerializer

class CustomerViewset(ReadOnlyModelViewSet):
    '''
    viewset for handling customer  (get,retrieve)
    '''
    serializer_class = CustomerSerializer
    queryset = Customer.objects.annotate(total_sales_order=Count('marketing_salesorders',distinct=True),total_product=Count('ppic_products',distinct=True))
    
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class CustomerManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud customer
    '''
    permission_classes = [MarketingPermission,CanManageCustomer]
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def check_products_customer(self,queryset_product:QuerySet):
        '''
        check if the customer still have a product in warehouse product
        '''
        if queryset_product.filter(ppic_warehouseproducts__quantity__gt=0).exists():
            invalid()

    def check_used_product_assembly(self,queryset_product:QuerySet):
        '''
        check if the product is still used as requirement product assembly in any process
        '''
        if queryset_product.filter(ppic_requirementproducts__input__gt=0).exists():
            invalid()

    def destroy(self, request, *args, **kwargs):
        '''
        endpoint for delete customer
        '''
        pk = kwargs['pk']
        queryset = Customer.objects.prefetch_related(
            Prefetch('marketing_salesorder_related',queryset=SalesOrder.objects.prefetch_related('productorder_set'))).prefetch_related(
                Prefetch('ppic_product_related',queryset=Product.objects.prefetch_related('ppic_requirementproduct_related').prefetch_related('ppic_warehouseproduct_related').filter(Q(ppic_requirementproducts__isnull=False) | Q(ppic_warehouseproducts__isnull=False) )))

        instance_customer = get_object_or_404(queryset,pk=pk)
        queryset_so = instance_customer.marketing_salesorder_related.all()
        queryset_product = instance_customer.ppic_product_related.all()
        
        validate_so(queryset_so)
        self.check_products_customer(queryset_product)
        self.check_used_product_assembly(queryset_product)

        return super().destroy(request, *args, **kwargs)        


class CustomerPendingInvoiceReadOnlyViewSet(RetrieveModelViewSet):
    '''
    a viewset for readonly invoice
    '''
    permission_classes = [MarketingPermission]
    serializer_class = InvoiceNestedSalesOrderSerializer
    queryset = Invoice.objects.get_queryset_related().prefetch_related(
        Prefetch('sales_order__productorder_set',queryset=ProductOrder.objects.select_related('product','product__customer','product__type','sales_order','sales_order__customer'))).filter(done=False)

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])
        
        filtered_queryset_by_customer = self.queryset.filter(sales_order__customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_customer,many=True)
        return Response(serializer.data)


class CustomerProductDeliverCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset class provide get data product delivery, and retrieve product delivery by its sales order
    '''
    serializer_class = TwoDepthProductDeliverCustomerSerializer
    permission_classes = [MarketingPermission]
    queryset = ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver')

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset_by_sales_order = self.queryset.filter(delivery_note_customer__customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_sales_order,many=True)
        return Response(serializer.data)
    
class ProductCustomerViewSet(ReadOnlyModelViewSet):
    permission_classes = [MarketingPermission]
    serializer_class = OneDepthProductSerializer
    queryset = Product.objects.select_related('customer','type').annotate(total_stock=Sum('ppic_warehouseproducts__quantity'))

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset = self.queryset.filter(customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset,many=True)
        return Response(serializer.data)
