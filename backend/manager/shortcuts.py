from rest_framework.serializers import ValidationError

def invalid(massage='delete failed due to data integrity') -> None:
    raise ValidationError(massage)