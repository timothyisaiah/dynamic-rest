import os


class Action(object):
    def __init__(
        self,
        icon=None,
        label=None,
        permissions=None,
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

    def bind(self, view, name):
        self.name = name
        self.view = view
        if not self.url:
            self.url = os.path.join(
                view.request.get_full_path(),
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
