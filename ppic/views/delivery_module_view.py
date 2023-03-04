from rest_framework.viewsets import ReadOnlyModelViewSet,CreateUpdateDeleteModelViewSet

from django.db.models import Count,F,Prefetch,Q,Sum
from django.shortcuts import get_object_or_404

from manager.shortcuts import invalid
from ppic.permissions import PpicPermission,CanManageDelivery

from ppic.models import Vehicle,Driver,DeliveryNoteCustomer,DeliveryNoteSubcont,ProductDeliverCustomer,ProductDeliverSubcont,Product,ProductOrder,DeliverySchedule,Process,RequirementMaterial,RequirementProduct,WarehouseProduct,RequirementMaterialSubcont,RequirementProductsubcont

from ppic.serializers.product_serializer import OneDepthProductNestedProcessSerializer

from ppic.serializers.delivery_serializer import OneDepthDeliveryNoteCustomerSerializer,BaseDeliveryNoteCustomerSerializer,BaseDeliveryNoteSubcontSerializer,OneDepthDeliveryNoteSubcontSerializer,ProductDeliverySubcontManagementSerializer,ProductDeliverCustomerManagementSerializer,BaseDriverSerializer,BaseVehicleSerializer

from marketing.serializers.sales_order_serializer import TwoDepthProductOrderSerializer,ThreeDepthDeliveryScheduleSerializer

class VehicleViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve vehicle
    '''
    permission_classes = [PpicPermission]
    serializer_class = BaseVehicleSerializer
    queryset = Vehicle.objects.annotate(numbers_of_delivery_customer=Count('deliverynotecustomer',distinct=True),numbers_of_delivery_subcont=Count('deliverynotesubcont',distinct=True))


class VehicleManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud vehicle
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = BaseVehicleSerializer
    queryset = Vehicle.objects.all()

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']

        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.deliverynotecustomer_set.exists():
            invalid()

        if instance.deliverynotesubcont_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)


class DriverViewSet(ReadOnlyModelViewSet):
    '''
    viewset for get and retrieve driver
    '''
    permission_classes = [PpicPermission]
    serializer_class = BaseDriverSerializer
    queryset = Driver.objects.annotate(numbers_of_delivery_customer=Count('deliverynotecustomer',distinct=True),numbers_of_delivery_subcont=Count('deliverynotesubcont',distinct=True))

class DriverManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud driver
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = BaseDriverSerializer
    queryset = Driver.objects.all()
    
    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']

        instance = get_object_or_404(self.queryset,pk=pk)
        if instance.deliverynotecustomer_set.exists():
            invalid()

        if instance.deliverynotesubcont_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)

class DeliveryScheduleListViewSet(ReadOnlyModelViewSet):
    '''
    a view set for get and retrieve delivery schedule
    '''
    permission_classes = [PpicPermission]
    serializer_class = ThreeDepthDeliveryScheduleSerializer
    queryset = DeliverySchedule.objects.select_related('product_order','product_order__product','product_order__product__customer','product_order__product__type','product_order__sales_order','product_order__sales_order__customer').filter(Q(fulfilled_quantity__lte=0)&Q(product_order__delivered__lt=F('product_order__ordered')),Q(product_order__sales_order__fixed=True)&Q(product_order__sales_order__closed=False)).order_by('date')

class DeliveryNoteCustomerManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for create, update, delete delivery note
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = BaseDeliveryNoteCustomerSerializer
    queryset = DeliveryNoteCustomer.objects.select_related('driver','customer','vehicle').prefetch_related('productdelivercustomer_set')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_dn_customer = get_object_or_404(self.queryset,pk=pk)
        if instance_dn_customer.productdelivercustomer_set.exists():
            invalid()

        return super().destroy(request, *args, **kwargs)

class DeliveryNoteCustomerReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set for get and retrieve delivery note -> product delivery -> schedule if exists
    '''
    serializer_class = OneDepthDeliveryNoteCustomerSerializer
    queryset = DeliveryNoteCustomer.objects.get_queryset_related().prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.select_related('product_order','product_order__product','product_order__sales_order','schedules','delivery_note_customer','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver','schedules__product_order')))

class DeliveryNoteSubcontManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set to handle cud (Create,Update,Delete) delivery note subcont
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = BaseDeliveryNoteSubcontSerializer
    queryset = DeliveryNoteSubcont.objects.get_queryset_related().prefetch_related('productdeliversubcont_set')

    def destroy(self, request, *args, **kwargs):
        
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)

        for productSubcont in instance.productdeliversubcont_set.all():
            if productSubcont.quantity > 0:
                ## if quantity product subconstruction that included in this delivery note is not zero, raise error 

                invalid()

        return super().destroy(request, *args, **kwargs)

class DeliveryNoteSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get and retrieve delivery product subconstruction
    '''
    serializer_class = OneDepthDeliveryNoteSubcontSerializer
    queryset = DeliveryNoteSubcont.objects.prefetch_related(
        Prefetch('productdeliversubcont_set',queryset=ProductDeliverSubcont.objects.select_related('deliver_note_subcont','product','process','deliver_note_subcont__driver','deliver_note_subcont__vehicle','deliver_note_subcont__supplier','product__customer','product__type','process__process_type','process__product').annotate(received=Sum('subcontreceipt__quantity')).prefetch_related(
        Prefetch('requirementmaterialsubcont_set',queryset=RequirementMaterialSubcont.objects.select_related('product_subcont','material','material__uom','material__supplier') )).prefetch_related(
            Prefetch('requirementproductsubcont_set',queryset=RequirementProductsubcont.objects.select_related('product_subcont','product','product__customer','product__type'))).prefetch_related('receiptsubcontschedule_set'))).select_related('driver','vehicle','supplier')

class ProductOrderListViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve product ordered, used in delivery module, ppic
    '''
    permission_classes = [PpicPermission]
    serializer_class = TwoDepthProductOrderSerializer
    queryset   = ProductOrder.objects.select_related('product','sales_order','product__customer','product__type','sales_order__customer').filter(Q(delivered__lt=F('ordered')),Q(sales_order__fixed=True)&Q(sales_order__closed=False))

class ProductDeliverManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set for create, update, delete product delivery
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = ProductDeliverCustomerManagementSerializer
    queryset = ProductDeliverCustomer.objects.select_related('delivery_note_customer','product_order','schedules','product_order__product','product_order__sales_order__customer','delivery_note_customer__customer')

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance_pd = get_object_or_404(self.queryset,pk=pk)
        if instance_pd.quantity > 0 :
            invalid()

        return super().destroy(request, *args, **kwargs)

class ProductListSubcontReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a view set to get all product that can be delivered in delivery product subconstruction
    '''
    permission_classes = [PpicPermission]
    serializer_class = OneDepthProductNestedProcessSerializer
    queryset = Product.objects.prefetch_related(
            Prefetch('ppic_process_related',queryset=Process.objects.
            prefetch_related(
                Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))).
            prefetch_related(
                Prefetch('requirementproduct_set',queryset=RequirementProduct.objects.select_related('product'))).
            prefetch_related(
                Prefetch('requirementmaterial_set',queryset=RequirementMaterial.objects.select_related('material'))).select_related('process_type').filter(process_type=2) ))


class ProductDeliverySubcontManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a view set to handle cud (Create,Update,Delete) product that included in delivery note subcont
    '''
    permission_classes = [PpicPermission,CanManageDelivery]
    serializer_class = ProductDeliverySubcontManagementSerializer
    queryset = ProductDeliverSubcont.objects.prefetch_related('subcontreceipt_set').select_related('product','process','deliver_note_subcont')

    def destroy(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)

        if instance.quantity > 0:
            ## if quantity product subconstruction sended to supplier is greater than zero, raise errorr

            invalid()

        return super().destroy(request, *args, **kwargs)
