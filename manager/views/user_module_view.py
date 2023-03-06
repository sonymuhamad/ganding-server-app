from rest_framework import response,status
from django.contrib.auth.models import User,Group,Permission

from manager.viewsets import CreateUpdateDeleteModelViewSet,ReadOnlyModelViewSet,GetModelViewSet,UpdateModelViewSet,RetrieveModelViewSet
from manager.permissions import ManagerPermission,CanManageUser
from manager.serializer import UserManagementSerializer,UserReadOnlySerializer,GroupReadOnlySerializer,UserGroupManagementSerializer,PermissionReadOnlySerializer

from django.db.models import Prefetch,Count,Q
from django.shortcuts import get_object_or_404
from manager.shortcuts import get_key,invalid,get_default_password,filter_helper_app_label



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

        if instance.is_superuser and obj_group.pk == 4:
            invalid('Tidak bisa menghapus superuser dari divisi Manager')
        
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


