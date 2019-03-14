from __future__ import absolute_import

import json
from rest_framework.serializers import JSONField
from .base import DynamicField


class DynamicJSONField(
    JSONField,
    DynamicField
):
    def __init__(self, *args, **kwargs):
        if 'long' not in kwargs:
            kwargs['long'] = True

        self.chart = kwargs.pop('chart', False)
        super(DynamicJSONField, self).__init__(*args, **kwargs)

    def admin_render(self, instance, value=None):
        if self.chart:
            return super(DynamicJSONField, self).admin_render(
                instance, value=value
            )

        value = value or self.prepare_value(instance)
        return '''
            <span class="drest-json" data-json='%s'></span>
        ''' % json.dumps(value or {})
