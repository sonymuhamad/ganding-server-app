from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db.models import Prefetch

from marketing.permissions import MarketingPermission
from marketing.serializer import DeliveryNoteCustomerListSerializer

from ppic.models import DeliveryNoteCustomer,ProductDeliverCustomer

class DeliveryNoteListViewSet(ReadOnlyModelViewSet):
    '''
    for delivery note page
    '''
    permission_classes = [MarketingPermission]
    serializer_class = DeliveryNoteCustomerListSerializer
    queryset = DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','schedules','schedules__product_order'))).select_related('vehicle','customer','driver').order_by('-created')


