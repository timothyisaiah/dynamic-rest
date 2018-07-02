from .base import DynamicField
from rest_framework.serializers import ChoiceField
from dynamic_rest.meta import Meta


class DynamicChoiceField(
    DynamicField,
    ChoiceField,
):
    def admin_render_value(self, value):
        model = self.parent_model
        source = self.source or self.field_name
        choices = Meta(model).get_field(source).choices
        choices = dict(choices).get(value, None)
        return choices
