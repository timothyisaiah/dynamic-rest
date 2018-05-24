from __future__ import absolute_import

import arrow

from rest_framework.serializers import DateField
from dynamic_rest.conf import settings
from .base import DynamicField


class DynamicDateField(
    DateField,
    DynamicField
):
    ADMIN_FORMAT = settings.ADMIN_DATE_FORMAT

    def admin_get_icon(self, instance, value):
        return 'calendar'

    def prepare_value(self, instance):
        value = super(DynamicDateField, self).prepare_value(
            instance
        )
        if value:
            timezone = getattr(instance, 'timezone', None)
            value = arrow.get(value)
            if timezone:
                value = value.to(timezone)
            return value.format(self.ADMIN_FORMAT)
        else:
            return None
