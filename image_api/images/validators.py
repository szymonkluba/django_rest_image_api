from django.core.exceptions import ValidationError


def validate_duration_value(value):
    if 300 <= value <= 30000:
        return value
    raise ValidationError("Enter value between 300 and 30000")
