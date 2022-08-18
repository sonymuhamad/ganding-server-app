from rest_framework.serializers import ModelSerializer
from .models import UserActivity

class UserActivitySerializer(ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['user','activity','descriptions']







