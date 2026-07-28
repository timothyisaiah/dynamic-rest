"""Helpers for synthetic/ephemeral resource filtering metadata."""

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
