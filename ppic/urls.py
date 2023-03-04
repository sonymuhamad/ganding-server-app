from rest_framework.routers import DefaultRouter
from django.urls import path,include

# from .views import *


from ppic.views.product_module_view import ProductTypeManagementViewSet,ProductListViewSet,ProductTypeViewSet,ProcessTypeManagementViewSet,ProcessTypeViewSet,ProductManagementViewSet,ProductDetailReadOnlyViewSet,ProcessManagementViewSet

from ppic.views.material_module_view import MaterialListViewSet,UomListViewSet,UomManagementViewSet,MaterialManagementViewSet,MrpReadOnlyViewSet,MrpManagementViewSet,MaterialDetailViewSet


from ppic.views.production_module_view import MachineManagementViewSet,MachineViewSet,OperatorManagementViewSet,OperatorViewSet,ProductionReportManagementViewSet,ProductionReportReadOnlyViewSet,ProductionPriorityViewSet,ReceiptSubcontScheduleManagementViewSet,ProductDeliverSubcontReadOnlyViewSet,ProductionListViewSet

from ppic.views.delivery_module_view import VehicleManagementViewSet,VehicleViewSet,DriverManagementViewSet,DriverViewSet,DeliveryNoteCustomerManagementViewSet,DeliveryNoteCustomerReadOnlyViewSet,DeliveryNoteSubcontManagementViewSet,DeliveryNoteSubcontReadOnlyViewSet,ProductDeliverManagementViewSet,ProductDeliverySubcontManagementViewSet,ProductListSubcontReadOnlyViewSet,ProductOrderListViewSet,DeliveryScheduleListViewSet

from ppic.views.warehouse_module_view import UomWarehouseMaterialViewSet,DeliveryNoteMaterialManagementViewSet,DeliveryNoteMaterialReadOnlyViewSet,ReceiptNoteSubcontManagementViewSet,ReceiptNoteSubcontReadOnlyViewSet,MaterialReceiptManagementViewSet,MaterialReceiptScheduleReadOnlyViewSet,SubcontReceiptManagementViewSet,ReceiptSubcontScheduleListViewSet,WarehouseFinishGoodViewSet,WarehouseMaterialManagementViewSet,WarehouseProductManagementViewSet,WarehouseWipViewSet,MaterialOrderReadOnlyViewSet,ProductDeliverSubcontListViewSet

from ppic.views.ppic_dashboard_view import MonthlyProductionReportViewSet,ProductOrderedViewSet,MaterialOrderedViewSet

router = DefaultRouter()


router.register(r'products',ProductListViewSet,basename='products')
router.register(r'products-detail',ProductDetailReadOnlyViewSet,basename='products-detail')
router.register(r'type/product',ProductTypeViewSet,basename='type/product')
router.register(r'type/product-management',ProductTypeManagementViewSet,basename='type/product-management') 
router.register(r'type/process',ProcessTypeViewSet,basename='type/process')
router.register(r'type/process-management',ProcessTypeManagementViewSet,basename='type/process-management') 
router.register(r'process/management',ProcessManagementViewSet,basename='process/management')
router.register(r'products-management',ProductManagementViewSet,basename='products-management')


router.register(r'uoms-management',UomManagementViewSet,basename='uoms-management')
router.register(r'uoms',UomListViewSet,basename='uoms')
router.register(r'mrps-management',MrpManagementViewSet,basename='mrps-management')
router.register(r'mrps',MrpReadOnlyViewSet,basename='mrps')
router.register(r'materials',MaterialListViewSet,basename='materials')
router.register(r'materials-detail',MaterialDetailViewSet,basename='materials-detail')
router.register(r'materials-management',MaterialManagementViewSet,basename='materials-management')  


router.register(r'warehouse/material',UomWarehouseMaterialViewSet,basename='warehouse/material')
router.register(r'warehouse/material-management',WarehouseMaterialManagementViewSet,basename='warehouse/material-management')
router.register(r'warehouse/product-management',WarehouseProductManagementViewSet,basename='warehouse/product-management')
router.register(r'warehouse/wip',WarehouseWipViewSet,basename='warehouse/wip')
router.register(r'warehouse/fg',WarehouseFinishGoodViewSet,basename='warehouse/fg')
router.register(r'receipts/material',DeliveryNoteMaterialReadOnlyViewSet,basename='receipts/material')
router.register(r'receipts/material-management',DeliveryNoteMaterialManagementViewSet,basename='receipts/material-management')
router.register(r'receipts/materials-received',MaterialReceiptManagementViewSet,basename='receipts/materials-received')
router.register(r'receipts/subcont',ReceiptNoteSubcontReadOnlyViewSet,basename='receipts/subcont')
router.register(r'receipts/subcont-management',ReceiptNoteSubcontManagementViewSet,basename='receipts/subcont-management')
router.register(r'receipts/products-received',SubcontReceiptManagementViewSet,basename='receipts/products-received')
router.register(r'order/material-incomplete',MaterialOrderReadOnlyViewSet,basename='order/material-incomplete')
router.register(r'schedules/material-incomplete',MaterialReceiptScheduleReadOnlyViewSet,basename='schedules/material-incomplete')
router.register(r'order/subcont-incomplete',ProductDeliverSubcontListViewSet,basename='product-subcont-list')
router.register(r'schedules/subcont-incomplete',ReceiptSubcontScheduleListViewSet,basename='schedules/subcont-incomplete')


router.register(r'order/product-incomplete',ProductOrderListViewSet,basename='order/product-incomplete')
router.register(r'schedules/product-incomplete',DeliveryScheduleListViewSet,basename='schedules/product-incomplete')
router.register(r'products-subcont',ProductListSubcontReadOnlyViewSet,basename='products-subcont')
router.register(r'deliveries/customer',DeliveryNoteCustomerReadOnlyViewSet,basename='deliveries/customer')
router.register(r'deliveries/customer-management',DeliveryNoteCustomerManagementViewSet,basename='deliveries/customer-management')
router.register(r'deliveries/products-shipped/customer',ProductDeliverManagementViewSet,basename='deliveries/products-shipped/customer')
router.register(r'vehicle',VehicleViewSet,basename='vehicle')
router.register(r'vehicle-management',VehicleManagementViewSet,basename='vehicle-management') 
router.register(r'driver',DriverViewSet,basename='driver')
router.register(r'driver-management',DriverManagementViewSet,basename='driver-management') 
router.register(r'deliveries/subcont',DeliveryNoteSubcontReadOnlyViewSet,basename='deliveries/subcont')
router.register(r'deliveries/subcont-management',DeliveryNoteSubcontManagementViewSet,basename='deliveries/subcont-management')
router.register(r'deliveries/products-shipped/subcont',ProductDeliverySubcontManagementViewSet,basename='deliveries/products-shipped/subcont')


router.register(r'product-delivery-subcont',ProductDeliverSubcontReadOnlyViewSet,basename='product-subcont')
router.register(r'receipt-subcont-schedule-management',ReceiptSubcontScheduleManagementViewSet,basename='receipt-subcont-schedule-management')
router.register(r'production-report',ProductionReportReadOnlyViewSet,basename='production-report')
router.register(r'production-report-management',ProductionReportManagementViewSet,basename='production-report-management')
router.register(r'production-priority',ProductionPriorityViewSet,basename='production-priority')
router.register(r'production-list',ProductionListViewSet,basename='production-list')
router.register(r'machine',MachineViewSet,basename='machine') 
router.register(r'machine-management',MachineManagementViewSet,basename='machine-management')
router.register(r'operator',OperatorViewSet,basename='operator')
router.register(r'operator-management',OperatorManagementViewSet,basename='operator-management') 


router.register(r'list-product-in-order',ProductOrderedViewSet,basename='list-product-in-order')
router.register(r'list-material-in-order',MaterialOrderedViewSet,basename='list-material-in-order')
router.register(r'monthly-production-report',MonthlyProductionReportViewSet,basename='monthly-production-report')




# router.register(r'requirement-product',RequirementProductViewSet,basename='requirement-product')
# router.register(r'requirement-material',RequirementMaterialViewSet,basename='requirement-material')
# router.register(r'material',MaterialViewSet,basename='material')
# router.register(r'uom-conversion-detail',UomConversionReadOnlyViewSet,basename='uom-conversion-detail')
# router.register(r'uom-conversion-management',UomConversionManagementViewSet,basename='uom-conversion-management')
# router.register(r'based-conversion-detail',BasedConversionMaterialReadOnlyViewSet,basename='based-conversion-detail')
# router.register(r'based-conversion-management',BasedConversionMaterialManagementViewSet,basename='based-conversion-management')
# router.register(r'report-conversion-detail',ReportConversionMaterialReadOnlyViewSet,basename='report-conversion-detail')
# router.register(r'report-conversion-management',ReportConversionMaterialManagementViewSet,basename='report-conversion-management')
# router.register(r'warehouse-subcont',WarehouseSubcontViewSet,basename='warehouse-subcont')


urlpatterns = [
    path('',include(router.urls)),  
]
