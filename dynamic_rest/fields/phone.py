from __future__ import absolute_import

from rest_framework.serializers import CharField
from dynamic_rest.conf import settings
from .base import DynamicField


class DynamicPhoneField(
    CharField,
    DynamicField
):
    def admin_get_icon(self, instance, value):
        return 'phone'
