from functools import wraps
import datetime
from decimal import Decimal

FALSEY_STRINGS = (
    '0',
    'false',
    '',
)


def is_truthy(x):
    if isinstance(x, str):
        return x.lower() not in FALSEY_STRINGS
    return bool(x)


ONE_THOUSAND = Decimal('1000.00')
ONE_MILLION = Decimal('1000000.00')
ONE_BILLION = Decimal('1000000000.00')


def money_format(number):
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
    if isinstance(by, str):
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


def get(path, context):
    """Resolve a value given a path and a deeply-nested object

    Arguments:
        path: a dot-separated string
        context: any object, list, dictionary,
            or single-argument callable

    Returns:
        value at the end of the path, or None
    """
    parts = path.split(".")
    for part in parts:
        if context is None:
            break
        if callable(context):
            # try to "call" into the context
            try:
                try:
                    # 1. assume it is a method that takes no arguments
                    # and returns a nested object
                    context = context()
                except TypeError:
                    # 2. assume its a method that takes the next part
                    # as the argument
                    context = context(part)
                    continue
            except Exception:
                # fallback: assume this is a special object
                # that we should not call into
                # e.g. a django ManyRelatedManager
                pass

        if isinstance(context, dict):
            context = context.get(part, None)
        elif isinstance(context, list):
            # throws ValueError if part is NaN
            part = int(part)
            try:
                context = context[part]
            except IndexError:
                context = None
                break
        else:
            context = getattr(context, part, None)
    if context and callable(context):
        # if the result is a callable,
        # try to resolve it
        context = context()
    return context


def urljoin(*args):
    if not args:
        return None
    url = args[0]
    i = 1
    while i < len(args):
        if not url.endswith('/'):
            url += '/'
        url += args[i]
    return url


def clean(data):
    if isinstance(data, list):
        return [clean(item) for item in data]
    if isinstance(data, dict):
        return {(str(key) if key is not None else ''): clean(value) for key, value in data.items()}
    if isinstance(data, datetime.datetime):
        return data.isoformat()
    if isinstance(data, (datetime.date, datetime.time, Decimal)):
        return str(data)
    return data
