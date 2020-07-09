import warnings

import six
import sqlalchemy as sa
from sqlalchemy import types


class ScalarListException(Exception):
    pass


class ScalarListType(types.TypeDecorator):
    """
    ScalarListType type provides convenient way for saving multiple scalar
    values in one column. ScalarListType works like list on python side and
    saves the result as comma-separated list in the database.

    Example ::


        from sqlalchemy_utils import ScalarListType


        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True)
            hobbies = sa.Column(ScalarListType())


        user = User()
        user.hobbies = [u'football', u'ice_hockey']
        session.commit()


    You can easily set up integer lists too:

    ::


        from sqlalchemy_utils import ScalarListType


        class Player(Base):
            __tablename__ = 'player'
            id = sa.Column(sa.Integer, autoincrement=True)
            points = sa.Column(ScalarListType(int))


        player = Player()
        player.points = [11, 12, 8, 80]
        session.commit()


    :param inner_type:
        The type of the values. Default is ``str``.
    :param separator:
        Separator of the values. Default is ``,``.
    :param coerce_func:
        Custom function to coerce values when read from database.
        By default ``inner_type`` is used instead.
    """

    impl = sa.UnicodeText()

    def __init__(self, inner_type=six.text_type, separator=u',',
                 coerce_func=None):
        self.separator = six.text_type(separator)
        if not isinstance(inner_type, type) and coerce_func is None:
            warn_msg = (
                "ScalarListType has new required argument 'inner_type'. "
                "Provide the type of the values and if required, "
                "pass coerce func as a keyword argument.")
            warnings.warn(warn_msg, DeprecationWarning)
            self.inner_type = None
            self.coerce_func = inner_type
        else:
            self.inner_type = inner_type
            self.coerce_func = coerce_func

    def process_bind_param(self, value, dialect):
        # Convert list of values to unicode separator-separated list
        # Example: [1, 2, 3, 4] -> u'1, 2, 3, 4'
        if value is not None:
            if any(self.separator in six.text_type(item) for item in value):
                raise ScalarListException(
                    "List values can't contain string '%s' (its being used as "
                    "separator. If you wish for scalar list values to contain "
                    "these strings, use a different separator string.)"
                    % self.separator
                )
            if self.inner_type is not None:
                if any(not isinstance(i, self.inner_type) for i in value):
                    msg = "Not all items in value {} match the type {}"
                    raise ValueError(msg.format(value, self.inner_type))
            return self.separator.join(
                map(six.text_type, value)
            )

    def process_result_value(self, value, dialect):
        if value is not None:
            if value == u'':
                return []
            # coerce each value
            coerce_func = self.coerce_func or self.inner_type
            return list(map(
                coerce_func, value.split(self.separator)
            ))
