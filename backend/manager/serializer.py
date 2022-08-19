from rest_framework.serializers import ModelSerializer
from .models import UserActivity
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User,Group,update_last_login
from django.contrib.auth.hashers import check_password

class UserActivitySerializer(ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['user','activity','descriptions']

class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']

class AccessTokenSerializer(ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ['token','expires','scope','created']

class UserManagementSerializer(ModelSerializer):
    groups = GroupSerializer(many=True)
    
    class Meta:
        model = User
        fields = ['username','last_login','email','groups'] 

    def create(self,validated_data):
        validated_data['password'] = 'gandingtoolsindomajubersama' #default password
        group = validated_data.pop('groups')

        newUser = User.objects.create(**validated_data)
        newUser.groups.add(group)

        return newUser


class UserSerializer(ModelSerializer):
    oauth2_provider_accesstoken = AccessTokenSerializer(many=True)
    groups = GroupSerializer(many=True)
    
    class Meta:
        model = User
        fields = ['last_login','username','email','oauth2_provider_accesstoken','groups']


    def get_auth(self,username,password):
        user = User.objects.filter(username=username).first()
        if user:
            pass
        return 

class AuthSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['username','password']

    def auth(self,validated_data) -> bool:
        username = validated_data.pop('username')
        user = User.objects.filter(username=username).first()
        
        if user is not None:
            password = validated_data.pop('password')

            if check_password(password,user.password):
                update_last_login('User',user)
                return True

        return False





