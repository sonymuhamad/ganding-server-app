from django.db import connection, reset_queries
import time
import functools
from django.db.models import Prefetch,Count,Q,Sum,F,Avg

from django.contrib.auth.models import User
from rest_framework import response,status,permissions
from rest_framework.viewsets import ReadOnlyModelViewSet,GetModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,RetrieveModelViewSet

from marketing.models import Customer
from purchasing.models import Supplier
from .serializer import  *
from .shortcuts import get_default_password,filter_helper_app_label,get_key,date_last_week
from django.shortcuts import get_object_or_404

from ppic.models import DeliveryNoteCustomer,  ProductDeliverCustomer,ProductOrder,Product,MaterialOrder,MaterialReceipt,SubcontReceipt,ProductionReport,DeliveryNoteMaterial,MaterialProductionReport,ProductProductionReport

from .permissions import ManagerPermission,CanManageUser
from datetime import date
from dateutil import rrule
from dateutil.relativedelta import relativedelta

from ppic.serializer import ProductOrderListSerializer,ProductDeliverCustomerReadOnlySerializer,MaterialOrderReadOnlySerializer,MaterialReceiptReadOnlySerializer,DeliveryNoteCustomerReadOnlySerializer,DeliveryNoteMaterialReadOnlySerializer,ProductionReportReadOnlySerializer

def queryDebug(func):

    @functools.wraps(func)
    def inner_func(*args, **kwargs):

        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.2f}s")

        return result

    return inner_func


class UserManagementViewSet(CreateUpdateDeleteModelViewSet):
    '''
    a viewset for cud user
    '''
    serializer_class = UserManagementSerializer
    permission_classes = [ManagerPermission,CanManageUser]
    queryset = User.objects.prefetch_related('groups')

    def destroy(self, request, *args, **kwargs):
        
        instance = self.get_object()

        if instance.groups.exists():
            invalid()
        
        self.perform_destroy(instance)
        return response.Response(status=status.HTTP_204_NO_CONTENT)
    
    def partial_update(self, request, *args, **kwargs):
        '''
        a endpoint for reset password of user, PATCH METHOD
        '''
        instance = self.get_object()
        password = get_default_password()
        instance.password = password
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

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

class UserReadOnlyViewSet(ReadOnlyModelViewSet):
    '''
    a viewset for get and retrieve user nested to -> groups, permissions
    '''
    serializer_class = UserReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = User.objects.prefetch_related('groups').prefetch_related(Prefetch('user_permissions',Permission.objects.select_related('content_type')))


class GroupReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get list of groups
    '''
    serializer_class = GroupReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = Group.objects.prefetch_related('user_set').annotate(number_of_user=Count('user')).order_by('-id')


class UserGroupManagementAddViewSet(UpdateModelViewSet):
    '''
    a viewset for add group to each user (create())
    '''
    serializer_class = UserGroupManagementSerializer
    permission_classes = [ManagerPermission,CanManageUser]
    queryset = User.objects.prefetch_related('groups')
    queryset_group = Group.objects.all()

    def update(self, request, *args, **kwargs):
        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        
        id_group = request.data.get('group',None)
        queryset_group_from_instance = instance.groups.all()

        obj_group = get_object_or_404(self.queryset_group,pk=id_group)

        if not queryset_group_from_instance.contains(obj_group):
            instance.groups.add(obj_group)
        
        serializer = self.get_serializer(obj_group)

        return response.Response(serializer.data,status=status.HTTP_200_OK)

class UserGroupManagementDeleteViewSet(UpdateModelViewSet):
    '''
    a viewset for delete group from user
    '''
    serializer_class = UserGroupManagementSerializer
    permission_classes = [ManagerPermission,CanManageUser]
    queryset = User.objects.prefetch_related('groups')
    queryset_group =  Group.objects.all()

    def update(self, request, *args, **kwargs):

        pk = kwargs['pk']
        instance = get_object_or_404(self.queryset,pk=pk)
        
        id_group = request.data.get('group',None)
        
        queryset_group_from_instance = instance.groups.all()
        if queryset_group_from_instance.count() == 1:
            invalid('Cannot perform remove division from user, because user at least have one division')
        
        obj_group = get_object_or_404(self.queryset_group,pk=id_group)
        
        if queryset_group_from_instance.contains(obj_group):
            instance.groups.remove(obj_group)
        
        app_label = get_key(obj_group.name)
        permission_have_to_delete = instance.user_permissions.filter(content_type__app_label=app_label)
        
        for i in permission_have_to_delete:
            instance.user_permissions.remove(i)

        serializer = self.get_serializer(obj_group)

        return response.Response(serializer.data,status=status.HTTP_200_OK) 


class PermissionListReadOnlyViewSet(RetrieveModelViewSet):
    '''
    a viewset for get permission list that can be granted to the associated user
    '''
    serializer_class = PermissionReadOnlySerializer
    queryset = Permission.objects.all()
    permission_classes = [ManagerPermission]
    queryset_user = User.objects.prefetch_related('user_permissions','groups')
    filter_helper = {
        1:'marketing',
        2:'purchasing',
        3:'ppic',
        4:'auth'
    }

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']
        temp_storage_permissions = []
        obj_user = get_object_or_404(self.queryset_user,pk=pk)
        queryset_permissions_from_user = obj_user.user_permissions.all()

        for group in obj_user.groups.all():
            app_label_from_group = self.filter_helper[group.id]
            ## get app label from helper, based on its group

            queryset_permission = Permission.objects.select_related('content_type').filter(Q(codename__startswith='can_manage')&Q(content_type__app_label=app_label_from_group))

            for obj_permission in queryset_permission:
                if not queryset_permissions_from_user.contains(obj_permission):
                    temp_storage_permissions.append(obj_permission)

        
        serializer = self.get_serializer(temp_storage_permissions, many=True)
        return response.Response(serializer.data)


class UserPermissionAddManagementViewSet(UpdateModelViewSet):
    '''
    a viewset for add permission to user, based on its group
    '''
    serializer_class = PermissionReadOnlySerializer
    permission_classes = [ManagerPermission,CanManageUser]
    queryset = Permission.objects.select_related('content_type')
    queryset_user = User.objects.prefetch_related('groups','user_permissions')
    

    def update(self, request, *args, **kwargs):

        pk = kwargs['pk']
        obj_user = get_object_or_404(self.queryset_user,pk=pk)
        id_permission = request.data.get('id_permission',None)

        obj_permission = get_object_or_404(self.queryset,pk=id_permission)
        serializer = self.get_serializer(obj_permission)

        if not obj_user.user_permissions.contains(obj_permission):
            
            group_name_from_app_label = filter_helper_app_label[obj_permission.content_type.app_label]
            if not obj_user.groups.filter(name=group_name_from_app_label).exists():
                ## if user doesn't have group related to this permission
                
                invalid('Error while perform granting permission access')

            obj_user.user_permissions.add(obj_permission)

        return response.Response(serializer.data)


class UserPermissionDeleteManagementViewSet(UpdateModelViewSet):
    '''
    a viewset for delete permission acces from user
    '''
    serializer_class = PermissionReadOnlySerializer
    permission_classes = [ManagerPermission,CanManageUser]
    queryset = Permission.objects.select_related('content_type')
    queryset_user = User.objects.prefetch_related('groups','user_permissions')
    filter_helper_app_label = {
        'auth':'plant-manager',
        'ppic':'ppic',
        'purchasing':'purchasing',
        'marketing':'marketing'
    }

    def update(self, request, *args, **kwargs):

        pk = kwargs['pk']
        obj_user = get_object_or_404(self.queryset_user,pk=pk)

        id_permission = request.data.get('id_permission')
        obj_permission = get_object_or_404(self.queryset,pk=id_permission)
        serializer = self.get_serializer(obj_permission)


        if obj_user.user_permissions.contains(obj_permission):
            obj_user.user_permissions.remove(obj_permission)

        return response.Response(serializer.data)


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
    queryset = Customer.objects.annotate(customer_total_order=Sum('ppic_products__ppic_productorders__ordered',filter=Q(ppic_products__ppic_productorders__sales_order__fixed=True),default=0)).prefetch_related(Prefetch('ppic_product_related',queryset=Product.objects.select_related('customer','type').annotate(total_order=Sum('ppic_productorders__ordered',filter=Q(ppic_productorders__sales_order__fixed=True),default=0)).order_by('-total_order'))).order_by('-customer_total_order')

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


class ReportProductInProgressReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get list of product in order
    '''
    permission_classes = [ManagerPermission]
    serializer_class = ProductOrderListSerializer
    queryset = ProductOrder.objects.select_related('product','sales_order','product__customer','product__type','sales_order__customer').filter(Q(delivered__lt=F('ordered')),Q(sales_order__fixed=True)&Q(sales_order__closed=False)).order_by('pk')


class ReportProductDeliverCustomerReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get list of product delivery and show its timeliness on react (frontend)
    '''
    permission_classes = [ManagerPermission]
    serializer_class = ProductDeliverCustomerReadOnlySerializer
    queryset = ProductDeliverCustomer.objects.select_related('delivery_note_customer','product_order','delivery_note_customer__customer','delivery_note_customer__vehicle','delivery_note_customer__driver','product_order__product','product_order__sales_order','schedules','schedules__product_order')



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
        return response.Response(serializer.data)


class MaterialOrderListReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get all upcoming materials
    '''
    serializer_class = MaterialOrderReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = MaterialOrder.objects.filter(Q(arrived__lt=F('ordered')))


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

    result_data = []


    def return_serializer(self):
        serializer = self.get_serializer(self.result_data,many=True)

        return response.Response(serializer.data)

    def generate_data_from_queryset(self):
      
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

            self.result_data.append(temp_data)

        return self.return_serializer()

    def list(self, request, *args, **kwargs):

        return self.generate_data_from_queryset()


class ReportProductionReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get data total quantity production, and total quantity not good production each month
    '''
    serializer_class = ReportProductionReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = ProductionReport.objects.filter(date__lte=date.today()).values('date__year','date__month').annotate(total_good_production=Sum('quantity',default=0,filter=Q(process__warehouseproduct__warehouse_type__id__contains=1))).annotate(total_not_good_production=Sum('quantity_not_good',default=0)).order_by('date__year','date__month')

    storage_data = []

    def loop_through_dates(self,first_date,last_date,store_data):

        for dt in rrule.rrule(rrule.MONTHLY,dtstart=first_date,until=last_date):
            
            data_production = store_data.get(dt.date(),{
                "total_good_production":0,
                "total_not_good_production":0
            })

            temp_data = {
                'production_date':dt.date(),
                **data_production
            }
            
            self.storage_data.append(temp_data)
            
            ### append each data to storage data before return all data

        return

    def generate_queryset(self,queryset) -> dict:
        
        ## set dates to key of dictionary, and set data total productions as value

        store_data = {}
        for data in queryset:
            year = data['date__year']
            month = data['date__month']
            each_date = date(year,month,1)

            store_data[each_date] = {
                'total_good_production':data['total_good_production'],
                'total_not_good_production':data['total_not_good_production']
            }
            
        return store_data

    def generate_data_and_return_from_queryset(self):
        
        queryset = self.filter_queryset(self.get_queryset())
        first_data = queryset.first()
        last_data = queryset.last()

        if first_data:
            # if data is exists then do generate, else return empty array(list)

            first_year = first_data['date__year']
            first_month = first_data['date__month']
            first_date = date(first_year,first_month,1)

            last_year = last_data['date__year']
            last_month = last_data['date__month']
            last_date = date(last_year,last_month,1)

            store_data = self.generate_queryset(queryset)
            self.loop_through_dates(first_date,last_date,store_data)

        serializer = self.get_serializer(self.storage_data,many=True)

        return  response.Response(serializer.data)

    def list(self, request, *args, **kwargs):

        return self.generate_data_and_return_from_queryset()


class OperatorReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get all data operator, avg production, good percentage of production, and times do production
    '''
    serializer_class = OperatorReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = Operator.objects.annotate(times_do_production=Count('productionreport',distinct=True),avg_production=Avg('productionreport__quantity'),good_percentage=(Sum('productionreport__quantity') / (Sum('productionreport__quantity')+Sum('productionreport__quantity_not_good'))) * 100,total_goods_produced=Sum('productionreport__quantity')  )


class MachineReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset class for get all data machine, avg production, goods percentage of production, and times used in production
    '''
    serializer_class = MachineReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = Machine.objects.prefetch_related('productionreport_set').annotate(times_do_production=Count('productionreport',distinct=True),avg_production=Avg('productionreport__quantity'),good_percentage=(Sum('productionreport__quantity')/(Sum('productionreport__quantity')+Sum('productionreport__quantity_not_good'))) * 100,total_goods_produced=Sum('productionreport__quantity') )


class ProductionReportReadOnlyViewSet(GetModelViewSet):
    '''
    a viewset for get data of production this week
    '''
    serializer_class = ProductionReportReadOnlySerializer
    permission_classes = [ManagerPermission]
    queryset = ProductionReport.objects.filter(date__range=(date_last_week,date.today())).prefetch_related(
        Prefetch('productproductionreport_set',ProductProductionReport.objects.select_related('product','product__customer','product__type')),
        Prefetch('materialproductionreport_set',MaterialProductionReport.objects.select_related('material','material__uom','material__supplier'))).select_related('operator','machine','product','product__customer','product__type','process','process__product','process__process_type')
























