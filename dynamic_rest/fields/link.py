from __future__ import absolute_import

from rest_framework.serializers import CharField
from .base import DynamicField


class DynamicLinkField(
    CharField,
    DynamicField
):
    def __init__(self, **kwargs):
        self.iframe = kwargs.pop('iframe', False)
        return super(DynamicLinkField, self).__init__(**kwargs)
