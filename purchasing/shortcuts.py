from manager.shortcuts import invalid


def validate_mo(queryset):
    for mo in queryset:
            if mo.arrived > 0:
                invalid()

def validate_po(queryset):

    for po in queryset:
        if po.done:
            invalid()
        queryset_mo = po.materialorder_set.all() 
        validate_mo(queryset_mo)
