from six import binary_type


class FileType(TypeDecorator):
    """
    FileType for SQLAlchemy

    When the FileType value is being stored into database the FileType saves
    the filename as unicode in the associated column.

    When the value is fetched from database this type opens the associated
    file object.
    """
    impl = UnicodeText

    def __init__(self, open_func=open, *args, **kwargs):
        self.open_func = open_func
        TypeDecorator.__init__(self, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value:
            if isinstance(value.name, str):
                return value.name.decode('utf8')
            else:
                return value.name

    def process_result_value(self, value, dialect):
        if value:
            return self.open_func(value.encode('utf8'))
