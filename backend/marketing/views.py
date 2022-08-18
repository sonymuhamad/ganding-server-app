from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializer import CustomerSerializer
from .models import Customer
from ppic.models import Product
from rest_framework import response,status,permissions

class CustomerViewset(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = Customer.objects.prefetch_related('ppic_product_related').all()

        data = self.serializer_class(queryset,many=True)
        
        return response.Response(data.data,status=status.HTTP_200_OK)

