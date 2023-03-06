from rest_framework.response import Response
from rest_framework import status

from manager.viewsets import ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet,GetModelViewSet
from django.db.models import Prefetch

from marketing.permissions import MarketingPermission,CanManageInvoice
from marketing.models import Invoice,SalesOrder

from manager.shortcuts import invalid
from ppic.models import ProductOrder

from marketing.serializers.invoice_serializer import InvoiceSerializer,InvoiceNestedSalesOrderSerializer
from marketing.serializers.sales_order_serializer import OneDepthSalesOrderNestedProductOrderSerializer


class InvoiceReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for readonly invoice
    '''
    permission_classes = [MarketingPermission]
    serializer_class = InvoiceNestedSalesOrderSerializer
    queryset = Invoice.objects.get_queryset_related().prefetch_related(
        Prefetch('sales_order__productorder_set',queryset=ProductOrder.objects.select_related('product','product__customer','product__type','sales_order','sales_order__customer')))
    
class SalesOrderDoneListViewSet(GetModelViewSet):
    '''
    a viewset for get all sales order that already done, which can be the basis of making the invoice 
    '''
    permission_classes = [MarketingPermission]
    serializer_class = OneDepthSalesOrderNestedProductOrderSerializer
    queryset_product_order = ProductOrder.objects.select_related('product','product__customer','product__type','sales_order','sales_order__customer')
    queryset = SalesOrder.objects.select_related('customer').prefetch_related(
        Prefetch('productorder_set',queryset_product_order)).filter(closed=True,invoice__isnull=True)

class InvoiceManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud invoice
    '''
    permission_classes = [MarketingPermission,CanManageInvoice]
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.select_related('sales_order')

    def destroy(self, request, *args, **kwargs):
        '''
        endpoint method to delete invoice
        '''
        
        instance = self.get_object()
        if instance.closed or instance.done:
            invalid()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

