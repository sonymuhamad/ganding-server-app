from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import *


router = DefaultRouter()

mrp_management_post = MrpManagementViewSet.as_view({
    'post':'create',
    'get':'list',
})

mrp_management_put_and_delete = MrpManagementViewSet.as_view({
    'put':'update',
    'delete':'destroy',
})

warehouse_management_put = WarehouseProductManagementViewSet.as_view({
    'put':'update'
})


router.register(r'uom-management',UomManagementViewSet,basename='uom-management')

router.register(r'product-detail',ProductCustomerReadOnlyViewSet,basename='product-detail')
router.register(r'product-management',ProductManagementViewSet,basename='product-management')
router.register(r'requirement-product',RequirementProductViewSet,basename='requirement-product')

router.register(r'requirement-material',RequirementMaterialViewSet,basename='requirement-material')
router.register(r'material-detail',MaterialSupplierReadOnlyViewSet,basename='material-detail')
router.register(r'material',MaterialSerializer,basename='material')

router.register(r'uom-conversion-detail',UomConversionReadOnlyViewSet,basename='uom-conversion-detail')
router.register(r'uom-conversion-management',UomConversionManagementViewSet,basename='uom-conversion-management')
router.register(r'based-conversion-detail',BasedConversionMaterialReadOnlyViewSet,basename='based-conversion-detail')
router.register(r'based-conversion-management',BasedConversionMaterialManagementViewSet,basename='based-conversion-management')
router.register(r'report-conversion-detail',ReportConversionMaterialReadOnlyViewSet,basename='report-conversion-detail')
router.register(r'report-conversion-management',ReportConversionMaterialManagementViewSet,basename='report-conversion-management'
)

router.register(r'warehouse-material',UomWarehouseMaterialViewSet,basename='warehouse-material')
router.register(r'warehouse-management-material',WarehouseMaterialManagementViewSet,basename='warehouse-management-material')

router.register(r'warehouse-management-product',WarehouseProductManagementViewSet,basename='warehouse-management-product')
router.register(r'warehouse-subcont',WarehouseSubcontViewSet,basename='warehouse-subcont')
router.register(r'warehouse-wip',WarehouseWipViewSet,basename='warehouse-wip')
router.register(r'warehouse-fg',WarehouseFinishGoodViewSet,basename='warehouse-fg')

router.register(r'mrp-details',MrpReadOnlyViewSet,basename='mrp-details')

router.register(r'deliverynote-material',DeliveryNoteMaterialReadOnlyViewSet,basename='deliverynote-material')
router.register(r'deliverynote-material-management',DeliveryNoteMaterialManagementViewSet,basename='deliverynote-material-management')
router.register(r'material-receipt-management',MaterialReceiptManagementViewSet,basename='material-receipt-management')

router.register(r'deliverynote-customer',DeliveryNoteCustomerReadOnlyViewSet,basename='deliverynote-customer')
router.register(r'deliverynote-customer-management',DeliveryNoteCustomerManagementViewSet,basename='deliverynote-customer-management')
router.register(r'product-deliver-management',ProductDeliverManagementViewSet,basename='product-deliver-management')

router.register(r'production-report',ProductionReportReadOnlyViewSet,basename='production-report')
router.register(r'production-report-management',ProductionReportManagementViewSet,basename='production-report-management')


urlpatterns = [
    path('',include(router.urls)),
    path('mrp-management/',mrp_management_post,name='mrp-management'),
    path('mrp-management/<int:pk>/',mrp_management_put_and_delete,name='mrp-management'),    
]
