"""
Custom Django lookups for JSON field operations.

This module provides custom lookup classes that enable JSON field filtering
using PostgreSQL JSON operators and other JSON-specific operations.
"""

from django.db.models import Lookup, Transform
from django.db.models.functions import JSONObject
from django.db.models import JSONField
from django.contrib.postgres.fields import JSONField as PostgresJSONField


class HasKeyLookup(Lookup):
    """
    Custom lookup for checking if a JSON field has a specific key.
    
    Usage: Model.objects.filter(data__has_key='enquiry')
    """
    lookup_name = 'has_key'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s ? %s", [lhs, rhs]
    
    def get_prep_lookup(self):
        return self.rhs


class HasKeysLookup(Lookup):
    """
    Custom lookup for checking if a JSON field has all specified keys.
    
    Usage: Model.objects.filter(data__has_keys=['enquiry', 'status'])
    """
    lookup_name = 'has_keys'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        
        # Convert single string to array format for PostgreSQL
        if rhs_params and isinstance(rhs_params[0], str):
            # If it's a comma-separated string, split it
            if ',' in rhs_params[0]:
                keys = rhs_params[0].split(',')
            else:
                # Single key
                keys = [rhs_params[0]]
            
            # Format as PostgreSQL array
            array_str = '{' + ','.join(keys) + '}'
            return f"{lhs} ?& %s", [array_str]
        
        return "%s ?& %s", [lhs, rhs]
    
    def get_prep_lookup(self):
        return self.rhs


class HasAnyKeysLookup(Lookup):
    """
    Custom lookup for checking if a JSON field has any of the specified keys.
    
    Usage: Model.objects.filter(data__has_any_keys=['enquiry', 'status'])
    """
    lookup_name = 'has_any_keys'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        
        # Convert single string to array format for PostgreSQL
        if rhs_params and isinstance(rhs_params[0], str):
            # If it's a comma-separated string, split it
            if ',' in rhs_params[0]:
                keys = rhs_params[0].split(',')
            else:
                # Single key
                keys = [rhs_params[0]]
            
            # Format as PostgreSQL array
            array_str = '{' + ','.join(keys) + '}'
            return f"{lhs} ?| %s", [array_str]
        
        return "%s ?| %s", [lhs, rhs]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONLengthTransform(Transform):
    """
    Transform to get the length of a JSON field.
    
    Usage: Model.objects.filter(data__length__gt=3)
    """
    lookup_name = 'length'
    
    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "jsonb_array_length(%s)", [lhs]


class JSONIsEmptyLookup(Lookup):
    """
    Custom lookup for checking if a JSON field is empty.
    
    Usage: Model.objects.filter(data__is_empty=True)
    """
    lookup_name = 'is_empty'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        
        if self.rhs:
            sql = f"({lhs} IS NULL OR jsonb_typeof({lhs}) = 'null' OR (jsonb_typeof({lhs}) = 'array' AND jsonb_array_length({lhs}) = 0) OR (jsonb_typeof({lhs}) = 'object' AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys({lhs}))))"
            return sql, []
        else:
            sql = f"({lhs} IS NOT NULL AND jsonb_typeof({lhs}) != 'null' AND NOT ((jsonb_typeof({lhs}) = 'array' AND jsonb_array_length({lhs}) = 0) OR (jsonb_typeof({lhs}) = 'object' AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys({lhs})))))"
            return sql, []
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathExistsLookup(Lookup):
    """
    Custom lookup for checking if a JSON path exists.
    
    Usage: Model.objects.filter(data__path_exists='enquiry.status')
    """
    lookup_name = 'path_exists'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params        
        
        # Convert dot notation to JSONPath format
        # e.g., 'enquiry.status' becomes '$.enquiry.status'
        path = rhs_params[0]
       
        if not path.startswith('$'):
            jsonpath_expr = f"$.{path}"
        else:
            jsonpath_expr = path
            
        # Use jsonb_path_exists to check if the path exists and has a value       
        sql = f"jsonb_path_exists({lhs}, '{jsonpath_expr}')"
        
        return sql, []
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathEqLookup(Lookup):
    """
    Custom lookup for checking if a JSON path equals a value.
    
    Usage: Model.objects.filter(data__path_eq='enquiry.status:active')
    """
    lookup_name = 'path_eq'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s) = %s", [lhs, json_path, value]
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s) = %s", [lhs, json_path, rhs_params[0]]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathGtLookup(Lookup):
    """
    Custom lookup for checking if a JSON path is greater than a value.
    
    Usage: Model.objects.filter(data__path_gt='enquiry.priority:3')
    """
    lookup_name = 'path_gt'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s)::numeric > %s", [lhs, json_path, value]
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s)::numeric > %s", [lhs, json_path, rhs_params[0]]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathGteLookup(Lookup):
    """
    Custom lookup for checking if a JSON path is greater than or equal to a value.
    
    Usage: Model.objects.filter(data__path_gte='enquiry.priority:3')
    """
    lookup_name = 'path_gte'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s)::numeric >= %s", [lhs, json_path, value]
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s)::numeric >= %s", [lhs, json_path, rhs_params[0]]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathLtLookup(Lookup):
    """
    Custom lookup for checking if a JSON path is less than a value.
    
    Usage: Model.objects.filter(data__path_lt='enquiry.priority:3')
    """
    lookup_name = 'path_lt'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s)::numeric < %s", [lhs, json_path, value]
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s)::numeric < %s", [lhs, json_path, rhs_params[0]]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathLteLookup(Lookup):
    """
    Custom lookup for checking if a JSON path is less than or equal to a value.
    
    Usage: Model.objects.filter(data__path_lte='enquiry.priority:3')
    """
    lookup_name = 'path_lte'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s)::numeric <= %s", [lhs, json_path, value]
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s)::numeric <= %s", [lhs, json_path, rhs_params[0]]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathContainsLookup(Lookup):
    """
    Custom lookup for checking if a JSON path contains a value.
    
    Usage: Model.objects.filter(data__path_contains='enquiry.tags:important')
    """
    lookup_name = 'path_contains'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s) LIKE %s", [lhs, json_path, f'%{value}%']
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s) LIKE %s", [lhs, json_path, f'%{rhs_params[0]}%']
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathIcontainsLookup(Lookup):
    """
    Custom lookup for case-insensitive contains on a JSON path.
    
    Usage: Model.objects.filter(data__path_icontains='enquiry.tags:important')
    """
    lookup_name = 'path_icontains'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "LOWER(%s #>> %s) LIKE %s", [lhs, json_path, f'%{value.lower()}%']
        json_path = "{" + rhs_params[0] + "}"
        return "LOWER(%s #>> %s) LIKE %s", [lhs, json_path, f'%{rhs_params[0].lower()}%']
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathInLookup(Lookup):
    """
    Custom lookup for checking if a JSON path value is in a list.
    
    Usage: Model.objects.filter(data__path_in='enquiry.status:active,pending')
    """
    lookup_name = 'path_in'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the path and values by ':'
        if ':' in rhs_params[0]:
            path, values = rhs_params[0].split(':', 1)
            value_list = values.split(',')
            placeholders = ','.join(['%s'] * len(value_list))
            json_path = "{" + path + "}"
            return "(%s #>> %s) IN (%s)", [lhs, json_path, placeholders] + value_list
        json_path = "{" + rhs_params[0] + "}"
        return "(%s #>> %s) IN (%s)", [lhs, json_path, rhs_params[0]]
    
    def get_prep_lookup(self):
        return self.rhs


class JSONArrayContainsLookup(Lookup):
    """
    Custom lookup for checking if a JSON array contains a value.
    
    Usage: Model.objects.filter(data__array_contains='tags:important')
    """
    lookup_name = 'array_contains'
    
    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        # Split the array path and value by ':'
        if ':' in rhs_params[0]:
            path, value = rhs_params[0].split(':', 1)
            json_path = "{" + path + "}"
            return "(%s #>> %s)::jsonb @> %s::jsonb", [lhs, json_path, f'["{value}"]']
        return "(%s)::jsonb @> %s::jsonb", [lhs, f'["{rhs_params[0]}"]']
    
    def get_prep_lookup(self):
        return self.rhs


class JSONArrayLengthTransform(Transform):
    """
    Transform to get the length of a JSON array.
    
    Usage: Model.objects.filter(data__array_length__gt=3)
    """
    lookup_name = 'array_length'
    
    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "jsonb_array_length(%s)", [lhs]


# Register the custom lookups with Django
JSONField.register_lookup(HasKeyLookup)
JSONField.register_lookup(HasKeysLookup)
JSONField.register_lookup(HasAnyKeysLookup)
JSONField.register_lookup(JSONIsEmptyLookup)
JSONField.register_lookup(JSONPathExistsLookup)
JSONField.register_lookup(JSONPathEqLookup)
JSONField.register_lookup(JSONPathGtLookup)
JSONField.register_lookup(JSONPathGteLookup)
JSONField.register_lookup(JSONPathLtLookup)
JSONField.register_lookup(JSONPathLteLookup)
JSONField.register_lookup(JSONPathContainsLookup)
JSONField.register_lookup(JSONPathIcontainsLookup)
JSONField.register_lookup(JSONPathInLookup)
JSONField.register_lookup(JSONArrayContainsLookup)

# Register transforms
JSONField.register_lookup(JSONLengthTransform)
JSONField.register_lookup(JSONArrayLengthTransform)

# Also register with PostgresJSONField for backward compatibility
if hasattr(PostgresJSONField, 'register_lookup'):
    PostgresJSONField.register_lookup(HasKeyLookup)
    PostgresJSONField.register_lookup(HasKeysLookup)
    PostgresJSONField.register_lookup(HasAnyKeysLookup)
    PostgresJSONField.register_lookup(JSONIsEmptyLookup)
    PostgresJSONField.register_lookup(JSONPathExistsLookup)
    PostgresJSONField.register_lookup(JSONPathEqLookup)
    PostgresJSONField.register_lookup(JSONPathGtLookup)
    PostgresJSONField.register_lookup(JSONPathGteLookup)
    PostgresJSONField.register_lookup(JSONPathLtLookup)
    PostgresJSONField.register_lookup(JSONPathLteLookup)
    PostgresJSONField.register_lookup(JSONPathContainsLookup)
    PostgresJSONField.register_lookup(JSONPathIcontainsLookup)
    PostgresJSONField.register_lookup(JSONPathInLookup)
    PostgresJSONField.register_lookup(JSONArrayContainsLookup)
    PostgresJSONField.register_lookup(JSONLengthTransform)
    PostgresJSONField.register_lookup(JSONArrayLengthTransform)
