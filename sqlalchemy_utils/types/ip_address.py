import six
import ipaddress
from sqlalchemy import types


class IPAddressType(types.TypeDecorator):
    """
    Changes Color objects to a string representation on the way in and
    changes them back to Color objects on the way out.
    """
    impl = types.Unicode(50)

    def __init__(self, max_length=50, *args, **kwargs):
        super(IPAddressType, self).__init__(*args, **kwargs)
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        if value:
            return six.text_type(value)
        return value

    def process_result_value(self, value, dialect):
        if value:
            return ipaddress.ip_address(value)
        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        if (
            value is not None and
            not isinstance(value, ipaddress.IPv4Address) and
            not isinstance(value, ipaddress.IPv6Address)
        ):
            value = ipaddress.ip_address(value)
        return value
