from .base import DynamicField
from rest_framework.serializers import ChoiceField
from dynamic_rest.meta import Meta


class DynamicChoiceField(
    DynamicField,
    ChoiceField,
):
    def __init__(self, *args, **kwargs):
        self.controls = kwargs.pop('controls', {})
        super(DynamicChoiceField, self).__init__(*args, **kwargs)

    def prepare_value(self, instance):
        model = self.parent_model
        source = self.source or self.field_name
        choices = Meta(model).get_field(source).choices
        value = getattr(instance, source)
        choice = dict(choices).get(value)
        return choice
