from oauth2_provider.models import AccessToken
from datetime import datetime
import requests
from django.db import connection, reset_queries
import time
import functools

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from rest_framework import response,status,permissions
from rest_framework.viewsets import ModelViewSet

from .serializer import UserSerializer,UserManagementSerializer

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
                return response.Response(serializer.data) 
            return response.Response({'error':{'password':'invalid password'}},status=status.HTTP_400_BAD_REQUEST )

        return response.Response({'error':{'username':'invalid username'}},status=status.HTTP_400_BAD_REQUEST )



class UserViewSet(ModelViewSet):
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.prefetch_related('groups').all()

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        
        return
