"""This module contains custom DRF metadata classes."""
from collections import OrderedDict

from rest_framework.fields import empty
from rest_framework.metadata import SimpleMetadata
from rest_framework.serializers import ListSerializer, ModelSerializer

from dynamic_rest.fields import DynamicRelationField, DynamicJSONField, DynamicLinkField
from dynamic_rest.utils import urljoin


class DynamicMetadata(SimpleMetadata):
    """A subclass of SimpleMetadata.

    Adds `fields` and `features` to the metdata.
    """

    def determine_actions(self, request, view):
        """Prevent displaying action-specific details."""
        return None

    def determine_metadata(self, request, view):
        """Adds `fields` and `features` to the metadata response."""
        metadata = super(DynamicMetadata, self).determine_metadata(request, view)
        metadata['label'] = metadata['name']
        if hasattr(view, 'get_serializer'):
            metadata['type'] = 'resource'
            metadata['features'] = getattr(view, 'features', [])
            serializer = view.get_serializer(dynamic=False)
            metadata['section'] = serializer.get_section()
            if hasattr(serializer, 'get_name'):
                metadata['singular'] = serializer.get_name()
            if hasattr(serializer, 'get_plural_name'):
                metadata['name'] = serializer.get_plural_name()
            metadata['fields'] = self.get_serializer_info(serializer)
            metadata['icon'] = serializer.get_icon()
            metadata['style'] = serializer.get_style()
            metadata['section'] = serializer.get_section()
            metadata['description'] = serializer.get_description()
            metadata['sections'] = [
                section.serialize() for section in serializer.get_sections()
            ]
            metadata['id_field'] = serializer.get_pk_field()
            metadata['name_field'] = serializer.get_name_field()
            permissions = view.full_permissions
            metadata['permissions'] = permissions.serialize() if permissions else {}
            metadata['permissions']['fields'] = serializer.get_field_permissions()
            metadata['actions'] = [action.serialize() for action in view.actions]

        elif hasattr(view, '_router'):
            metadata['type'] = 'namespace'
            if request.GET.get('all') is not None:
                metadata['resources'] = {
                    name: self.determine_metadata(request, view)
                    for name, view in view._router.get_viewsets(request).items()
                }
            else:
                metadata['resources'] = view._router.get_viewsets(request).keys()

            metadata['url'] = view._router.base_url

        return metadata

    def get_field_info(self, field):
        """Adds to the metadata response."""
        field_info = OrderedDict()
        for out, internal in (
            ('default', 'default'),
            ('label', 'label'),
            ('description', 'help_text'),
            ('null', 'allow_null'),
            ('deferred', 'deferred'),
            ('depends', 'depends'),
            ('style', 'style')
        ):
            field_info[out] = getattr(field, internal, None)

        if field_info['deferred'] is None:
            field_info['deferred'] = False

        if not field_info['default'] and getattr(field, 'model_field', None) and field.model_field.default:
            field_info['default'] = field.model_field.default
        if field_info['default'] is empty:
            field_info['default'] = None
        if callable(field_info['default']):
            # stringify callable default
            field_info['default'] = f'.{field_info["default"]}'
        if hasattr(field, 'choices'):
            field_info['choices'] = [
                {"id": choice_name, "label": choice_value}
                for choice_name, choice_value in (
                    field.choices.items()
                    if hasattr(field.choices, 'items')
                    else field.choices
                )
            ]
        many = False
        base_field = field
        if isinstance(field, DynamicRelationField):
            field = field.serializer
        if isinstance(field, ListSerializer):
            field = field.child
            many = True

        if isinstance(field, ModelSerializer):
            type = 'many' if many else 'one'
            field_info['related'] = field.get_plural_name()
            field_info['filter'] = base_field.filter
        else:
            if getattr(field, 'chart', False):
                type = 'chart'
            elif isinstance(field, DynamicJSONField):
                type = 'object'
            elif isinstance(field, DynamicLinkField):
                type = 'iframe' if field.iframe else 'string'
            else:
                type = self.label_lookup[field]

        field_info['type'] = type
        field_info['filterable'] = base_field.source and base_field.source != '*'
        field_info['sortable'] = field_info['filterable'] or (
            getattr(base_field, 'sort_field', None) is not None
        )
        return field_info
