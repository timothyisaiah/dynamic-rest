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
        return f"{lhs} ? {rhs}", params
    
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
        
        return f"{lhs} ?& {rhs}", params
    
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
        
        return f"{lhs} ?| {rhs}", params
    
    def get_prep_lookup(self):
        return self.rhs


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
            # Convert dot notation to PostgreSQL JSON path array
            path_elements = path.split('.')
            json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
            
            # Try to determine the type of the value
            try:
                # Try to convert to integer
                int_value = int(value)
                sql_template = f"({lhs} #>> %s::text[])::integer = %s::integer"
                final_params = [json_path, int_value]
            except ValueError:
                try:
                    # Try to convert to float
                    float_value = float(value)
                    sql_template = f"({lhs} #>> %s::text[])::float = %s::float"
                    final_params = [json_path, float_value]
                except ValueError:
                    # Treat as string/text
                    sql_template = f"({lhs} #>> %s::text[]) = %s::text"
                    final_params = [json_path, value]
            
            return sql_template, final_params
        
        # Handle case where no value is provided (just path)
        path_elements = rhs_params[0].split('.')
        json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
        sql_template = f"({lhs} #>> %s::text[]) IS NOT NULL"
        final_params = [json_path]
        return sql_template, final_params
    
    def get_prep_lookup(self):
        return self.rhs


class JSONPathContainsLookup(Lookup):
    """
    Custom lookup for case-insensitive contains on a JSON path.
    
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
            # Convert dot notation to PostgreSQL JSON path array
            path_elements = path.split('.')
            json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
            return f"LOWER({lhs} #>> %s::text[]) LIKE %s", [json_path, f'%{value.lower()}%']
        # Handle case where no value is provided (just path)
        path_elements = rhs_params[0].split('.')
        json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
        return f"LOWER({lhs} #>> %s::text[]) LIKE %s", [json_path, f'%{rhs_params[0].lower()}%']
    
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
        
        # Handle multiple path-value pairs separated by commas
        pairs = rhs_params[0].split(',')
        conditions = []
        all_params = []
        
        for pair in pairs:
            if ':' in pair:
                path, value = pair.split(':', 1)
                # Convert dot notation to PostgreSQL JSON path array
                path_elements = path.split('.')
                json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
                conditions.append(f"({lhs} #>> %s::text[]) = %s")
                all_params.extend([json_path, value])
            else:
                # Handle case where no value is provided (just path)
                path_elements = pair.split('.')
                json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
                conditions.append(f"({lhs} #>> %s::text[]) IS NOT NULL")
                all_params.append(json_path)
        
        if len(conditions) == 1:
            sql_template = conditions[0]
            final_params = all_params
        else:
            sql_template = " OR ".join(conditions)
            final_params = all_params
        
        return sql_template, final_params
    
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
            # Convert dot notation to PostgreSQL JSON path array
            path_elements = path.split('.')
            json_path = "{" + ",".join(f'"{element}"' for element in path_elements) + "}"
            return f"({lhs} #>> %s::text[])::jsonb @> %s::jsonb", [json_path, f'["{value}"]']
        return f"({lhs})::jsonb @> %s::jsonb", [f'["{rhs_params[0]}"]']
    
    def get_prep_lookup(self):
        return self.rhs


# Register the custom lookups with Django
JSONField.register_lookup(HasKeyLookup)
JSONField.register_lookup(HasKeysLookup)
JSONField.register_lookup(HasAnyKeysLookup)
JSONField.register_lookup(JSONIsEmptyLookup)
JSONField.register_lookup(JSONPathExistsLookup)
JSONField.register_lookup(JSONPathEqLookup)
JSONField.register_lookup(JSONPathContainsLookup)
JSONField.register_lookup(JSONPathInLookup)
JSONField.register_lookup(JSONArrayContainsLookup)

# Also register with PostgresJSONField for backward compatibility
if hasattr(PostgresJSONField, 'register_lookup'):
    PostgresJSONField.register_lookup(HasKeyLookup)
    PostgresJSONField.register_lookup(HasKeysLookup)
    PostgresJSONField.register_lookup(HasAnyKeysLookup)
    PostgresJSONField.register_lookup(JSONIsEmptyLookup)
    PostgresJSONField.register_lookup(JSONPathExistsLookup)
    PostgresJSONField.register_lookup(JSONPathEqLookup)
    PostgresJSONField.register_lookup(JSONPathContainsLookup)
    PostgresJSONField.register_lookup(JSONPathInLookup)
    PostgresJSONField.register_lookup(JSONArrayContainsLookup)