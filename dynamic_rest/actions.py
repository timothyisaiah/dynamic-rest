import os


class Action(object):
    def __init__(
        self,
        icon=None,
        label=None,
        permissions=None,
        on_detail=False,
        on_list=False,
        url=None,
        **kwargs
    ):
        self.icon = icon
        self.label = label
        self.permissions = permissions
        self.url = url
        # set during binding
        self.view = None
        self.name = None
        self.on_detail = on_detail
        self.on_list = on_list

    def bind(self, view, name):
        self.name = name
        self.view = view
        if not self.url:
            self.url = os.path.join(
                view.get_url(view.get_pk()),
                name
            )
        elif callable(self.url):
            self.url = self.url(view)


def action(**kwargs):
    a = Action(**kwargs)

    def decorator(fn):
        fn.drest_action = a
        return fn

    return decorator
