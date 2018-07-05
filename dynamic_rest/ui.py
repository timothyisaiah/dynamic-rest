from random import randint
import json
import uuid

from django.utils.functional import cached_property
from django.utils import six
from decimal import Decimal
from django.template import loader
from rest_framework.compat import unicode_to_repr

from dynamic_rest.utils import is_truthy
from dynamic_rest import fields as dfields


def get_type_for(field):
    if isinstance(field, dfields.DynamicChoiceField):
        return "select"
    elif isinstance(field, dfields.DynamicIntegerField):
        return 'integer'
    elif isinstance(
        field, (
            dfields.DynamicBooleanField,
            dfields.DynamicNullBooleanField
        )
    ):
        return 'boolean'
    elif isinstance(field, dfields.DynamicDecimalField):
        return 'decimal'
    elif isinstance(field, dfields.DynamicDateField):
        return 'date'
    elif isinstance(field, dfields.DynamicDateTimeField):
        return 'datetime'
    elif isinstance(field, dfields.DynamicRelationField):
        return "relation"
    elif isinstance(field, dfields.DynamicListField):
        return "list"
    elif isinstance(field,
                    (dfields.DynamicFileField, dfields.DynamicImageField)):
        return "file"
    else:
        return "text"


class UIField(object):
    """
    A field object that also includes `.value` and `.error` properties
    as well as `.instance`.
    Returned when iterating over a serializer instance,
    providing an API similar to Django forms and form fields.
    """

    def __init__(self, field, value, errors, prefix='', instance=None,
                 id=None):
        self._field = field
        self._prefix = prefix
        rand = ''.join([str(randint(0, 9)) for _ in range(6)])
        self.id = id or rand
        self.value = value
        self.errors = errors
        self.instance = instance
        self.name = prefix + self.field_name
        self.type = get_type_for(self._field)
        self.is_null = value is None or value == ''
        self.is_empty = (not value and not (value == 0 or value is False))

    def __getattr__(self, attr_name):
        return getattr(self._field, attr_name)

    @property
    def _proxy_class(self):
        return self._field.__class__

    def __repr__(self):
        return unicode_to_repr(
            '<%s %s value=%s errors=%s instance=%s>' %
            (self.__class__.__name__, self._field.field_name, self.value,
             self.errors, self.instance))

    @cached_property
    def rendered_value(self):
        if callable(getattr(self._field, 'admin_render', None)):
            return self._field.admin_render(
                instance=self.instance,
                value=self.value
            )
        else:
            return

    @cached_property
    def should_render(self):
        field = self._field
        read_only = field.read_only

        model_field = getattr(field, 'model_field', None)
        if getattr(model_field, 'primary_key', None):
            return False

        request_method = field.parent.get_request_method().upper()

        if request_method == 'GET':
            if (
                field.write_only or (
                    getattr(field, 'hide', None) and
                    field.read_only and not getattr(field, 'create', None)
                    and self.is_empty
                )
            ):
                return False

        elif request_method in ('POST', 'PATCH', 'PUT'):
            if read_only:
                return False

        return True

    def as_form_field(self):
        value = '' if (self.value is None
                       or self.value is False) else self.value

        parent_name = self._field.parent.get_name()
        rand = ''.join([str(randint(0, 9)) for _ in range(6)])
        id = '%s-%s-%s' % (parent_name, self.name, rand)

        result = self.__class__(self._field, value, self.errors, self._prefix,
                                self.instance, id)
        return result


class UIJSONField(UIField):
    def as_form_field(self):
        value = self.value
        try:
            value = json.dumps(self.value, sort_keys=True, indent=4)
        except TypeError:
            pass

        parent_name = self._field.parent.get_name()
        rand = ''.join([str(randint(0, 9)) for _ in range(6)])
        id = '%s-%s-%s' % (parent_name, self.name, rand)
        result = self.__class__(self._field, value, self.errors, self._prefix,
                                self.instance, id)
        return result


class UISection(object):
    def __init__(self, name, fields, serializer, instance=None, main=False):
        self.serializer = serializer
        self.name = name
        self.fields = []
        self.instance = instance
        for field in fields:
            try:
                self.fields.append(serializer.get_field_value(field, instance))
            except KeyError:
                pass
        if len(self.fields) == 1:
            self.field = self.fields[0]
        else:
            self.field = None

        self.main = main

    @cached_property
    def should_render(self):
        return any([f.should_render for f in self.fields])


class UIFilter(object):
    base_template_path = 'dynamic_rest/filters'

    def __init__(self, name, options, serializer=None):
        """
        Arguments:
            name:       Filter name
            options:    A configuration object:
                        {
                            field:  An underlying field to bind to.
                            label:  The label to be displayed for this filter.
                            key:    A URL query parameter to map to.
                                    Will be inferred from `field` if not set
                            type:   A filter type, one of:
                                    "text", "integer", "decimal", "boolean",
                                    "date", "datetime", or "relation"
                        }
            serializer: A serializer object.
        """
        self.name = name
        self.options = options
        self.serializer = serializer
        # filter options
        self.field = None
        self.key = None
        self.type = None
        self.choices = None
        self.many = None
        self.help_text = None
        self.min = None
        self.max = None
        # resolve options
        self.resolve()

    def get_choices_for(self, field):
        choices = getattr(field, 'choices', None)
        if choices:
            return choices
        else:
            field = field.model_field
            if field and hasattr(field, 'choices'):
                return dict(field.choices)
            return {}

    def get_key_for(self, name):
        type = self.type
        if type in ("select", "relation", "boolean"):
            return 'filter{%s.in}' % name
        elif type in ("date", "datetime", "integer", "decimal"):
            return 'filter{%s.range}' % name
        elif type == 'text':
            return 'filter{%s.icontains}' % name
        else:
            return 'filter{%s}' % name

    def resolve(self):
        if isinstance(self.options, six.string_types):
            self.options = {'field': self.options}
        name = self.name
        field_name = self.options.get('field', None)
        key = self.options.get('key', None)
        type = self.options.get('type', None)
        choices = self.options.get('choices', None)
        help_text = self.options.get('help_text', None)
        self.label = self.options.get('label', (field_name
                                                or name).title().replace(
                                                    '_', ' '))
        self.many = self.options.get('many', True)
        if field_name:
            field = self.serializer.get_field(field_name)
            self.field = field
            self.type = get_type_for(field)
            self.key = self.get_key_for(field_name)
            self.choices = self.get_choices_for(field)
            self.help_text = getattr(field, 'help_text', None)

        if key:
            # override key
            self.key = key or None
        if type:
            # override type
            self.type = type
        if self.type == 'text':
            self.many = False
        if choices:
            self.choices = choices
        if help_text:
            self.help_text = help_text
        self.value = self.get_value()
        if self.field:
            self.field.value = self.value

    def render(self):
        template_name = '%s/%s.html' % (self.base_template_path, self.type)
        template = loader.get_template(template_name)
        context = {
            'serializer': self.serializer,
            'many': self.many,
            'min': self.min,
            'max': self.max,
            'field': self.field,
            'label': self.label,
            'name': self.name,
            'key': self.key,
            'choices': self.choices,
            'value': self.value,
            'id': str(uuid.uuid4())
        }
        return template.render(context)

    def get_value(self):
        key = self.key
        assert key is not None
        request = self.serializer.context.get('request')
        type = self.type
        many = self.many

        return_list = False
        if many or type == 'integer':
            return_list = True
            value = request.query_params.getlist(key)
        else:
            return_list = False
            value = [request.query_params.get(key)]

        result = []
        for v in value:
            if type == "boolean":
                if is_truthy(value):
                    v = "True"
                elif value is not None:
                    v = "False"
            elif type == "integer":
                v = str(int(v)) if v else None
            elif type == "decimal":
                v = str(Decimal(v)) if v else None
            else:
                v = str(v) if v else None
            result.append(v)

        return result if return_list else result[0]
