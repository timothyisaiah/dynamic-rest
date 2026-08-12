"""Helpers for synthetic/ephemeral resources."""

import re

EPHEMERAL_FILTER_TYPE_OPERATORS = {
    "boolean": {"eq", "in", "isnull"},
    "date": {
        "day",
        "eq",
        "gt",
        "gte",
        "in",
        "isnull",
        "lt",
        "lte",
        "month",
        "range",
        "week_day",
        "year",
    },
    "datetime": {
        "day",
        "eq",
        "gt",
        "gte",
        "in",
        "isnull",
        "lt",
        "lte",
        "month",
        "range",
        "week_day",
        "year",
    },
    "decimal": {"eq", "gt", "gte", "in", "isnull", "lt", "lte", "range"},
    "float": {"eq", "gt", "gte", "in", "isnull", "lt", "lte", "range"},
    "integer": {"eq", "gt", "gte", "in", "isnull", "lt", "lte", "range"},
    "string": {
        "contains",
        "endswith",
        "eq",
        "icontains",
        "iexact",
        "iendswith",
        "in",
        "isnull",
        "istartswith",
        "startswith",
    },
}


def get_ephemeral_filter_fields(serializer_or_class):
    meta = getattr(serializer_or_class, "Meta", None)
    if meta is None and not isinstance(serializer_or_class, type):
        meta = getattr(serializer_or_class.__class__, "Meta", None)
    return getattr(meta, "filter_fields", {})


def normalize_ephemeral_filter_field(field_name, filter_fields):
    field_config = filter_fields[field_name]
    operators = None

    if isinstance(field_config, str):
        queryset_field = field_config
        field_type = "string"
    elif isinstance(field_config, dict):
        queryset_field = field_config.get("source", field_name)
        field_type = field_config.get("type", "string")
        operators = field_config.get("operators")
    else:
        queryset_field = field_config[0]
        field_type = field_config[1]
        if len(field_config) > 2:
            operators = field_config[2]

    return queryset_field, field_type, operators


def get_ephemeral_filter_operators(field_type, operators=None):
    if operators is not None:
        return set(operators)
    return EPHEMERAL_FILTER_TYPE_OPERATORS.get(
        field_type,
        EPHEMERAL_FILTER_TYPE_OPERATORS["string"],
    )


def _class_name_for_resource(name):
    parts = re.split(r"[^0-9A-Za-z]+", name or "ephemeral")
    class_name = "".join(part[:1].upper() + part[1:] for part in parts if part)
    return "%sSerializer" % (class_name or "Ephemeral")


def _build_ephemeral_serializer_field(field_config):
    from dynamic_rest import fields as dynamic_fields

    field_type = field_config.get("type", "string")
    field_type_map = {
        "boolean": dynamic_fields.DynamicBooleanField,
        "date": dynamic_fields.DynamicDateField,
        "datetime": dynamic_fields.DynamicDateTimeField,
        "decimal": dynamic_fields.DynamicDecimalField,
        "float": dynamic_fields.DynamicFloatField,
        "integer": dynamic_fields.DynamicIntegerField,
        "json": dynamic_fields.DynamicJSONField,
        "object": dynamic_fields.DynamicJSONField,
        "string": dynamic_fields.DynamicCharField,
        "text": dynamic_fields.DynamicTextField,
    }
    field_class = field_config.get("field_class") or field_type_map.get(
        field_type,
        dynamic_fields.DynamicCharField,
    )
    kwargs = {
        "read_only": field_config.get("read_only", True),
        "required": field_config.get("required", False),
        "allow_null": field_config.get(
            "allow_null",
            field_config.get("nullable", True),
        ),
        "label": field_config.get("label"),
        "help_text": field_config.get("description"),
        "ui": field_config.get("ui", True),
        "api_type": field_config.get("api_type", field_type),
        "sortable": field_config.get("sortable", False),
    }
    if field_type in {"string", "text"}:
        kwargs["allow_blank"] = field_config.get("allow_blank", True)
    if field_type == "decimal" and issubclass(
        field_class,
        dynamic_fields.DynamicDecimalField,
    ):
        kwargs["max_digits"] = field_config.get("max_digits", 30)
        kwargs["decimal_places"] = field_config.get("decimal_places", 10)

    kwargs.update(field_config.get("field_kwargs", {}))
    return field_class(**kwargs)


def build_ephemeral_serializer(
    name,
    fields,
    plural_name=None,
    class_name=None,
    id_field="pk",
    name_field=None,
    icon=None,
    description=None,
    section=None,
    serializer_base_class=None,
    meta_options=None,
):
    """Build a DREST serializer for a synthetic resource schema.

    ``fields`` is an ordered mapping of public field name to either a DRF field
    instance or a config dictionary. Config dictionaries may include:

    - ``type``: string, integer, decimal, float, boolean, date, datetime, object
    - ``label`` / ``description`` / ``ui`` / ``nullable``
    - ``filterable`` plus ``filter_source``, ``filter_type`` and
      ``filter_operators``
    - ``sortable`` for metadata only; callers still apply ordering themselves.
    """
    from rest_framework import serializers

    from dynamic_rest.serializers import DynamicEphemeralSerializer

    serializer_base_class = serializer_base_class or DynamicEphemeralSerializer
    declared = {}
    serializer_fields = []
    filter_fields = {}

    for field_name, field_config in fields.items():
        if field_config is False:
            continue
        if field_config is None:
            field_config = {}

        if isinstance(field_config, serializers.Field):
            field = field_config
            config = {}
        else:
            config = dict(field_config)
            if not config.get("include", True):
                continue
            field = config.get("field") or _build_ephemeral_serializer_field(config)

        field.ui = config.get("ui", getattr(field, "ui", True))
        field.api_type = config.get(
            "api_type",
            config.get("type", getattr(field, "api_type", None)),
        )
        if getattr(field, "sortable", None) is None:
            field.sortable = config.get("sortable", False)
        if config.get("extra") is not None:
            field.extra = config["extra"]

        declared[field_name] = field
        serializer_fields.append(field_name)

        if config.get("filterable", False):
            filter_fields[field_name] = {
                "source": config.get("filter_source")
                or config.get("queryset_field")
                or config.get("source")
                or field_name,
                "type": config.get("filter_type")
                or config.get("type")
                or "string",
                "operators": config.get("filter_operators")
                or config.get("operators"),
            }

    meta_attrs = {
        "name": name,
        "plural_name": plural_name or "%ss" % name,
        "fields": tuple(serializer_fields),
        "filter_fields": filter_fields,
    }
    if id_field is not None:
        meta_attrs["pk_field"] = id_field
    if name_field is not None:
        meta_attrs["name_field"] = name_field
    if icon is not None:
        meta_attrs["icon"] = icon
    if description is not None:
        meta_attrs["description"] = description
    if section is not None:
        meta_attrs["section"] = section
    if meta_options:
        meta_attrs.update(meta_options)

    declared["Meta"] = type("Meta", (), meta_attrs)
    return type(
        class_name or _class_name_for_resource(name),
        (serializer_base_class,),
        declared,
    )
