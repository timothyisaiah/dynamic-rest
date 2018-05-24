from __future__ import absolute_import

import arrow

from rest_framework.serializers import DateTimeField
from dynamic_rest.conf import settings
from .base import DynamicField


class DynamicDateTimeField(
    DateTimeField,
    DynamicField
):
    ADMIN_FORMAT = settings.ADMIN_DATETIME_FORMAT

    def admin_get_icon(self, instance, value):
        return 'calendar-clock'

    def prepare_value(self, instance):
        value = super(DynamicDateTimeField, self).prepare_value(
            instance
        )
        timezone = getattr(instance, 'timezone', None)
        value = arrow.get(value)
        if timezone:
            value = value.to(timezone)
        return value.format(self.ADMIN_FORMAT)
