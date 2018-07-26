from django.test import TestCase
from tests.serializers import LocationSerializer
from model_mommy import mommy
from rest_framework.exceptions import ValidationError
from tests.models import Location
from override_storage import override_storage
from override_storage.storage import LocMemStorage


class FileFieldTestCase(TestCase):
    @override_storage(storage=LocMemStorage())
    def test_field_internal_value(self):
        location = mommy.make(Location)
        serializer = LocationSerializer(
            instance=location
        )
        file_field = serializer.get_field('document')
        storage = file_field.model_field.storage

        def exists(name):
            return name == 'bar'

        def size(*args):
            return 1

        storage.exists = exists
        storage.size = size

        with self.assertRaises(ValidationError):
            file_field.to_internal_value('foo')

        self.assertEquals(
            file_field.to_internal_value('bar'),
            'bar'
        )
