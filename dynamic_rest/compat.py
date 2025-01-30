# flake8: noqa
from __future__ import absolute_import
from django.conf.urls import include
import re

try:
    from django.conf.urls import url
except ImportError:
    from django.urls import path, re_path
    def is_simple_path(x):
        return re.match('^[.a-zA-Z_/]*$', x)

    def url(p, *args, **kwargs):
        fn = path if is_simple_path(p) else re_path
        return fn(p, *args, **kwargs)

try:
    from django.urls import NoReverseMatch, get_script_prefix, reverse, resolve
except ImportError:
    from django.core.urlresolvers import (  # Will be removed in Django 2.0
        NoReverseMatch,
        get_script_prefix,
        reverse,
        resolve,
    )


def replace_methodname(format_string, methodname):
    """
    Partially format a format_string, swapping out any
    '{methodname}' or '{methodnamehyphen}' components.
    """
    methodnamehyphen = methodname.replace("_", "-")
    ret = format_string
    ret = ret.replace("{methodname}", methodname)
    ret = ret.replace("{methodnamehyphen}", methodnamehyphen)
    return ret
