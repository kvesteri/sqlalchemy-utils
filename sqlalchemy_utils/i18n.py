from .exceptions import ImproperlyConfigured


try:
    from babel.dates import get_day_names
except ImportError:
    def get_day_names():
        raise ImproperlyConfigured(
            'Could not load get_day_names function from babel. Either install '
            ' babel or make a similar function and override it in this '
            'module.'
        )


try:
    from flask.ext.babel import get_locale
except ImportError:
    def get_locale():
        raise ImproperlyConfigured(
            'Could not load get_locale function from Flask-Babel. Either '
            'install babel or make a similar function and override it '
            'in this module.'
        )
