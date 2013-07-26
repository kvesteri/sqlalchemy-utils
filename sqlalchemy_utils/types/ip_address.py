import six

try:
    from ipaddress import ip_address

except ImportError:
    try:
        from ipaddr import IPAddress as ip_address

    except ImportError:
        ip_address = None


from sqlalchemy import types
from sqlalchemy_utils import ImproperlyConfigured


class IPAddressType(types.TypeDecorator):
    """
    Changes IPAddress objects to a string representation on the way in and
    changes them back to IPAddress objects on the way out.
    """

    impl = types.Unicode(50)

    def __init__(self, max_length=50, *args, **kwargs):
        if not ip_address:
            raise ImproperlyConfigured(
                "'ipaddr' package is required to use 'IPAddressType' "
                "in python 2"
            )

        super(IPAddressType, self).__init__(*args, **kwargs)
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        return six.text_type(value) if value else None

    def process_result_value(self, value, dialect):
        return ip_address(value) if value else None

    def coercion_listener(self, target, value, oldvalue, initiator):
        return ip_address(value) if value else None
