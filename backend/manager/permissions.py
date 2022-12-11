from rest_framework.permissions import BasePermission
from .shortcuts import get_error_message

class ManagerPermission(BasePermission):
    '''
    a custom permission class to block access from user which not from manager groups
    '''
    message = 'access except from manager division is not allowed'

    def has_permission(self, request, view):
        permissions = request.user.get_all_permissions()
        return 'auth.can_access_manager' in permissions


class CanManageUser(BasePermission):
    '''
    a custom permission for disabled access to manage user if not granted
    '''
    message = get_error_message('User')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_user')

