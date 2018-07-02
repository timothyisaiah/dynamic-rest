from __future__ import absolute_import

from rest_framework.serializers import DecimalField, IntegerField
from dynamic_rest.utils import money_format
from .base import DynamicField


class DynamicMoneyFieldBase(
    DynamicField
):
    def admin_get_icon(self, instance, value):
        return 'cash-usd'

    def admin_render_value(self, value):
        return money_format(value)


class DynamicMoneyField(
    DecimalField,
    DynamicMoneyFieldBase
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


class DynamicMoneyIntegerField(
    IntegerField,
    DynamicMoneyFieldBase
):
    pass
