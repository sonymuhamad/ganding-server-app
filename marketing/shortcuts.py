from manager.shortcuts import invalid
from django.db.models import Q,QuerySet

def validate_productorder(queryset_po:QuerySet)-> None:
    '''
    check if there are product order which is in progress 
    '''
    if queryset_po.filter(Q(delivered__gt=0)|Q(ordered__gt=0)).exists():
        invalid()
        
def validate_so(queryset:QuerySet) -> None:
    '''
    check if there are closed sales order 
    '''    
    if queryset.filter(closed=True).exists():
        invalid()
    
    for so in queryset:
        '''
        loop through queryset sales order to check its product ordered
        '''
        queryset_productorder = so.productorder_set.all()
        validate_productorder(queryset_productorder)
        
