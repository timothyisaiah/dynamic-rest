from __future__ import absolute_import

from rest_framework.serializers import DecimalField
from dynamic_rest.utils import money_format
from .base import DynamicField


class DynamicMoneyField(
    DecimalField,
    DynamicField
):
    def __init__(self, *args, **kwargs):
        if len(args) != 2:
            args = [24, 2]  # max_digits, decimal_places

        currency = kwargs.pop('currency', None)
        self.currency = currency
        return super(
            DynamicMoneyField,
            self,
        ).__init__(*args, **kwargs)

    def admin_get_icon(self, instance, value):
        return 'cash-usd'

    def prepare_value(self, instance):
        value = super(DynamicMoneyField, self).prepare_value(
            instance
        )
        value = money_format(
            value,
        )
        return value
