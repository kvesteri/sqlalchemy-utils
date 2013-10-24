from sqlalchemy import types
import six
from ..exceptions import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible


class Choice(object):
    def __init__(self, code, value):
        self.code = code
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Choice):
            return self.code == other.code
        return other == self.code

    def __ne__(self, other):
        return not (self == other)

    def __unicode__(self):
        return six.text_type(self.value)

    def __repr__(self):
        return 'Choice(code={code}, value={value})'.format(
            code=self.code,
            value=self.value
        )


class ChoiceType(types.TypeDecorator, ScalarCoercible):
    impl = types.Unicode(255)

    def __init__(self, choices):
        if not choices:
            raise ImproperlyConfigured(
                'ChoiceType needs list of choices defined.'
            )
        self.choices = choices
        self.choices_dict = dict(choices)

    def _coerce(self, value):
        if value is None:
            return value
        if isinstance(value, Choice):
            return value
        return Choice(value, self.choices_dict[value])

    def process_bind_param(self, value, dialect):
        if value:
            return value.code
        return value

    def process_result_value(self, value, dialect):
        if value:
            return Choice(value, self.choices_dict[value])
        return value
