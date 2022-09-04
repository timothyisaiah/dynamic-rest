"""
Login and logout views for the admin API.

Add these to your root URLconf if you're using the browsable API and
your API requires authentication:

    urlpatterns = [
        ...
        url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
    ]

In Django versions older than 1.9, the urls must be namespaced as 'rest_framework',
and you should make sure your authentication settings include `SessionAuthentication`.
"""  # noqa
from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth import views, REDIRECT_FIELD_NAME
from dynamic_rest.conf import settings as drest

template_name = {'template_name': drest.ADMIN_LOGIN_TEMPLATE}

app_name = 'dynamic_rest'

logout = login = None
if hasattr(views, 'login'):
    login = views.login
else:
    from django.contrib.auth import REDIRECT_FIELD_NAME
    from django.contrib.auth.forms import AuthenticationForm
    def login_view(
        request,
        template_name='registration/login.html',
        redirect_field_name=REDIRECT_FIELD_NAME,
        authentication_form=AuthenticationForm,
        extra_context=None,
        redirect_authenticated_user=False
    ):
        return views.LoginView.as_view(
            template_name=template_name,
            redirect_field_name=redirect_field_name,
            form_class=authentication_form,
            extra_context=extra_context,
            redirect_authenticated_user=redirect_authenticated_user
        )(request)
    login = login_view

if hasattr(views, 'logout'):
    logout = views.logout
else:
    from django.contrib.auth import REDIRECT_FIELD_NAME
    from django.contrib.auth.forms import AuthenticationForm
    def logout_view(
        request,
        next_page=None,
        template_name='registration/logged_out.html',
        redirect_field_name=REDIRECT_FIELD_NAME,
        extra_context=None,
    ):
        return views.LogoutView.as_view(
            next_page=next_page,
            template_name=template_name,
            redirect_field_name=redirect_field_name,
            extra_context=extra_context,
        )(request)
    logout = logout_view


urlpatterns = [
    url(r'^login/$', login, template_name, name='login'),
    url(r'^logout/$', logout, template_name, name='logout'),
]
