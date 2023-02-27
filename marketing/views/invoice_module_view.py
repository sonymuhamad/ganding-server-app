from rest_framework.viewsets import GetModelViewSet,ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Prefetch

from marketing.permissions import MarketingPermission,CanManageInvoice
from marketing.models import Invoice,SalesOrder
from marketing.serializer import InvoiceReadOnlySerializer,InvoiceManagementSerializer,SalesOrderReadOnlyFromInvoiceSerializer

from manager.shortcuts import invalid
from ppic.models import ProductOrder



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

