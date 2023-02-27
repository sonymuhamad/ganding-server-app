from rest_framework.viewsets import ReadOnlyModelViewSet,RetrieveModelViewSet,CreateUpdateDeleteModelViewSet
from django.db.models import Count,Q,Sum,Prefetch
from rest_framework.response import Response

from marketing.permissions import MarketingPermission,CanManageCustomer
from marketing.serializer import CustomerSerializer,InvoiceReadOnlySerializer
from marketing.models import Customer,SalesOrder,Invoice

from ppic.serializer import ProductDeliverCustomerReadOnlySerializer,ProductListSerializer
from ppic.models import Product,ProductDeliverCustomer,ProductOrder

from manager.shortcuts import invalid
from django.shortcuts import get_object_or_404
from marketing.shortcuts import validate_so

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
    
class ProductCustomerViewSet(ReadOnlyModelViewSet):
    permission_classes = [MarketingPermission]
    serializer_class = ProductListSerializer
    queryset = Product.objects.select_related('customer','type').annotate(total_stock=Sum('ppic_warehouseproducts__quantity'))

    def retrieve(self, request, *args, **kwargs):

        pk = int(kwargs['pk'])

        filtered_queryset = self.queryset.filter(customer__pk__exact=pk)
        serializer = self.get_serializer(filtered_queryset,many=True)
        return Response(serializer.data)
