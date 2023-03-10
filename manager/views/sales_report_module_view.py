from rest_framework import response
from django.db.models import Sum,Q,Prefetch

from datetime import date
from dateutil import rrule
from manager.viewsets import GetModelViewSet
from manager.permissions import ManagerPermission
from manager.serializer import ReportOrderEachMonthReadOnlySerializer,ReportCustomerOrderReadOnlySerializer

from marketing.models import Customer

from ppic.models import ProductOrder,Product



class ReportProductOrderReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset provide report of total product ordered each month
    '''
    permission_classes = [ManagerPermission]
    serializer_class = ReportOrderEachMonthReadOnlySerializer
    queryset = ProductOrder.objects.filter(Q(sales_order__fixed=True),sales_order__date__lte=date.today()).values('sales_order__date__year','sales_order__date__month').annotate(total_order=Sum('ordered')).order_by('sales_order__date__year','sales_order__date__month')

    def generate_date_from_queryset(self) -> dict:

        store_data = {}

        for data in self.queryset:
            year = data['sales_order__date__year']
            month = data['sales_order__date__month']
            store_data[date(year,month,1)] = data['total_order']
        
        return store_data

    def list(self, request, *args, **kwargs):

        first_monthly_order = self.queryset.first()
        last_monthly_order = self.queryset.last()
        data_report = []

        
        if self.queryset.count() > 0:
            generated_data = self.generate_date_from_queryset()

            first_year = first_monthly_order['sales_order__date__year']
            first_month = first_monthly_order['sales_order__date__month']

            last_year = last_monthly_order['sales_order__date__year']
            last_month = last_monthly_order['sales_order__date__month']

            first_date = date(first_year,first_month,1)
            last_date = date(last_year,last_month,1)

            for dt in rrule.rrule(rrule.MONTHLY,dtstart=first_date,until=last_date):
                current_date = date(dt.year,dt.month,1)
                current_total_order = generated_data.get(current_date,0)
                data_report.append({
                    'order_date':current_date,
                    'total_order':current_total_order
                })

        serializer = self.get_serializer(data_report,many=True)
        return response.Response(serializer.data)

class ReportCustomerAndOrderedProductViewSet(GetModelViewSet):
    '''
    a viewset for get all customer and its total product order, and most ordered product
    '''
    permission_classes = [ManagerPermission]
    serializer_class = ReportCustomerOrderReadOnlySerializer
    queryset = Customer.objects.annotate(customer_total_order=Sum('ppic_products__ppic_productorders__ordered',filter=Q(ppic_products__ppic_productorders__sales_order__fixed=True),default=0)).prefetch_related(
        Prefetch('ppic_product_related',queryset=Product.objects.select_related('customer','type').annotate(total_order=Sum('ppic_productorders__ordered',filter=Q(ppic_productorders__sales_order__fixed=True),default=0)).order_by('-total_order'))).order_by('-customer_total_order')

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
                'customer_total_order':cust.customer_total_order,
                'most_ordered_product':most_ordered_product
            }
            data.append(temp_data)

        return data

    def list(self, request, *args, **kwargs):

        validate_data = self.generate_data_from_queryset()

        serializer = self.get_serializer(validate_data,many=True)
        return response.Response(serializer.data)