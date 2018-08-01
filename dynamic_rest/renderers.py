"""This module contains custom renderer classes."""
from django.utils import six
import copy
from rest_framework.renderers import (
    HTMLFormRenderer,
    ClassLookupDict
)
from django.utils.html import mark_safe
from dynamic_rest.compat import reverse, NoReverseMatch, AdminRenderer
from dynamic_rest.conf import settings
from dynamic_rest import fields


DynamicRelationField = fields.DynamicRelationField

mapping = copy.deepcopy(HTMLFormRenderer.default_style.mapping)
mapping[DynamicRelationField] = {
    'base_template': 'relation.html'
}
mapping[fields.DynamicListField] = {
    'base_template': 'list.html'
}
mapping[fields.DynamicFileField] = {
    'base_template': 'file.html'
}
mapping[fields.DynamicImageField] = {
    'base_template': 'file.html'
}
mapping[fields.DynamicNullBooleanField] = {
    'base_template': 'checkbox.html'
}
mapping[fields.DynamicDecimalField] = {
    'base_template': 'input.html',
    'input_type': 'number',
    'step': '.01'
}
mapping[fields.DynamicPasswordField] = {
    'base_template': 'input.html',
    'input_type': 'password'
}
mapping[fields.DynamicMoneyField] = {
    'base_template': 'input.html',
    'input_type': 'number'
}


def get_user_name(request):
    user = request.user
    if user:
        username = getattr(
            user, getattr(user, 'USERNAME_FIELD', 'username'), None
        )
        name = getattr(
            user, getattr(user, 'NAME_FIELD', 'name'), None
        )
        return name if name else username
    return None


class DynamicHTMLFormRenderer(HTMLFormRenderer):
    template_pack = 'dynamic_rest/form'
    default_style = ClassLookupDict(mapping)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render serializer data and return an HTML form, as a string.
        """
        if renderer_context:
            style = renderer_context.get('style', {})
            style['template_pack'] = self.template_pack
        return super(DynamicHTMLFormRenderer, self).render(
            data,
            accepted_media_type,
            renderer_context
        )


class DynamicAdminRenderer(AdminRenderer):
    """Admin renderer."""
    form_renderer_class = DynamicHTMLFormRenderer
    template = settings.ADMIN_TEMPLATE

    def get_context(self, data, media_type, context):
        view = context.get('view')
        response = context.get('response')
        request = context.get('request')
        is_error = response.status_code > 399
        is_auth_error = response.status_code in (401, 403)
        is_not_found_error = response.status_code == 404

        # remove envelope for successful responses
        if getattr(data, 'serializer', None):
            serializer = data.serializer
            if hasattr(serializer, 'disable_envelope'):
                serializer.disable_envelope()
            data = serializer.data

        context = super(DynamicAdminRenderer, self).get_context(
            data,
            media_type,
            context
        )

        # add context
        meta = None
        is_detail = context['style'] == 'detail'
        is_list = context['style'] == 'list'
        is_directory = view and view.__class__.__name__ == 'API'
        header = ''

        title = settings.API_NAME or ''
        singular_name = plural_name = description = ''

        results = context.get('results')

        render_style = {}
        render_style['template_pack'] = self.form_renderer_class.template_pack
        render_style['renderer'] = self.form_renderer_class()

        paginator = context.get('paginator')
        columns = context.get('columns')
        serializer = getattr(results, 'serializer', None)
        instance = serializer.instance if serializer else None
        filters = {}
        fields = {}
        create_related_forms = {}
        name_field = None

        if isinstance(instance, list):
            instance = None

        nav_icon = '<span class="material-icons">menu</span>'

        if is_error:
            context['style'] = 'error'
            if is_auth_error:
                title = header = 'Unauthorized'
            if is_not_found_error:
                title = header = 'Not Found'

        elif is_directory:
            context['style'] = 'directory'
            title = header = settings.API_NAME or ''
            description = settings.API_DESCRIPTION

        elif serializer:
            name_field = serializer.get_name_field()

            related_serializers = serializer.create_related_serializers or []
            if related_serializers:
                related_serializers = related_serializers.items()
            create_related_forms = {
                name: (
                    serializer,
                    self.render_form_for_serializer(serializer)
                )
                for name, serializer
                in related_serializers
            }
            filters = serializer.get_filters()
            meta = serializer.get_meta()
            singular_name = serializer.get_name().title()
            plural_name = serializer.get_plural_name().title()
            description = serializer.get_description()
            icon = serializer.get_icon()
            if icon:
                nav_icon = '<span class="{0} {0}-{1}"></span>'.format(
                    settings.ADMIN_ICON_PACK,
                    icon
                )
            header = serializer.get_plural_name().title().replace('_', ' ')

            if is_list:
                if paginator:

                    paging = paginator.get_page_metadata()
                    count = paging['total_results']
                else:
                    count = len(results)
                header = '%d %s' % (count, header)
            elif is_detail:
                header = serializer.get_name().title().replace('_', ' ')

            title = header

            if is_list:
                list_fields = getattr(meta, 'list_fields', None) or meta.fields
                blacklist = ('id', )
                if not isinstance(list_fields, six.string_types):
                    # respect serializer field ordering
                    columns = [
                        f for f in list_fields
                        if f in columns and f not in blacklist
                    ]

            fields = serializer.get_all_fields()

        # login and logout
        login_url = ''
        try:
            login_url = settings.ADMIN_LOGIN_URL or reverse(
                'dynamic_rest:login'
            )
        except NoReverseMatch:
            try:
                login_url = (
                    settings.ADMIN_LOGIN_URL or reverse('rest_framework:login')
                )
            except NoReverseMatch:
                pass

        logout_url = ''
        try:
            logout_url = (
                settings.ADMIN_LOGOUT_URL or reverse('dynamic_rest:logout')
            )
        except NoReverseMatch:
            try:
                logout_url = (
                    settings.ADMIN_LOGOUT_URL or reverse('dynamic_rest:logout')
                )
            except NoReverseMatch:
                pass

        if getattr(serializer, 'child', None):
            permissions = getattr(serializer.child, 'permissions', None)
        else:
            permissions = getattr(serializer, 'permissions', None)

        allowed_methods = set(
            (x.lower() for x in (view.http_method_names or ()))
        )
        allowed = set()
        if 'put' in allowed_methods:
            allowed.add('update')
        if 'post' in allowed_methods:
            allowed.add('create')
        if 'delete' in allowed_methods:
            allowed.add('delete')
        if 'get' in allowed_methods:
            allowed.add('list')
            allowed.add('read')

        if permissions:
            if not permissions.delete:
                allowed.discard('delete')
            elif not permissions.delete.no_access:
                if instance and not instance._meta.model.objects.filter(
                    permissions.delete.filters
                ).filter(pk=instance.pk).exists():
                    allowed.discard('delete')
            if not permissions.update:
                allowed.discard('update')
            elif not permissions.update.no_access:
                if instance and not instance._meta.model.objects.filter(
                    permissions.update.filters
                ).filter(pk=instance.pk).exists():
                    allowed.discard('update')

            if not permissions.create:
                allowed.discard('create')

            if not permissions.list:
                allowed.discard('list')

        from dynamic_rest.routers import get_directory, get_home

        if hasattr(view, 'get_actions'):
            actions = view.get_actions()
        else:
            actions = []

        home = get_home(request)

        if home and request.path == home:
            nav_icon = '<span class="material-icons">home</span>'
            title = header = 'Home'

        context['name_field'] = name_field
        context['search_key'] = (
            serializer.get_search_key() if serializer
            else None
        )
        context['user_name'] = get_user_name(request)
        context['actions'] = actions
        context['render_style'] = render_style
        context['directory'] = get_directory(request, icons=True)
        context['home'] = home
        context['filters'] = filters
        context['num_filters'] = sum([
            1 if (
                any([ff is not None for ff in f.value])
                if isinstance(f.value, list)
                else f.value is not None
            ) else 0
            for f in filters.values()
        ])
        context['columns'] = columns
        context['fields'] = fields
        context['serializer'] = serializer
        context['sortable_fields'] = set([
            c for c in columns if (
                getattr(fields.get(c), 'sort_field', None)
            )
        ])
        sorted_ascending = None
        if hasattr(view, 'get_request_feature'):
            sorted_field = view.get_request_feature(view.SORT)
            sorted_field = sorted_field[0] if sorted_field else None
            if sorted_field:
                if sorted_field.startswith('-'):
                    sorted_field = sorted_field[1:]
                    sorted_ascending = False
                else:
                    sorted_ascending = True
        else:
            sorted_field = None

        context['actions'] = actions
        context['create_related_forms'] = create_related_forms
        context['sorted_field'] = sorted_field
        context['sorted_ascending'] = sorted_ascending
        context['details'] = context['columns']
        context['description'] = description
        context['singular_name'] = singular_name
        context['plural_name'] = plural_name
        context['login_url'] = login_url
        context['logout_url'] = logout_url
        context['header'] = header
        context['title'] = title
        context['api_name'] = settings.API_NAME
        context['url'] = request.get_full_path()
        context['allow_filter'] = (
            'list' in allowed
        ) and bool(filters)
        context['allow_search'] = (
            'list' in allowed
        )
        context['list_url'] = (
            '/' if serializer is None
            else serializer.get_url()
        )
        context['detail_url'] = (
            None if serializer is None or instance is None
            else serializer.get_url(instance.pk)
        )
        context['allow_delete'] = (
            'delete' in allowed and is_detail
            and bool(instance)
        )
        context['allow_edit'] = (
            'update' in allowed and
            is_detail and
            bool(instance)
        )
        context['allow_add'] = (
            'create' in allowed and is_list
        )
        context['nav_icon'] = mark_safe(nav_icon)
        context['show_nav'] = (
            not is_auth_error and
            not is_directory
        )
        context['show_menu'] = (
            not is_auth_error
        )
        return context

    def get_filter_form(self, *args, **kwargs):
        return None

    def render_form_for_serializer(self, serializer):
        serializer.disable_envelope()
        if hasattr(serializer, 'initial_data'):
            serializer.is_valid()

        form_renderer = self.form_renderer_class()
        if hasattr(serializer, 'child'):
            # re-initialize the serializer
            serializer = serializer.child.__class__()

        return form_renderer.render(
            serializer.data,
            self.accepted_media_type,
            {'style': {'template_pack': 'dynamic_rest/form'}}
        )
