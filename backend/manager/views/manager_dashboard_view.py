from rest_framework.viewsets import GetModelViewSet
from django.db.models import Prefetch,F,Q
from rest_framework import response
from datetime import date

from permissions import ManagerPermission
from shortcuts import date_last_week
from serializer import PercentageSerializer

from ppic.models import DeliveryNoteCustomer,ProductDeliverCustomer,DeliveryNoteMaterial,MaterialReceipt,ProductionReport,MaterialProductionReport,ProductProductionReport,SubcontReceipt
from ppic.serializer import DeliveryNoteCustomerReadOnlySerializer,ProductionReportReadOnlySerializer,DeliveryNoteMaterialReadOnlySerializer


class DeliveryNoteCustomerReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get this week delivery note
    '''
    permission_classes = [ManagerPermission]
    serializer_class = DeliveryNoteCustomerReadOnlySerializer
    queryset = DeliveryNoteCustomer.objects.filter(date__range=(date_last_week,date.today())).prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','schedules','delivery_note_customer','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver','schedules__product_order'))).select_related('customer','vehicle','driver')

class DeliveryNoteMaterialReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class gor get this week receipt note material
    '''
    permission_classes = [ManagerPermission]
    serializer_class = DeliveryNoteMaterialReadOnlySerializer
    queryset = DeliveryNoteMaterial.objects.filter(date__range=(date_last_week,date.today())).prefetch_related(
            Prefetch('materialreceipt_set',queryset=MaterialReceipt.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier','delivery_note_material','delivery_note_material__supplier'))).select_related('supplier')


class ProductionReportReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get data of production this week
    '''
    serializer_class = ProductionReportReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = ProductionReport.objects.filter(date__range=(date_last_week,date.today())).prefetch_related(
        Prefetch('productproductionreport_set',ProductProductionReport.objects.select_related('product','product__customer','product__type')),
        Prefetch('materialproductionreport_set',MaterialProductionReport.objects.select_related('material','material__uom','material__supplier'))).select_related('operator','machine','product','product__customer','product__type','process','process__product','process__process_type')


class ReportPresentageTimeLinessMaterialOrder(GetModelViewSet):
    '''
    a viewset class for get presentage of timeliness of material received
    '''
    serializer_class = PercentageSerializer
    permission_classes = [ManagerPermission]
    queryset = MaterialReceipt.objects.all()
    queryset_subcont_receipt = SubcontReceipt.objects.all()
    
    def list(self, request, *args, **kwargs):
        
        percentage = 100
        total_material_receipt = self.queryset.count()
        total_material_receipt_in_schedule = self.queryset.filter(schedules__isnull=False).count()
        total_material_receipt_on_time = self.queryset.filter(Q(schedules__isnull=False)&Q(schedules__date__gte=F('delivery_note_material__date'))).count()

        total_subcont_receipt = self.queryset_subcont_receipt.count()
        total_subcont_receipt_in_schedule = self.queryset_subcont_receipt.filter(schedules__isnull=False).count()
        total_subcont_receipt_on_time = self.queryset_subcont_receipt.filter(Q(schedules__isnull=False)&Q(schedules__date__gte=F('receipt_note__date'))).count()

        
        total_count_receipt_on_schedule = total_material_receipt_in_schedule + total_subcont_receipt_in_schedule
        total_receipt = total_material_receipt + total_subcont_receipt
        total_on_time = total_material_receipt_on_time + total_subcont_receipt_on_time
        unscheduled_receipt = total_receipt - total_count_receipt_on_schedule

        if total_material_receipt_in_schedule > 0 or total_subcont_receipt_in_schedule > 0:

            percentage = (total_on_time / total_count_receipt_on_schedule) * 100 

        data = {
            'percentage':percentage,
            'total_schedule':total_count_receipt_on_schedule,
            'total_schedule_on_time':total_on_time,
            'unscheduled':unscheduled_receipt
            }

        serializer = self.get_serializer(data)
        return response.Response(serializer.data)

class ReportPresentageDeliveryTimeLinessReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get presentage of delivery timeliness
    '''
    permission_classes = [ManagerPermission]
    serializer_class = PercentageSerializer
    queryset = ProductDeliverCustomer.objects.all()

    def list(self, request, *args, **kwargs):
        
        percentage = 100
        total_delivery = self.queryset.count()
        total_delivery_in_schedule = self.queryset.filter(schedules__isnull=False).count()
        total_on_time_delivery = self.queryset.filter(Q(schedules__isnull=False)&Q(schedules__date__gte=F('delivery_note_customer__date'))).count()
        

        unscheduled_delivery = total_delivery - total_delivery_in_schedule

        if total_delivery_in_schedule > 0:
            percentage = (total_on_time_delivery / total_delivery_in_schedule) * 100 

        data = {
            'percentage':percentage,
            'total_schedule': total_delivery_in_schedule,
            'total_schedule_on_time':total_on_time_delivery,
            'unscheduled':unscheduled_delivery
        }

        serializer = self.get_serializer(data)
        return response.Response(serializer.data)
