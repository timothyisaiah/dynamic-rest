from .utils import get, is_truthy


def evaluate(when, context):
    return Condition(**when).evaluate(**context)


class Condition(object):
    """A declarative filter"""

    OPERATORS = {
        "isnull": (2, lambda x, y: (x is None) == is_truthy(y)),
        "eq": (2, lambda x, y: x == y),
        "ne": (2, lambda x, y: x != y),
        "gt": (2, lambda x, y: x > y),
        "lt": (2, lambda x, y: x < y),
        "gte": (2, lambda x, y: x >= y),
        "lte": (2, lambda x, y: x <= y),
        "icontains": (2, lambda x, y: x and y and x.lower() in y.lower()),
        "contains": (2, lambda x, y: x and y and y in x),
        "not-contains": (2, lambda x, y: x and y and y not in x),
        "not-in": (2, lambda x, y: x not in y),
        "in": (2, lambda x, y: x in y),
        "range": (2, lambda x, y: x >= y[0] and x <= y[1]),
    }

    def __init__(self, **condition):
        self.condition = condition

    def __str__(self):
        if self.always:
            return "ALWAYS"
        return "(%s)" % (
            " AND ".join(
                ["{k}={v}".format(k=k, v=v) for k, v in self.condition.items()]
            )
        )

    def __unicode__(self):
        return self.__str__()

    @property
    def always(self):
        """Return True iff. this is a tautological condition"""
        return not self.condition

    def evaluate(self, **context):
        """Return True iff. the given context matches the condition"""
        return all(
            [
                self._evaluate(key, value, **context)
                for key, value in self.condition.items()
            ]
        )

    def _evaluate(self, key, value, **context):
        parts = key.split(".")
        last = parts[-1]
        if last in self.OPERATORS:
            path = ".".join(parts[0:-1])
            operator = last
        else:
            path = key
            operator = "eq"

        context = get(path, context)
        num_args, fn = self.OPERATORS[operator]
        if num_args == 1:
            # unary operator
            return fn(context) == value
        else:
            # binary operator
            return fn(context, value)

    def __or__(self, other):
        return OrCondition(self, other)

    def __and__(self, other):
        return AndCondition(self, other)


class ComplexCondition(Condition):
    def __init__(self, *condition):
        self.condition = condition


class OrCondition(ComplexCondition):
    def evaluate(self, **context):
        return any([c.evaluate(**context) for c in self.condition])

    def __str__(self):
        return "(%s)" % (" OR ".join([str(c) for c in self.condition]))


class AndCondition(ComplexCondition):
    def evaluate(self, **context):
        return all([c.evaluate(**context) for c in self.condition])

    def __str__(self):
        return "(%s)" % (" AND ".join([str(c) for c in self.condition]))
