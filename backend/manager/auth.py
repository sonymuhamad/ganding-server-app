from django.contrib.auth.models import User,update_last_login
from rest_framework import response,permissions,status
import requests
from oauth2_provider.models import AccessToken
from datetime import datetime
from .serializer import UserSerializer
from rest_framework.viewsets import ModelViewSet,CreateModelViewSet
from django.contrib.auth.hashers import check_password
from .shortcuts import invalid



CLIENT_ID = '9IwGfEqtmqoIFcFSGz2C1kcX8zNmCVFczPNy0vgk'
CLIENT_SECRET = 'PlPFwPLscJ6b4c71UUCc0CebfEZf89CJCQqHSWOA3IolreLNfSfjr8NZqCbPfqmQjacCbr30wmvIUIIrUFSYExxKsoSYcgi4B8L65aGMjsATaoPCL0PRD28oq1DtPUYs'
URL = 'http://127.0.0.1:8000/o/token/'


def deleteExpiredToken(function):
    def inner_func(*args,**kwargs):
        AccessToken.objects.filter(expires__lt=datetime.now()).delete()
        
        return function(*args,**kwargs)

    return inner_func 

class AuthViewSet(ModelViewSet):
    
    # class view for sign in or get authentication
    
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

    def groups_check(self):
        return self.user.groups.exists()

    @deleteExpiredToken
    def auth(self,request):
        if self.username_check(request.data['username']):
            
            if self.password_check(request.data['password']):
                self.token_check()
                
                if not self.groups_check():
                    return response.Response({'error':{'groups':"User doesn't have any division, please ask manager to granted some division"}},status=status.HTTP_400_BAD_REQUEST )

                serializer = UserSerializer(self.user)
                update_last_login('User',self.user)
                return response.Response(serializer.data,status=status.HTTP_200_OK) 
            return response.Response({'error':{'password':'invalid password'}},status=status.HTTP_400_BAD_REQUEST )

        return response.Response({'error':{'username':'invalid username'}},status=status.HTTP_400_BAD_REQUEST )

class LogoutViewSet(CreateModelViewSet):
    '''
    class for destroy authentication or sign out
    '''
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    @deleteExpiredToken
    def create(self,request):
        token = request.data['access_token']
        r = requests.post('http://127.0.0.1:8000/o/revoke_token/', data = {
            'token':token,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET,},)

        return response.Response({'revoke':'success','logout':'success'},status=status.HTTP_200_OK)
