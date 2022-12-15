
from django.db import connection, reset_queries
import time
import functools
from django.db.models import Prefetch,Count,Q

from django.contrib.auth.models import User
from rest_framework import response,status,permissions
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet,GetModelViewSet,CreateUpdateDeleteModelViewSet,UpdateModelViewSet,RetrieveModelViewSet,CreateModelViewSet

from marketing.models import Customer, SalesOrder
from purchasing.models import Supplier,PurchaseOrderMaterial
from .serializer import  *
from .shortcuts import get_default_password,filter_helper_app_label,get_key
from django.shortcuts import get_object_or_404

from ppic.models import DeliveryNoteCustomer, DetailMrp, MaterialRequirementPlanning, ProductDeliverCustomer,ProductOrder,Product,MaterialOrder, WarehouseProduct,Process
from .permissions import ManagerPermission,CanManageUser


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
    
    

class ReportMrpViewSet(GetModelViewSet):
    '''
    plant manager -> material requirement planning report
    '''
    serializer_class = ReportMrpSerializer
    permission_classes = [ManagerPermission]
    queryset = MaterialRequirementPlanning.objects.select_related('material').prefetch_related(
        Prefetch('detailmrp_set',queryset=DetailMrp.objects.select_related('product')))

    
class ReportSupplierPurchaseOrderViewSet(GetModelViewSet):
    '''
    plant manager -> schedule material receipt report
    '''
    serializer_class = SupplierSerializer
    permission_classes = [ManagerPermission]
    queryset = Supplier.objects.prefetch_related(
        Prefetch('purchasing_purchaseordermaterial_related',queryset=PurchaseOrderMaterial.objects.prefetch_related(
            Prefetch('materialorder_set',queryset=MaterialOrder.objects.prefetch_related('materialreceiptschedule_set').select_related('material__uom')))))
    
class ReportCustomerSalesOrderViewSet(ReadOnlyModelViewSet):
    '''
    plant manager -> sales report -> sales order
    '''
    
    serializer_class = CustomerSalesOrderSerializer
    permission_classes = [ManagerPermission]
    queryset = Customer.objects.prefetch_related(
        Prefetch('marketing_salesorder_related',queryset=SalesOrder.objects.prefetch_related(
            Prefetch('productorder_set',queryset=ProductOrder.objects.prefetch_related(
                Prefetch('product',queryset=Product.objects.prefetch_related(
                        Prefetch('ppic_process_related',queryset=Process.objects.prefetch_related(Prefetch('warehouseproduct_set',queryset=WarehouseProduct.objects.select_related('warehouse_type'))))).prefetch_related(Prefetch('ppic_warehouseproduct_related',queryset=WarehouseProduct.objects.select_related('warehouse_type')))))))))


class ReportDeliveryNoteCustomerViewSet(ReadOnlyModelViewSet):
    '''
    plant manager -> sales report -> delivery note
    '''
    serializer_class = CustomerDeliveryNoteSerializer
    permission_classes = [ManagerPermission]
    queryset = Customer.objects.prefetch_related(
        Prefetch('ppic_deliverynotecustomer_related',queryset=DeliveryNoteCustomer.objects.prefetch_related(
            Prefetch('productdelivercustomer_set',queryset=ProductDeliverCustomer.objects.prefetch_related(
                Prefetch('product_order',queryset=ProductOrder.objects.select_related('product','sales_order'))))).select_related('driver','vehicle')))

    

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
    permission_classes = [permissions.AllowAny]
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
    permission_classes = [permissions.AllowAny]
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








