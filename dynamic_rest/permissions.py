from django.db.models import Q
from django.db import transaction
from rest_framework import exceptions
from rest_framework.fields import flatten_choices_dict, to_choices_dict
from django.utils.functional import cached_property


class Me(object):
    def __repr__(self):
        return "<the current user>"


class Filter(object):
    def __repr__(self):
        return str(self.spec)

    def __init__(self, spec, user=None):
        if callable(spec):
            try:
                spec = spec(user)
            except TypeError:
                pass

        self.spec = spec
        self.user = user

    def __and__(self, other):
        no_access = self.no_access
        if no_access:
            return self.NO_ACCESS
        no_access = other.no_access
        if no_access:
            return self.NO_ACCESS

        access = self.full_access
        if access:
            return other
        access = other.full_access
        if access:
            return self

        filters = self.do_and(self.filters, other.filters)
        return self(filters, self.user)

    def do_and(self, a, b):
        return a & b

    def do_or(self, a, b):
        return a | b

    def __or__(self, other):
        access = self.full_access
        if access:
            return self.FULL_ACCESS
        access = other.full_access
        if access:
            return self.FULL_ACCESS

        no_access = self.no_access
        if no_access:
            return other
        no_access = other.no_access
        if no_access:
            return self

        filters = self.do_or(self.filters, other.filters)
        return Filter(filters, self.user)

    def __bool__(self):
        if self.no_access:
            return False
        return True

    __nonzero__ = __bool__

    def __not__(self):
        if self.full_access:
            return self.NO_ACCESS
        if self.no_access:
            return self.FULL_ACCESS
        return Filter(~self.filters, self.user)

    @cached_property
    def filters(self):
        if self.full_access:
            return Q()
        if self.no_access:
            return Q(pk=None)

        user = self.user
        spec = self.spec

        if isinstance(spec, Q):
            return spec

        if isinstance(spec, Me) or spec is Me:
            return Q(pk=user.pk)

        if isinstance(spec, dict):
            spec = {
                k: user if isinstance(v, Me) or v is Me else v for k, v in spec.items()
            }
            return Q(**spec)

        raise Exception("Not sure how to deal with: %s" % spec)

    @property
    def no_access(self):
        return self.spec is False or self.spec is None or self.spec == {}

    @property
    def full_access(self):
        return self.spec is True


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value
    return destination


class Fields(Filter):
    @cached_property
    def filters(self):
        return self.spec

    def do_and(self, a, b):
        return merge(a, merge(b, {}))

    def do_or(self, a, b):
        return self.do_and(a, b)


Filter.FULL_ACCESS = Filter(True)

Filter.NO_ACCESS = Filter(False)


class Role(object):
    def __repr__(self):
        return str(self.spec)

    def __init__(self, spec, user):
        self.user = user
        self.spec = spec

    @cached_property
    def fields(self):
        return self.get_fields()

    @cached_property
    def list(self):
        return self.get("list")

    @cached_property
    def read(self):
        return self.get("read")

    @cached_property
    def delete(self):
        return self.get("delete")

    @cached_property
    def create(self):
        return self.get("create")

    @cached_property
    def update(self):
        return self.get("update")

    def get_fields(self):
        spec = self.spec.get("fields", None)
        if spec is None:
            return Fields.NO_ACCESS
        return Fields(spec, self.user)

    def get(self, name):
        spec = self.spec.get(name, False)
        while isinstance(spec, Filter):
            spec = spec.spec

        if spec is False:
            return Filter.NO_ACCESS

        if spec is True:
            return Filter.FULL_ACCESS

        return Filter(
            spec,
            self.user,
        )


class Permissions(object):
    ALL_METHODS = {"read", "list", "create", "update", "delete"}

    def __repr__(self):
        return str(self.spec)

    def __init__(self, spec, user, allowed=None):
        self.allowed = self.ALL_METHODS if allowed is None else allowed
        self.spec = spec
        self.user = user

    def has_role(self, role):
        if role == "*":
            return True
        role = getattr(self.user, role, None)
        return bool(role)

    @cached_property
    def roles(self):
        user = self.user
        return [Role(v, user) for k, v in self.spec.items() if self.has_role(k)]

    @cached_property
    def fields(self):
        return self.get("fields")

    @cached_property
    def list(self):
        return self.get("list")

    @cached_property
    def read(self):
        return self.get("read")

    @cached_property
    def delete(self):
        return self.get("delete")

    @cached_property
    def update(self):
        return self.get("update")

    @cached_property
    def create(self):
        return self.get("create")

    def get(self, name):
        if name != "fields" and name not in self.allowed:
            # method not allowed at the view level
            return Filter.NO_ACCESS

        roles = self.roles
        f = None
        for role in roles:
            r = getattr(role, name)
            if f is None:
                f = r
            else:
                f |= r

        result = f if f is not None else Filter.NO_ACCESS

        # if self.user.is_superuser and result.no_access and name != 'fields':
        #    # unless blocked by view.http_method_names, superuser has full access
        #    return result.FULL_ACCESS

        return result

    def serialize(self):
        return {
            "create": bool(self.create),
            "update": bool(self.update),
            "delete": bool(self.delete),
            "list": bool(self.list),
            "read": bool(self.read),
            "fields": self.fields.spec,
        }


class PermissionsSerializerMixin(object):
    def initialized(self, **kwargs):
        super(PermissionsSerializerMixin, self).initialized(**kwargs)
        if not kwargs.get("nested", False):
            full_permissions = self.full_permissions

            if full_permissions and full_permissions.fields:
                spec = full_permissions.fields.spec
                fields = self.fields
                for name, values in spec.items():
                    if name in fields:
                        field = fields[name]
                        for key, value in values.items():
                            if key == "choices":
                                # special-case
                                field.grouped_choices = to_choices_dict(value)
                                field.choices = flatten_choices_dict(
                                    field.grouped_choices
                                )
                                field.choice_strings_to_values = {
                                    str(key): key for key in field.choices.keys()
                                }
                            else:
                                setattr(field, key, value)

    @classmethod
    def get_user_permissions(cls, user, even_if_superuser=False, allowed=None):
        if not user or (not even_if_superuser and user.is_superuser):
            return None

        permissions = getattr(cls.get_meta(), "permissions", None)
        if permissions:
            return Permissions(permissions, user, allowed=allowed)

        return None

    def get_allowed_methods(self):
        view = self.context.get("view")
        return view.get_allowed_methods()

    @cached_property
    def permissions(self):
        return self.get_user_permissions(
            self.get_request_attribute("user"), allowed=self.get_allowed_methods()
        )

    @cached_property
    def full_permissions(self):
        return self.get_user_permissions(
            self.get_request_attribute("user"),
            even_if_superuser=True,
            allowed=self.get_allowed_methods(),
        )

    def create(self, data, **kwargs):
        permissions = self.permissions

        if permissions:
            access = self.permissions.create
            if access.no_access:
                raise exceptions.PermissionDenied()
            with transaction.atomic():
                instance = super(PermissionsSerializerMixin, self).create(
                    data, **kwargs
                )
                if access.full_access:
                    # grant full create
                    return instance
                else:
                    # check filters
                    model = self.get_model()
                    if model:
                        if (
                            not model.objects.filter(access.filters)
                            .filter(pk=str(instance.pk))
                            .exists()
                        ):
                            raise exceptions.PermissionDenied()
                    return instance
        else:
            return super(PermissionsSerializerMixin, self).create(data, **kwargs)


class PermissionsViewSetMixin(object):
    @classmethod
    def get_user_permissions(cls, user, even_if_superuser=False):
        if not user or (not even_if_superuser and user.is_superuser):
            return None

        permissions = getattr(cls.serializer_class.get_meta(), "permissions", None)
        if permissions:
            return Permissions(
                permissions,
                user,
            )

        return None

    @cached_property
    def permissions(self):
        return self.get_user_permissions(self.request.user)

    @cached_property
    def full_permissions(self):
        return self.get_user_permissions(self.request.user, True)

    def list(self, request, **kwargs):
        permissions = self.permissions
        if not permissions or permissions.list:
            return super(PermissionsViewSetMixin, self).list(request, **kwargs)
        else:
            raise exceptions.PermissionDenied()

    def get_queryset(self):
        permissions = self.permissions
        queryset = super(PermissionsViewSetMixin, self).get_queryset()

        if permissions:
            access = None
            if self.is_list():
                access = permissions.list
            elif self.is_get():
                access = permissions.read
            elif self.is_create():
                access = permissions.read
            elif self.is_update():
                access = permissions.update
            elif self.is_delete():
                access = permissions.delete
            else:
                return queryset

            if access.full_access:
                return queryset
            elif access.no_access:
                return queryset.none()
            else:
                return queryset.filter(access.filters)
        else:
            return queryset
