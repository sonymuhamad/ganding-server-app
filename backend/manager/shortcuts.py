from rest_framework.serializers import ValidationError

def invalid(massage='delete failed due to data integrity') -> None:
    raise ValidationError(massage)


def get_error_message(module_name:str):
    '''
    return an error message 
    '''
    return f'access to manage {module_name} denied'