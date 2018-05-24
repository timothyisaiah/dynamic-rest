from __future__ import absolute_import

from rest_framework.serializers import CharField
from .base import DynamicField


class DynamicPhoneField(
    CharField,
    DynamicField
):
    def admin_get_icon(self, instance, value):
        return 'phone'

    def admin_get_url(self, instance, value):
        return 'tel:%s' % value
