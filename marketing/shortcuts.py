from manager.shortcuts import invalid

def validate_productorder(queryset_po)-> None:
    for productorder in queryset_po:
        if productorder.delivered > 0 or productorder.ordered > 0:
            invalid()
            
def validate_so(queryset) -> None:
    for so in queryset:
        if so.closed:
            invalid()
        queryset_productorder = so.productorder_set.all()
        validate_productorder(queryset_productorder)
        
