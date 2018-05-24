from __future__ import absolute_import

import json
from rest_framework.serializers import JSONField
from .base import DynamicField


class DynamicJSONField(
    JSONField,
    DynamicField
):
    def admin_render(self, instance, value=None):
        value = value or self.prepare_value(instance)
        return '''
            <span class="drest-json" data-json='%s'></span>
        ''' % json.dumps(value or {})
