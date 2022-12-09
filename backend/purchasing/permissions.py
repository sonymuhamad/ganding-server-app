from rest_framework.permissions import BasePermission
from manager.shortcuts import get_error_message

class PurchasingPermission(BasePermission):
    '''
    a custom permission classes to block acces from user which not purchasing group
    '''
    message = 'access except from purchasing division is not allowed'

    def has_permission(self, request, view):
        return request.user.has_perm('can_access_purchasing')


class CanManageSupplier(BasePermission):
    '''
    a custom permission for disabled access to manage supplier if not granted
    '''
    message = get_error_message('supplier')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_supplier')


class CanManagePurchaseOrderMaterial(BasePermission):
    '''
    a custom permission for disabled access to manage purchase order material if not granted
    '''
    message = get_error_message('purchase order material')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_purchase_order_material')
