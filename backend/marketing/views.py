from ast import arg
from rest_framework.viewsets import ModelViewSet
from .serializer import CustomerSerializer,SalesOrderManagementSerializer,SalesOrderSerializer,ProductOrderManagementSerializer
from .models import Customer, SalesOrder
from ppic.models import Product
from rest_framework import response,status,permissions
from django.db.models import Prefetch

class CustomerViewset(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        tes = self.integrity_check(kwargs)

        if not tes:
            return super().destroy(request, *args, **kwargs)        
        return response.Response({'error':'there is still an order from this customer'},status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def integrity_check(self,data):
        id = data['pk']
        customer = Customer.objects.get(id=id)
        salesorder = SalesOrder.objects.filter(done=0,customer=customer).first()
        return salesorder

class SalesOrderViewSet(ModelViewSet):
    serializer_class = SalesOrderManagementSerializer
    queryset = SalesOrder.objects.all()
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        seriz = SalesOrderManagementSerializer(data=request.data)
        
        if seriz.is_valid():
            seriz.save()
            return response.Response({'data':seriz.data},status=status.HTTP_201_CREATED)
        else:
            print(seriz.errors)
            return response.Response(seriz.errors,status=status.HTTP_400_BAD_REQUEST)

         







