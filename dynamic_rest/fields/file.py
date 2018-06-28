from .base import DynamicField
from rest_framework.serializers import FileField
from dynamic_rest.conf import settings

IMAGE_TYPES = {
    'jpeg',
    'jpg',
    'png',
    'gif',
}


class DynamicFileField(
        DynamicField,
        FileField,
):
    def admin_render(self, instance=None, value=None):
        ext = (value.name or '').lower().split('.')
        ext = ext[-1] if ext else ''
        url = value.url
        name = str(value)

        icon = '<span class="{0} {0}-download"></span>'.format(
            settings.ADMIN_ICON_PACK)
        if ext == 'pdf':
            display = '%s<embed src="%s" width=250 height=250 alt="%s">' % (
                icon, url, name)
        elif ext in IMAGE_TYPES:
            display = '<img %s style="%s" src="%s" alt="%s">' % (
                'width=250 height=250', 'object-fit:contain', url, name)
        else:
            display = '{0}{1}'.format(icon, name)

        return '<a target="_blank" href="%s">%s</a>' % (url, display)

    def prepare_value(self, instance):
        source = self.source or self.field_name
        value = getattr(instance, source, None)
        return value
