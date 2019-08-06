# flake8: noqa
from __future__ import absolute_import

try:
    from django.urls import (
        NoReverseMatch,
        get_script_prefix,
        reverse,
        resolve
    )
except ImportError:
    from django.core.urlresolvers import (  # Will be removed in Django 2.0
        NoReverseMatch,
        get_script_prefix,
        reverse,
        resolve
    )


def replace_methodname(format_string, methodname):
    """
    Partially format a format_string, swapping out any
    '{methodname}' or '{methodnamehyphen}' components.
    """
    methodnamehyphen = methodname.replace('_', '-')
    ret = format_string
    ret = ret.replace('{methodname}', methodname)
    ret = ret.replace('{methodnamehyphen}', methodnamehyphen)
    return ret
