from .base import DynamicField
from rest_framework.serializers import ChoiceField
from dynamic_rest.meta import Meta


class DynamicChoiceField(
    DynamicField,
    ChoiceField,
):
    def admin_get_icon(self, instance, value):
        return 'format-list-bulleted'

    def prepare_value(self, instance):
        model = self.parent_model
        source = self.source or self.field_name
        choices = Meta(model).get_field(source).choices
        value = getattr(instance, source)
        choice = dict(choices).get(value)
        return choice
