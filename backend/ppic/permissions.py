from rest_framework.permissions import BasePermission
from manager.shortcuts import get_error_message

class PpicPermission(BasePermission):
    '''
    a custom permission for disabled access from user not ppic group
    '''
    message = 'access except from ppic division is not allowed'

    def has_permission(self, request, view):
        permissions = request.user.get_all_permissions()
        return 'auth.can_access_ppic' in permissions


class CanManageProduct(BasePermission):
    '''
    a custom permission for disabled access to manage product if not granted
    '''

    message = get_error_message('products')

    def has_permission(self, request, view):
        
        return request.user.has_perm('can_manage_product')

class CanManageMaterial(BasePermission):
    '''
    a custom permission for disabled access to manage material if not granted
    '''
    message = get_error_message('materials')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_material')

class CanManageProduction(BasePermission):
    '''
    a custom permission for disabled access to manage production if not granted
    '''

    message = get_error_message('production')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_production')


class CanManageDelivery(BasePermission):
    '''
    a custom permission for disabled access to manage delivery if not granted
    '''

    message = get_error_message('delivery')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_delivery')

class CanManageWarehouse(BasePermission):
    '''
    a custom permission for disabled access to manage warehouse if not granted
    '''
    message = get_error_message('warehouse')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_warehouse')








