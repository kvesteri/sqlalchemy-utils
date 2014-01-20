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
    """
    ChoiceType offers way of having fixed set of choices for given column.
    Columns with ChoiceTypes are automatically coerced to Choice objects.


    ::


        class User(self.Base):
            TYPES = [
                (u'admin', u'Admin'),
                (u'regular-user', u'Regular user')
            ]

            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            type = sa.Column(ChoiceType(TYPES))


        user = User(type=u'admin')
        user.type  # Choice(type='admin', value=u'Admin')



    ChoiceType is very useful when the rendered values change based on user's
    locale:

    ::

        from babel import lazy_gettext as _


        class User(self.Base):
            TYPES = [
                (u'admin', _(u'Admin')),
                (u'regular-user', _(u'Regular user'))
            ]

            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            type = sa.Column(ChoiceType(TYPES))


        user = User(type=u'admin')
        user.type  # Choice(type='admin', value=u'Admin')

        print user.type  # u'Admin'
    """

    impl = types.Unicode(255)

    def __init__(self, choices, impl=None):
        if not choices:
            raise ImproperlyConfigured(
                'ChoiceType needs list of choices defined.'
            )
        self.choices = choices
        self.choices_dict = dict(choices)
        if impl:
            self.impl = impl

    @property
    def python_type(self):
        return self.impl.python_type

    def _coerce(self, value):
        if value is None:
            return value
        if isinstance(value, Choice):
            return value
        return Choice(value, self.choices_dict[value])

    def process_bind_param(self, value, dialect):
        if value and isinstance(value, Choice):
            return value.code
        return value

    def process_result_value(self, value, dialect):
        if value:
            return Choice(value, self.choices_dict[value])
        return value
