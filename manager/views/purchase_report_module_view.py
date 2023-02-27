from rest_framework.viewsets import GetModelViewSet
from django.db.models import Q,F,Prefetch,Sum
from rest_framework.response import Response
from datetime import date
from dateutil import rrule

from manager.permissions import ManagerPermission
from manager.serializer import ReportOrderEachMonthReadOnlySerializer,ReportSupplierOrderReadOnlySerializer

from ppic.serializer import MaterialOrderReadOnlySerializer,MaterialReceiptReadOnlySerializer
from ppic.models import MaterialOrder,MaterialReceipt,Material

from purchasing.models import Supplier



class MaterialOrderListReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get all upcoming materials
    '''
    serializer_class = MaterialOrderReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = MaterialOrder.objects.filter(Q(arrived__lt=F('ordered')))


class ReportMaterialOrderReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get report of order of material each month
    '''
    permission_classes = [ManagerPermission]
    serializer_class = ReportOrderEachMonthReadOnlySerializer
    queryset = MaterialOrder.objects.values('purchase_order_material__date__year','purchase_order_material__date__month').annotate(total_order=Sum('ordered')).order_by('purchase_order_material__date__year','purchase_order_material__date__month')
    storage_data = {}
    final_data = []

    def __init__(self, **kwargs) -> None:
        self.storage_data = {}
        self.final_data = []
        super().__init__(**kwargs)

    def generate_from_queryset(self):

        for data in self.queryset:
            year = data['purchase_order_material__date__year']
            month = data['purchase_order_material__date__month']
            self.storage_data[date(year,month,1)] = data['total_order'] 

        return


    def list(self, request, *args, **kwargs):
        
        queryset = self.filter_queryset(self.get_queryset())
        
        first_data = queryset.first()
        first_year = first_data['purchase_order_material__date__year']
        first_month = first_data['purchase_order_material__date__month']
        
        last_data = queryset.last()
        last_year = last_data['purchase_order_material__date__year']
        last_month = last_data['purchase_order_material__date__month']

        if queryset.count() > 0:
            self.generate_from_queryset()

            first_date = date(first_year,first_month,1)
            last_date = date(last_year,last_month,1)

            for dt in rrule.rrule(rrule.MONTHLY,dtstart=first_date,until=last_date):
                current_date = date(dt.year,dt.month,1)
                current_total_order = self.storage_data.get(current_date,0)
                
                self.final_data.append({
                    'order_date':current_date,
                    'total_order':current_total_order
                })

        serializer = self.get_serializer(self.final_data,many=True)
        return Response(serializer.data)

class MaterialReceiptListReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get a list of material received    
    '''
    serializer_class = MaterialReceiptReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = MaterialReceipt.objects.select_related('material_order','material_order__material','material_order__purchase_order_material','schedules','schedules__material_order','schedules__material_order__material','schedules__material_order__purchase_order_material','material_order__material__supplier','material_order__material__uom','material_order__purchase_order_material__supplier','delivery_note_material','delivery_note_material__supplier')

class ReportSupplierOrderReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get list of supplier, and its total material order and the most ordered material, then sort by total material order
    '''
    serializer_class = ReportSupplierOrderReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = Supplier.objects.annotate(supplier_total_order=Sum('ppic_materials__ppic_materialorders__ordered',default=0)).prefetch_related(
        Prefetch('ppic_material_related',queryset=Material.objects.select_related('uom','supplier').annotate(total_order=Sum('ppic_materialorders__ordered',default=0)).order_by('-total_order'))).order_by('-supplier_total_order')


    def return_serializer(self,data):
        serializer = self.get_serializer(data,many=True)
        return Response(serializer.data)

    def generate_data_from_queryset(self):
        data = []
        for supp in self.queryset:
            most_ordered_material = supp.ppic_material_related.first()
            
            temp_data = {
                "id" : supp.pk,
                "name":supp.name,
                "email":supp.email,
                "phone":supp.phone,
                "address":supp.address,
                "supplier_total_order":supp.supplier_total_order,
                "most_ordered_material":most_ordered_material
            }

            data.append(temp_data)
        return self.return_serializer(data)

    def list(self, request, *args, **kwargs):

        return self.generate_data_from_queryset()
