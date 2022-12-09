from rest_framework.permissions import BasePermission
from manager.shortcuts import get_error_message

class MarketingPermission(BasePermission):
    '''
    a custom permission class to block access from user which not marketing group
    '''
    message = 'access except from marketing division is not allowed'

    def has_permission(self, request, view):

        return request.user.has_perm('can_access_marketing')
        
class CanManageCustomer(BasePermission):
    '''
    a custom permission for disabled access to manage data customer if not granted
    '''
    message = get_error_message('customer')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_customer')


class CanManageSalesOrder(BasePermission):
    '''
    a custom permission for disabled access to manage sales order if not granted
    '''
    message = get_error_message('sales order')

    def has_permission(self, request, view):
        return request.user.has_perm('can_manage_sales_order')

