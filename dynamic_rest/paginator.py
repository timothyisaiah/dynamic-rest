# adapted from Django's django.core.paginator (2.2 - 3.2+ compatible)
# adds support for the "exclude_count" parameter

from math import ceil

import base64
import inspect
from django.utils.functional import cached_property
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page

try:
    from django.utils.translation import gettext_lazy as _
except ImportError:
    def _(x):
        return x

try:
    from django.utils.inspect import method_has_no_args
except ImportError:
    def method_has_no_args(meth):
        """Return True if a method only accepts 'self'."""
        count = len([
            p for p in inspect.signature(meth).parameters.values()
            if p.kind == p.POSITIONAL_OR_KEYWORD
        ])
        return count == 0 if inspect.ismethod(meth) else count == 1


class BasePaginator(Paginator):
    def __init__(self, *args, **kwargs):
        self.exclude_count = kwargs.pop('exclude_count', False)
        self.order_by = kwargs.pop('order_by', '-created')
        super().__init__(*args, **kwargs)

    @cached_property
    def count(self):
        """Return the total number of objects, across all pages."""
        if self.exclude_count:
            # always return 0, count should not be called
            return 0

        c = getattr(self.object_list, 'count', None)
        if callable(c) and not inspect.isbuiltin(c) and method_has_no_args(c):
            return c()
        return len(self.object_list)

    @cached_property
    def num_pages(self):
        """Return the total number of pages."""
        if self.exclude_count:
            # always return 1, count should not be called
            return 1

        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        hits = max(1, self.count - self.orphans)
        return int(ceil(hits / float(self.per_page)))


class DynamicCursorPaginator(BasePaginator):
    def validate_number(self, cursor):
        return True

    def page(self, cursor):
        """Return a Page object for the given 1-based page number."""
        if cursor != '1':
            cursor = base64.b64decode(cursor).decode('utf-8')

        per_page = self.per_page
        per_page += 1

        reverse = '-' in self.order_by
        field = self.order_by.replace('-', '')
        op = 'lt' if reverse else 'gt'
        if cursor == '1':
            # blank starting point
            filters = {}
        else:
            filters = {f'{field}__{op}': cursor}
        order_by = [self.order_by]
        results = self.object_list.filter(**filters).order_by(*order_by)[0:per_page]
        next_cursor = None
        results = list(results)
        num_results = len(results)
        if num_results > self.per_page:
            next_cursor = base64.b64encode(str(getattr(results[-2], field)).encode('utf-8')).decode('utf-8')
        return self._get_page(results, cursor, self, next_cursor=next_cursor)

    def _get_page(self, *args, **kwargs):
        return CursorPage(*args, **kwargs)

class CursorPage(Page):
    def __init__(self, *args, next_cursor=None):
        self.next_cursor = next_cursor
        return super(CursorPage, self).__init__(*args)

    def __repr__(self):
        return '<Page %s>' % (self.number)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError
        # The object_list is converted to a list so that if it was a QuerySet
        # it won't be a database hit per __getitem__.
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def has_next(self):
        return bool(self.next_cursor)

    def has_previous(self):
        return None

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.next_cursor

    def previous_page_number(self):
        return None


class DynamicPageNumberPaginator(BasePaginator):

    def validate_number(self, number):
        """Validate the given 1-based page number."""
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger(_('That page number is not an integer'))
        if number < 1:
            raise EmptyPage(_('That page number is less than 1'))
        if self.exclude_count:
            # skip validating against num_pages
            return number
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage(_('That page contains no results'))
        return number

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if self.exclude_count:
            # always fetch one extra item
            # to determine if more pages are available
            # and skip validation against count
            top = top + 1
        else:
            if top + self.orphans >= self.count:
                top = self.count
        return self._get_page(self.object_list[bottom:top], number, self)
