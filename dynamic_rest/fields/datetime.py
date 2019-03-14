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

    def to_representation(self, value):
        try:
            return super(
                DynamicDateTimeField,
                self
            ).to_representation(value)
        except ValueError as e:
            if '>= 1900' in str(e):
                # strftime cant handle dates before 1900
                return value.isoformat()

    def prepare_value(self, instance):
        value = super(DynamicDateTimeField, self).prepare_value(
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
