from sqlalchemy.ext.hybrid import hybrid_property

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


class TranslationHybrid(object):
    def __init__(self, current_locale, default_locale):
        self.current_locale = current_locale
        self.default_locale = default_locale

    def cast_locale(self, obj, locale):
        """
        Cast given locale to string. Supports also callbacks that return
        locales.
        """
        if callable(locale):
            try:
                return str(locale())
            except TypeError:
                return str(locale(obj))
        return str(locale)

    def getter_factory(self, attr):
        """
        Return a hybrid_property getter function for given attribute. The
        returned getter first checks if object has translation for current
        locale. If not it tries to get translation for default locale. If there
        is no translation found for default locale it returns None.
        """
        def getter(obj):
            current_locale = self.cast_locale(obj, self.current_locale)
            try:
                return getattr(obj, attr.key)[current_locale]
            except (TypeError, KeyError):
                default_locale = self.cast_locale(
                    obj, self.default_locale
                )
                try:
                    return getattr(obj, attr.key)[default_locale]
                except (TypeError, KeyError):
                    return None
        return getter

    def setter_factory(self, attr):
        def setter(obj, value):
            if getattr(obj, attr.key) is None:
                setattr(obj, attr.key, {})
            locale = self.cast_locale(obj, self.current_locale)
            getattr(obj, attr.key)[locale] = value
        return setter

    def expr_factory(self, attr):
        return lambda cls: attr

    def __call__(self, attr):
        return hybrid_property(
            fget=self.getter_factory(attr),
            fset=self.setter_factory(attr),
            expr=self.expr_factory(attr)
        )
