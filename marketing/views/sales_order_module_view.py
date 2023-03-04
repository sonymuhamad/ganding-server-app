from rest_framework.viewsets import ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet
from rest_framework.response import Response

from django.db.models import Prefetch,Sum
from django.shortcuts import get_object_or_404

from marketing.permissions import MarketingPermission,CanManageSalesOrder
from marketing.models import SalesOrder

from marketing.shortcuts import validate_productorder
from manager.shortcuts import invalid

from ppic.models import DeliverySchedule,ProductOrder,ProductDeliverCustomer

from marketing.serializers.sales_order_serializer import ThreeDepthDeliveryScheduleSerializer,SalesOrderListSerializer,SalesOrderManagementSerializer,ProductOrderManagementSerializer,DeliveryScheduleManagementSerializer

from ppic.serializers.delivery_serializer import TwoDepthProductDeliverCustomerSerializer


class DeliveryScheduleReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset provide endpoint to get a list of delivery schedules
    '''
    permission_classes = [MarketingPermission]
    serializer_class = ThreeDepthDeliveryScheduleSerializer
    
    unfilter_queryset = DeliverySchedule.objects.select_related('product_order','product_order__product','product_order__sales_order','product_order__product__customer','product_order__product__type','product_order__sales_order__customer')
    
    queryset = unfilter_queryset.filter(fulfilled_quantity=0)

    def retrieve(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])

        filtered_queryset_by_sales_order = self.unfilter_queryset.filter(product_order__sales_order__id__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_sales_order,many=True)

        return Response(serializer.data)


class SalesOrderListReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get sales order nested to product order
    '''
    permission_classes = [MarketingPermission]
    serializer_class = SalesOrderListSerializer
    queryset = SalesOrder.objects.prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.select_related('product').annotate(total_deliver=Sum('productdelivercustomer__quantity',default=0)).prefetch_related(Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__driver','delivery_note_customer__customer','delivery_note_customer__vehicle'))))).select_related('customer').annotate(productordered=Sum('productorder__ordered',default=0)).annotate(productdelivered=Sum('productorder__delivered',default=0)).order_by('-date')


class ProductDeliverCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset class provide get data product delivery, and retrieve product delivery by its sales order
    '''
    serializer_class = TwoDepthProductDeliverCustomerSerializer
    queryset = ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','delivery_note_customer','schedules','schedules__product_order','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver')

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset_by_sales_order = self.queryset.filter(product_order__sales_order__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset_by_sales_order,many=True)
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


