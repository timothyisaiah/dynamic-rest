from rest_framework.serializers import CharField
from .base import DynamicField


class DynamicPasswordField(
    CharField,
    DynamicField
):
    pass
