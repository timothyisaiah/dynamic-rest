from __future__ import absolute_import

from rest_framework.serializers import CharField
from .base import DynamicField


class DynamicCharField(
    CharField,
    DynamicField
):
    pass


class DynamicTextField(
    DynamicCharField
):
    def __init__(self, *args, **kwargs):
        if 'long' not in kwargs:
            kwargs['long'] = True
        super(DynamicTextField, self).__init__(*args, **kwargs)
