from .base import DynamicField
from rest_framework.serializers import FileField, ImageField
from django.utils import six
from dynamic_rest.conf import settings

IMAGE_TYPES = {
    'jpeg',
    'jpg',
    'png',
    'gif',
    'bmp',
    'tiff',
    'webp',
    'ico',
    'eps'
}


class DynamicFileFieldBase(
    DynamicField
):
    def __init__(self, **kwargs):
        self.allow_remote = kwargs.pop('allow_remote', True)
        super(DynamicFileFieldBase, self).__init__(**kwargs)

    def admin_render(self, instance=None, value=None):
        ext = self.get_extension(value.name)
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

    def get_extension(name):
        if not name or '.' not in name:
            return ''
        return name.split('.')[-1].lower()

    def to_internal_value_remote(self, name):
        if not name:
            self.fail('no_name')

        field = self.model_field
        storage = field.storage
        if not storage.exists(name):
            self.fail('invalid')

        size = storage.size(name)
        name_length = len(name)

        if not self.allow_empty_file and not size:
            self.fail('empty')
        if self.max_length and name_length > self.max_length:
            self.fail(
                'max_length',
                max_length=self.max_length,
                length=name_length
            )

        if isinstance(self, ImageField):
            ext = self.get_extension(name)
            if ext not in IMAGE_TYPES:
                return self.fail('invalid_image')

        return name

    def to_internal_value(self, data):
        if isinstance(data, six.string_types) and self.allow_remote:
            return self.to_internal_value_remote(data)
        else:
            return super(DynamicFileFieldBase, self).to_internal_value(data)


class DynamicImageField(
    DynamicFileFieldBase,
    ImageField
):
    pass


class DynamicFileField(
    DynamicFileFieldBase,
    FileField
):
    pass
