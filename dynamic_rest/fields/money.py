from __future__ import absolute_import

from dynamic_rest.utils import money_format
from .model import DynamicDecimalField, DynamicIntegerField


class WithMoney(object):
    def admin_render_value(self, value):
        return money_format(value)


class DynamicMoneyField(
    DynamicDecimalField,
    WithMoney
):
    def __init__(self, *args, **kwargs):
        if len(args) != 2:
            args = [24, 2]  # max_digits, decimal_places

        currency = kwargs.pop('currency', None)
        self.currency = currency
        self.display_currency = kwargs.pop('display_currency', False)
        return super(
            DynamicMoneyField,
            self,
        ).__init__(*args, **kwargs)

    def to_representation(self, data):
        currency = None
        if hasattr(data, 'amount') and hasattr(data, 'currency'):
            data = data.amount
            currency = data.currency
        else:
            currency = self.currency

        base = super(DynamicMoneyField, self).to_representation(data)
        return f'{base} {currency}' if self.display_currency else base


class DynamicMoneyIntegerField(
    DynamicIntegerField,
    WithMoney
):
    pass
