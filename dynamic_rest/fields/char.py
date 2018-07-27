from __future__ import absolute_import

from rest_framework.serializers import CharField
from .base import DynamicField


class DynamicCharField(
    CharField,
    DynamicField
):
    def __init__(self, *args, **kwargs):
        self.long = kwargs.pop('long', False)
        super(DynamicCharField, self).__init__(*args, **kwargs)


class DynamicTextField(
    DynamicCharField
):
    def __init__(self, *args, **kwargs):
        if 'long' not in kwargs:
            kwargs['long'] = True
        super(DynamicTextField, self).__init__(*args, **kwargs)
