Using automatic data coercion
=============================

SQLAlchemy-Utils provides various new data types for SQLAlchemy and in order to gain full
advantage of these datatypes you should use coercion_listener. Setting up the listener is easy:

::

    import sqlalchemy as sa
    from sqlalchemy_utils import coercion_listener


    sa.event.listen(sa.orm.mapper, 'mapper_configured', coercion_listener)


The listener automatically detects SQLAlchemy-Utils compatible data types and coerces all attributes
using these types to appropriate objects.


Example
::


    from colour import Color
    from sqlalchemy_utils import ColorType


    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, autoincrement=True)
        name = sa.Column(sa.Unicode(50))
        background_color = sa.Column(ColorType)


    document = Document()
    document.background_color = 'F5F5F5'
    document.background_color  # Color object
    session.commit()
