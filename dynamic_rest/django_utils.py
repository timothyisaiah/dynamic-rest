from django.db.models.sql.where import WhereNode
from django.db.models.lookups import Lookup
from django.db.models.expressions import Col
from django.db.models.query import QuerySet


def get_filter_kwargs(queryset, prefix=None) -> dict:
    """
    Attempt to parse a queryset's internal SQL tree to build
    a dictionary of {ORM_lookup_path: value} for simple equality filters.

    :param queryset: Django QuerySet (un-executed) whose .query.where
                     you want to inspect.
    :return: A dict mapping 'some__lookup__path' -> value for simple .filter(...).

    Caveats:
      - Only simple AND conditions are handled.
      - Complex Q objects (ORs), subqueries, or advanced lookups won't
        map cleanly back to dotted ORM paths.
      - Many-to-many or reverse foreign keys can get tricky.
      - The path produced may differ from your original .filter() usage
        if the query was built in multiple steps or with different arguments.
    """

    def parse_where_node(node: WhereNode):
        """
        Recursively traverse WhereNode objects, collecting any
        (path, value) pairs for simple equality lookups.
        """
        results = {}
        for child in node.children:
            if isinstance(child, WhereNode):
                # Nested node; recurse
                results.update(parse_where_node(child))
            else:
                # Likely a Lookup (Exact, Gt, Lt, In, etc.)
                lookup = child
                if not (hasattr(lookup, "lhs") and hasattr(lookup, "lookup_name")):
                    continue

                # Must be a simple exact lookup
                if not isinstance(lookup, Lookup):
                    continue

                lhs = lookup.lhs
                rhs = getattr(lookup, "rhs", None)

                # We only handle the case where lhs is a Col
                # (i.e., a simple reference to a model column).
                if isinstance(lhs, Col):
                    orm_path = reconstruct_orm_path_for_col(queryset, lhs)
                    if orm_path is not None:
                        if prefix is not None:
                            orm_path = f"{prefix}__{orm_path}"
                        orm_path = add_lookup_suffix(orm_path, lookup.lookup_name)
                        results[orm_path] = rhs

        return results

    return parse_where_node(queryset.query.where)


def reconstruct_orm_path_for_col(queryset: QuerySet, col: Col) -> str:
    """
    Attempt to reconstruct a dotted ORM path (e.g. 'groups__name')
    from a Django 'Col' object by walking back through the alias_map
    to the base alias.

    :param queryset: The QuerySet whose query contains 'col'.
    :param col: A Col instance pointing to some table alias and column.
    :return: A string like 'groups__name' if it can be resolved,
             or None if it can’t.
    """
    # The final field name in the path (e.g. 'name' from 'groups__name').
    final_field_name = col.target.name
    # This is the alias for the table we are currently on.
    current_alias = col.alias
    base_alias = queryset.query.get_initial_alias()
    alias_map = queryset.query.alias_map

    # We will build the path in reverse: from the final table up to the base table.
    reversed_path = []

    # Walk up the chain of joins until we reach the base alias.
    while True:
        if current_alias == base_alias:
            # We've reached the base model table; break out.
            break

        if current_alias not in alias_map:
            # Shouldn't happen in most normal queries,
            # but if it does, we can't proceed.
            return None

        join_info = alias_map[current_alias]
        join_field = getattr(join_info, "join_field", None)
        if not join_field:
            # Possibly the base table or unexpected structure
            return None

        # 'join_field' is a ForeignKey, ManyToOneRel, etc.
        # We'll use its .name to build the relationship segment.
        reversed_path.append(join_field.name)

        # Move to the parent alias (the table we joined from).
        current_alias = join_info.parent_alias

    # Now reversed_path might look like ['groups'] for a M2M or FK to Group,
    # but it's in reverse order from how we want to display it.
    reversed_path.reverse()

    # Append the final column name (e.g. 'name') at the end
    reversed_path.append(final_field_name)

    # Combine with double-underscores: e.g. 'groups__name'
    return "__".join(reversed_path)


def add_lookup_suffix(base_path: str, lookup_name: str) -> str:
    """
    Return the ORM-style lookup path. If lookup_name is 'exact',
    just return base_path. Otherwise, append __<lookup_name>.

    e.g. add_lookup_suffix("groups__name", "icontains") -> "groups__name__icontains"
    """
    if lookup_name == "exact":
        return base_path
    return f"{base_path}__{lookup_name}"
