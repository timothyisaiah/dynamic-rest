"""This module contains custom DRF metadata classes."""
from collections import OrderedDict

from rest_framework.fields import empty
from rest_framework.metadata import SimpleMetadata
from rest_framework.serializers import ListSerializer, ModelSerializer

from dynamic_rest.fields import DynamicRelationField


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
        metadata['features'] = getattr(view, 'features', [])
        if hasattr(view, 'get_serializer'):
            serializer = view.get_serializer(dynamic=False)
            metadata['section'] = serializer.get_section()
            if hasattr(serializer, 'get_name'):
                metadata['singular'] = serializer.get_name()
            if hasattr(serializer, 'get_plural_name'):
                metadata['name'] = serializer.get_plural_name()
            metadata['fields'] = self.get_serializer_info(serializer)
            metadata['icon'] = serializer.get_icon()
            metadata['section'] = serializer.get_section()
            metadata['description'] = serializer.get_description()
            metadata['sections'] = [
                section.serialize() for section in serializer.get_sections()
            ]
            metadata['primary_key'] = serializer.get_pk_field()
            metadata['name_field'] = serializer.get_name_field()
            permissions = view.full_permissions
            metadata['permissions'] = permissions.serialize() if permissions else {}
            metadata['permissions']['fields'] = serializer.get_field_permissions()
            metadata['actions'] = [action.serialize() for action in view.actions]

        return metadata

    def get_field_info(self, field):
        """Adds `related_to` and `nullable` to the metadata response."""
        field_info = OrderedDict()
        for out, internal in (
            ('default', 'default'),
            ('label', 'label'),
            ('description', 'help_text'),
            ('null', 'allow_null'),
            ('deferred', 'deferred'),
            ('depends', 'depends'),
        ):
            field_info[out] = getattr(field, internal, None)

        if field_info['deferred'] is None:
            field_info['deferred'] = False

        if field_info['default'] is empty:
            field_info['default'] = None
        if callable(field_info['default']):
            # stringify callable default
            field_info['default'] = f'.{field_info["default"]}'
        if hasattr(field, 'choices'):
            field_info['choices'] = [
                {"id": choice_name, "label": choice_value}
                for choice_value, choice_name in (
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
            type = self.label_lookup[field]

        field_info['type'] = type
        field_info['filterable'] = base_field.source and base_field.source != '*'
        field_info['sortable'] = field_info['filterable'] or (
            getattr(base_field, 'sort_field', None) is not None
        )
        return field_info
