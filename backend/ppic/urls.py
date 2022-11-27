from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import *


router = DefaultRouter()


router.register(r'uom-management',UomManagementViewSet,basename='uom-management')
router.register(r'machine',MachineViewSet,basename='machine')
router.register(r'operator',OperatorViewSet,basename='operator')
router.register(r'vehicle',VehicleViewSet,basename='vehicle')
router.register(r'driver',DriverViewSet,basename='driver')

router.register(r'product-type',ProductTypeViewSet,basename='product-type')
router.register(r'process-type',ProcessTypeViewSet,basename='process-type')
router.register(r'customer-lists',CustomerListViewSet,basename='customer-lists')
router.register(r'product-lists',ProductListViewSet,basename='product-lists')
router.register(r'material-lists',MaterialListViewSet,basename='material-lists')
router.register(r'supplier-list',SupplierListViewSet,basename='supplier-list')

router.register(r'product-list',ProductListReadOnlyViewSet,basename='product-list')
router.register(r'product-detail',ProductDetailReadOnlyViewSet,basename='product-detail')
router.register(r'product-management',ProductManagementViewSet,basename='product-management')
router.register(r'process-management',ProcessManagementViewSet,basename='process-management')
router.register(r'requirement-product',RequirementProductViewSet,basename='requirement-product')

router.register(r'requirement-material',RequirementMaterialViewSet,basename='requirement-material')
router.register(r'supplier-material-list',MaterialSupplierReadOnlyViewSet,basename='supplier-material-list')
router.register(r'material',MaterialViewSet,basename='material')
router.register(r'material-detail',MaterialDetailViewSet,basename='material-detail')
router.register(r'uom-list',UomListViewSet,basename='uom-list')


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
router.register(r'mrp-management',MrpManagementViewSet,basename='mrp-management')

router.register(r'material-order-list',MaterialOrderReadOnlyViewSet,basename='material-order-list')
router.register(r'material-receipt-schedule',MaterialReceiptScheduleReadOnlyViewSet,basename='material-receipt-schedule')
router.register(r'deliverynote-material',DeliveryNoteMaterialReadOnlyViewSet,basename='deliverynote-material')
router.register(r'deliverynote-material-management',DeliveryNoteMaterialManagementViewSet,basename='deliverynote-material-management')
router.register(r'material-receipt-management',MaterialReceiptManagementViewSet,basename='material-receipt-management')

router.register(r'product-order-list',ProductOrderListViewSet,basename='product-order-list')
router.register(r'delivery-schedule',DeliveryScheduleListViewSet,basename='delivery-schedule')
router.register(r'delivery-note',DeliveryNoteCustomerReadOnlyViewSet,basename='delivery-note-customer')
router.register(r'delivery-note-management',DeliveryNoteCustomerManagementViewSet,basename='delivery-note-customer-management')
router.register(r'product-delivery',ProductDeliverManagementViewSet,basename='product-deliver-management')

router.register(r'delivery-note-subcont',DeliveryNoteSubcontReadOnlyViewSet,basename='delivery-note-subcont-read-only')
router.register(r'delivery-note-subcont-management',DeliveryNoteSubcontManagementViewSet,basename='delivery-note-subcont-management')
router.register(r'product-delivery-subcont-management',ProductDeliverySubcontManagementViewSet,basename='product-delivery-subcont')
router.register(r'product-delivery-subcont',ProductDeliverSubcontReadOnlyViewSet,basename='product-subcont')
router.register(r'receipt-subcont-schedule-management',ReceiptSubcontScheduleManagementViewSet,basename='receipt-subcont-schedule-management')
router.register(r'production-subcont-list',ProductListSubcontReadOnlyViewSet,basename='production-subcont-list')


router.register(r'receipt-note-subcont-management',ReceiptNoteSubcontManagementViewSet,basename='receipt-note-subcont-management')
router.register(r'receipt-note-subcont',ReceiptNoteSubcontReadOnlyViewSet,basename='receipt-note-subcont')
router.register(r'product-subcont-receipt-management',SubcontReceiptManagementViewSet,basename='product-subcont-receipt')
router.register(r'receipt-subcont-schedule-list',ReceiptSubcontScheduleListViewSet,basename='receipt-subcont-schedule-list')
router.register(r'product-subcont-list',ProductDeliverSubcontListViewSet,basename='product-subcont-list')


router.register(r'production-report',ProductionReportReadOnlyViewSet,basename='production-report')
router.register(r'production-report-management',ProductionReportManagementViewSet,basename='production-report-management')
router.register(r'production-priority',ProductionPriorityViewSet,basename='production-priority')
router.register(r'production-list',ProductionListViewSet,basename='production-list')

router.register(r'list-product-in-order',ProductOrderedViewSet,basename='list-product-in-order')
router.register(r'list-material-in-order',MaterialOrderedViewSet,basename='list-material-in-order')
router.register(r'monthly-production-report',MonthlyProductionReportViewSet,basename='monthly-production-report')



urlpatterns = [
    path('',include(router.urls)),  
]
