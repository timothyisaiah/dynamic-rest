from functools import wraps
from decimal import Decimal
from django.utils.six import string_types

FALSEY_STRINGS = (
    '0',
    'false',
    '',
)


def is_truthy(x):
    if isinstance(x, string_types):
        return x.lower() not in FALSEY_STRINGS
    return bool(x)


ONE_THOUSAND = Decimal('1000.00')
ONE_MILLION = Decimal('1000000.00')
ONE_BILLION = Decimal('1000000000.00')


def money_format(
    number
):
    if not number:
        return '0'
    number = Decimal(number)
    ext = ''
    if number >= ONE_BILLION:
        number = '%f' % (number / ONE_BILLION)
        ext = 'B'
    elif number >= ONE_MILLION:
        number = '%f' % (number / ONE_MILLION)
        ext = 'M'
    elif number >= ONE_THOUSAND:
        number = '%f' % (number / ONE_THOUSAND)
        ext = 'K'
    else:
        number = '%f' % number
    if '.' in number:
        number = number.strip('0').strip('.')
    return '%s%s' % (number, ext)


def memoize(getter, by):
    store = {}
    if isinstance(by, string_types):
        key_fn = lambda x: getattr(x, by)
    else:
        key_fn = by

    @wraps(getter)
    def inner(instance, *args, **kwargs):
        key = key_fn(instance)
        if key in store:
            return store[key]
        store[key] = getter(instance)
        return store[key]

    return inner
