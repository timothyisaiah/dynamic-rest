from __future__ import absolute_import
import inflection
import datetime
import re
import os
import json

from decimal import Decimal
from django.db.models.fields.files import FieldFile
from django.http.request import QueryDict
from urlparse import urlparse, urlunparse
from uuid import UUID
from django import template
from django.utils.safestring import mark_safe
from django.utils import six
from dynamic_rest.conf import settings
from dynamic_rest.renderers import DynamicHTMLFormRenderer
from rest_framework.fields import get_attribute

try:
    from rest_framework.templatetags.rest_framework import format_value
except:  # noqa
    def format_value(x):
        return x


register = template.Library()


@register.simple_tag
def get_image_url(field):
    # field = UI + DynamicRelationField

    instance = field.value

    if not instance:
        return None

    serializer = field.serializer
    if not serializer:
        return None

    image_field_name = serializer.get_image_field()

    if not image_field_name:
        return None

    image_field = serializer.get_field(image_field_name)

    if not image_field:
        return None

    image = getattr(
        instance,
        image_field.source or image_field_name,
        None
    )
    return getattr(image, 'url', None)


@register.simple_tag
def render_read_only_field(field, style):
    field._field.read_only = True
    renderer = style.get('renderer', DynamicHTMLFormRenderer())
    return renderer.render_field(field, style)


@register.filter
def help_text_format(txt):
    if not txt:
        return ''
    txt = txt.strip().replace('\n', '<br/>')
    txt = re.sub(r'\*([0-9A-Za-z ]+)\*', '<b>\\1</b>', txt)
    txt = re.sub(r'`([0-9A-Za-z ]+)`', '<code>\\1</code>', txt)
    return txt


@register.filter
def help_text_short_format(txt):
    if not txt:
        return ''
    txt = txt.strip()
    txt = txt.split('\n')[0]
    txt = re.sub(r'\*([0-9A-Za-z ]+)\*', '<b>\\1</b>', txt)
    txt = re.sub(r'`([0-9A-Za-z ]+)`', '<code>\\1</code>', txt)
    return txt


def _relation_to_json(field, value=None, many=None):
    serializer = field.serializer
    if many is None:
        many = field.many

    name_field_name = serializer.get_name_field()
    name_source = serializer.get_field(
        name_field_name
    ).source or name_field_name
    source_attrs = name_source.split('.')
    value = value or field.value

    if not (
        isinstance(value, list)
        and not isinstance(value, six.string_types)
        and not isinstance(value, UUID)
    ):
        value = [value]

    results = []
    model = serializer.get_model()
    for v in value:
        if v:
            if hasattr(v, 'instance'):
                instance = v.instance
            else:
                if v is None:
                    continue
                else:
                    if isinstance(v, model):
                        instance = v
                    else:
                        instance = model.objects.get(
                            pk=str(v)
                        )
            result = {
                'id': str(instance.pk),
                'name': get_attribute(instance, source_attrs)
            }
            results.append(result)

    if not many:
        # single value result
        results = results[0] if len(results) else None
    return mark_safe(json.dumps(results))


@register.simple_tag
def get_value_from_dict(d, key):
    return d.get(key, '')


@register.filter
def format_key(key):
    return key


@register.simple_tag
def drest_settings(key):
    return getattr(settings, key)


@register.filter
def to_json(value):
    return mark_safe(json.dumps(value))


@register.filter
def filter_to_json(filter):
    value = filter.value
    field = filter.field
    related_serializer = getattr(
        field,
        'serializer',
        None
    ) if field else None
    return _to_json(field, value, related_serializer, many=True)


@register.filter
def field_to_json(field):
    value = field.value
    related_serializer = getattr(
        field,
        'serializer',
        None
    )
    return _to_json(field, value, related_serializer)


def _to_json(field, value, related_serializer, many=None):
    if isinstance(value, FieldFile):
        try:
            value = value.url
        except ValueError:
            value = None
    elif isinstance(value, (
        Decimal,
        UUID,
        datetime.datetime,
        datetime.date,
        datetime.time
    )):
        value = str(value)

    if not related_serializer:
        return to_json(value)
    else:
        return _relation_to_json(field, many=many)


@register.filter
def admin_format_value(value):
    return format_value(value)


@register.simple_tag
def get_sections(serializer, instance=None, check=True):
    instance = instance or serializer.instance
    sections = serializer.get_sections(instance)
    if check:
        sections = [
            s for s in sections if s.should_render
        ]
    return sections


@register.simple_tag
def get_field_value(serializer, instance, key, idx=None):
    return serializer.get_field_value(key, instance)


@register.filter
def render_field_value(field):
    if hasattr(field, 'rendered_value'):
        value = field.rendered_value
    else:
        value = field
    return mark_safe(value)


@register.filter
def humanize(value):
    return inflection.humanize(value)


@register.simple_tag
def get_sort_query_value(field, sorted_field, sorted_ascending):
    if field != sorted_field:
        return field
    else:
        return '-%s' % field if sorted_ascending else field


@register.simple_tag
def replace_query_param(url, key, value):
    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    query_dict = QueryDict(query).copy()
    query_dict[key] = value
    query = query_dict.urlencode()
    return urlunparse((scheme, netloc, path, params, query, fragment))


@register.simple_tag
def render_filter(flt):
    return mark_safe(flt.render())


@register.filter
def get_related_url(serializer, related_name):
    instance = serializer.instance
    return os.path.join(
        serializer.get_url(instance.pk),
        related_name
    )
