from .models import CustomVariable


def get_custom_variable(key):
    return (
        CustomVariable.objects.filter(key=key, enabled=True)
        .values_list("value", flat=True)
        .first()
    )
