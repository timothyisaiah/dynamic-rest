from .base import DynamicField
from rest_framework.serializers import FileField
from dynamic_rest.conf import settings


class DynamicFileField(
    DynamicField,
    FileField,
):
    def admin_render(self, instance=None, value=None):
        return '<a target="_blank" href="%s">%s%s</a>' % (
            value.url,
            '<span class="%s %s-download"></span>'.format(
                settings.ADMIN_ICON_PACK
            ),
            str(value)
        )

    def prepare_value(self, instance):
        source = self.source or self.field_name
        value = getattr(instance, source)
        return value
