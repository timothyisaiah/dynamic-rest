from pyresource.server import Server
from pyresource.space import Space
from pyresource.resource import Resource
from pyresource.django.urls import get_urlpatterns
from pyresource.conf import configure

# set high page size to prevent pagination
configure({"page_size": 9999999, "page_total": False})

server = Server(url="http://localhost/")
resource = Space(name="resource", server=server)
users = Resource(
    id="resource.users",
    source="benchmarks.user",
    name="users",
    space=resource,
    fields={
        "id": "id",
        "name": "name",
        "groups": "groups"
    },
)
groups = Resource(
    id="resource.groups",
    source="benchmarks.group",
    name="groups",
    space=resource,
    fields={
        "id": "id",
        "name": "name",
        "permissions": "permissions"
    },
)
permissions = Resource(
    id="resource.groups",
    source="benchmarks.permission",
    name="groups",
    space=resource,
    fields={
        "id": "id",
        "name": "name"
    },
)
urlpatterns = get_urlpatterns(server)
