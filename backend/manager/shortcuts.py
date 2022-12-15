from rest_framework.serializers import ValidationError
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

def invalid(massage='delete failed due to data integrity') -> None:
    raise ValidationError(_(massage))


def get_error_message(module_name:str):
    '''
    return an error message 
    '''
    return f'access to manage {module_name} denied'

def get_default_password() ->str:
    '''
    return default password for user, when user is created, and when reset password of users
    '''
    return make_password('gandingtoolsindo')

filter_helper_app_label = {
        'auth':'plant-manager',
        'ppic':'ppic',
        'purchasing':'purchasing',
        'marketing':'marketing'
    }

def get_key(val):
    for key, value in filter_helper_app_label.items():
        if val == value:
            return key

    return "key doesn't exist"