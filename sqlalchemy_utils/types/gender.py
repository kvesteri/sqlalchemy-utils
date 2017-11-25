import sqlalchemy as sa

from ..operators import CaseInsensitiveComparator


class GenderType(sa.types.TypeDecorator):
    """
    GenderType represents the gender identity of a person. It is as inclusive
    as possible, suggesting "simple" genders like "male" and "female"
    but also supporting arbitrary text input for non-binary gender identities.
    This data is stored in the database as a lowercase string.

    This database type is primarily useful so that form libraries like wtforms
    can detect that this column represents a person's gender, which allows
    the form library to render an inclusive HTML form field that allows the
    user to select their gender.
    """
    impl = sa.Unicode(255)
    comparator_factory = CaseInsensitiveComparator

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.lower()
        return value

    @property
    def python_type(self):
        return self.impl.type.python_type
