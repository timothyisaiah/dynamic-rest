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

    def to_representation(self, value):
        try:
            return super(
                DynamicDateField,
                self
            ).to_representation(value)
        except ValueError as e:
            if '>= 1900' in str(e):
                # strftime cant handle dates before 1900
                return value.isoformat()

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
