from oauth2_provider.models import AccessToken
from datetime import datetime
import requests
from django.db import connection, reset_queries
import time
import functools

from django.contrib.auth.models import User,Group,update_last_login
from django.contrib.auth.hashers import check_password
from rest_framework import response,status,permissions
from rest_framework.viewsets import ModelViewSet

from marketing.models import SalesOrder

from .serializer import UserActivitySerializer, UserSerializer,UserManagementSerializer,ReportMrpSerializer,ReportSalesOrderSerializer
from .forms import RegisterForm
from .models import UserActivity
from ppic.models import MaterialRequirementPlanning

CLIENT_ID = '9IwGfEqtmqoIFcFSGz2C1kcX8zNmCVFczPNy0vgk'
CLIENT_SECRET = 'PlPFwPLscJ6b4c71UUCc0CebfEZf89CJCQqHSWOA3IolreLNfSfjr8NZqCbPfqmQjacCbr30wmvIUIIrUFSYExxKsoSYcgi4B8L65aGMjsATaoPCL0PRD28oq1DtPUYs'
URL = 'http://127.0.0.1:8000/o/token/'

def queryDebug(func):

    @functools.wraps(func)
    def inner_func(*args, **kwargs):

        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.2f}s")

        return result

    return inner_func


def deleteExpiredToken(function):
    def inner_func(*args,**kwargs):
        AccessToken.objects.filter(expires__lt=datetime.now()).delete()
        
        return function(*args,**kwargs)

    return inner_func 

class AuthViewSet(ModelViewSet):
    
    # class view for authentication / endpoints for authentication
    
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny] 
    user = None
    password = None

    def username_check(self,username):
        user = User.objects.filter(username=username).first()
        self.user = user
        return user

    def password_check(self,password):
        self.password = password
        return check_password(password,self.user.password)
    
    def token_check(self):
        access = self.user.oauth2_provider_accesstoken.first()
        data = {
            'grant_type':'password',
            'username':self.user.username,
            'password':self.password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET,
        }

        if access:
            return
        r = requests.post(URL,data)
        return

    @deleteExpiredToken
    def auth(self,request):
        if self.username_check(request.data['username']):
            
            if self.password_check(request.data['password']):
                self.token_check()
                serializer = UserSerializer(self.user)
                update_last_login('User',self.user)
                return response.Response(serializer.data,status=status.HTTP_200_OK) 
            return response.Response({'error':{'password':'invalid password'}},status=status.HTTP_400_BAD_REQUEST )

        return response.Response({'error':{'username':'invalid username'}},status=status.HTTP_400_BAD_REQUEST )



class UserViewSet(ModelViewSet):
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.prefetch_related('groups').all()

    def create(self, request, *args, **kwargs):

        data = {
            'username':request.data['username'],
            'email':request.data['email'],
            'password1':'gandingtoolsindo',
            'password2':'gandingtoolsindo',
            'group':request.data['group']
        }

        form = RegisterForm(data)

        if form.is_valid():
            respons = form.save()
            return response.Response(respons,status=status.HTTP_201_CREATED)
        return response.Response({'error':form.errors},status=status.HTTP_400_BAD_REQUEST)


class UserActivityViewSet(ModelViewSet):
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.AllowAny]
    queryset = UserActivity.objects.all()


class ReportMrpViewSet(ModelViewSet):
    serializer_class = ReportMrpSerializer
    permission_classes = [permissions.AllowAny]
    queryset = MaterialRequirementPlanning.objects.all()

class ReportSalesOrderViewSet(ModelViewSet):
    serializer_class = ReportSalesOrderSerializer
    permission_classes = [permissions.AllowAny]
    queryset = SalesOrder.objects.all()



