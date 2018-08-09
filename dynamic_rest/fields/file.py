import base64
import uuid
from .base import DynamicField
from rest_framework.serializers import FileField, ImageField
from rest_framework import exceptions
from django.core.files.base import ContentFile
from django.utils import six

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
        self.allow_base64 = kwargs.pop('allow_base64', True)
        super(DynamicFileFieldBase, self).__init__(**kwargs)

    def get_extension(self, name):
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

    def to_internal_value_base64(self, data):

        header, data = data.split(';base64,')
        try:
            decoded = base64.b64decode(data)
        except TypeError:
            self.fail('invalid')
        file_name = str(uuid.uuid4())[:12]
        ext = header.split('/')[-1]
        file_name += '.' + ext
        data = ContentFile(decoded, name=file_name)

        if isinstance(self, ImageField):
            if ext not in IMAGE_TYPES:
                return self.fail('invalid_image')

        return super(
            DynamicFileFieldBase,
            self
        ).to_internal_value(data)

    def to_internal_value(self, data):
        if isinstance(data, six.string_types):
            if self.allow_base64 and 'data:' in data and ';base64,' in data:
                return self.to_internal_value_base64(data)
            elif self.allow_remote:
                return self.to_internal_value_remote(data)
            else:
                raise exceptions.ValidationError()
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
