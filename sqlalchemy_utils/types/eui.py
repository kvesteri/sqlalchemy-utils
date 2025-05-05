from typing import Any, Type

from sqlalchemy import types
from ..exceptions import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible

eui = None
try:
    from netaddr import EUI
    python_eui_type = EUI
except (ImportError, AttributeError):
    python_eui_type = None


class EUIType(ScalarCoercible, types.TypeDecorator):
    """

    EUIType provides a way for saving EUI (from netaddr package) objects
    into database.  EUIType saves EUI objects as strings on the way in
    and converts them back to objects when querying the database.

    EUI objects can store either EUI64 identifiers or EUI48 identifiers
    EUI48 is frequently used for network MAC addresses.

    ::

        from netaddr import EUI
        from sqlalchemy_utils import EUI


        class Interface(Base):
            __tablename__ = 'interface'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            mac_address = sa.Column(EUIType)

        intf = Interface()
        intf.mac_address = EUI('a1:b2:c3:d4:e5:f6')
        session.commit()


    Querying the database returns EUI objects:

    ::

        import netaddr

        intf = session.query(Interface).first()

        intf.mac_address.dialect = netaddr.mac_unix
        intf.mac_address
        # 'a1:b2:c3:d4:e5:f6'

    .. _netaddr: https://github.com/netaddr/netaddr
    """

    impl = types.Unicode(50)
    cache_ok = True

    def __init__(self, max_length=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = types.Unicode(max_length)


    def process_bind_param(selfself, value, dialect):
        return str(value) if value else None

    def process_result_value(selfself, value, dialect):
        return EUI(value) if value else None

    def _coerce(self, value):
        return EUI(value) if value else None

    @property
    def python_type(self):
        return self.impl.type.python_type
