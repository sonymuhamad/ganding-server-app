from rest_framework.serializers import ValidationError

def invalid(massage='delete failed due to data integrity || hapus data gagal') -> None:
    raise ValidationError(massage)