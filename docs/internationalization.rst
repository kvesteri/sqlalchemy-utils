Internationalization
====================

SQLAlchemy-Utils provides a way for modeling translatable models. Model is
translatable if one or more of its columns can be displayed in various languages.

.. note::

    The implementation is currently highly PostgreSQL specific since it needs
    a dict-compatible column type (PostgreSQL HSTORE and JSON are such types).
    If you want database-agnostic way of modeling i18n see `SQLAlchemy-i18n`_.


TranslationHybrid vs SQLAlchemy-i18n
------------------------------------

Compared to SQLAlchemy-i18n the TranslationHybrid has the following pros and cons:

* Usually faster since no joins are needed for fetching the data
* Less magic
* Easier to understand data model
* Only PostgreSQL supported for now


Quickstart
----------

Let's say we have an Article model with translatable name and content. First we
need to define the TranslationHybrid.

::

    from sqlalchemy_utils import TranslationHybrid


    # For testing purposes we define this as simple function which returns
    # locale 'fi'. Usually you would define this function as something that
    # returns the user's current locale.
    def get_locale():
        return 'fi'


    translation_hybrid = TranslationHybrid(
        current_locale=get_locale,
        default_locale='en'
    )


Then we can define the model.::


    from sqlalchemy import *
    from sqlalchemy.dialects.postgresql import HSTORE


    class Article(Base):
        __tablename__ = 'article'

        id = Column(Integer, primary_key=True)
        name_translations = Column(HSTORE)
        content_translations = Column(HSTORE)

        name = translation_hybrid(name_translations)
        content = translation_hybrid(content_translations)


Now we can start using our translatable model. By assigning things to
translatable hybrids you are assigning them to the locale returned by the
`current_locale`.
::


    article = Article(name='Joku artikkeli')
    article.name_translations['fi']  # Joku artikkeli
    article.name  # Joku artikkeli


If you access the hybrid with a locale that doesn't exist the hybrid tries to
fetch a the locale returned by `default_locale`.
::

    article = Article(name_translations={'en': 'Some article'})
    article.name  # Some article
    article.name_translations['fi'] = 'Joku artikkeli'
    article.name  # Joku artikkeli


Translation hybrids can also be used as expressions.
::

    session.query(Article).filter(Article.name['en'] == 'Some article')


By default if no value is found for either current or default locale the
translation hybrid returns `None`. You can customize this value with `default_value` parameter
of translation_hybrid. In the following example we make translation hybrid fallback to empty string instead of `None`.

::

    translation_hybrid = TranslationHybrid(
        current_locale=get_locale,
        default_locale='en',
        default_value=''
    )


    class Article(Base):
        __tablename__ = 'article'

        id = Column(Integer, primary_key=True)
        name_translations = Column(HSTORE)

        name = translation_hybrid(name_translations, default)


    Article().name  # ''


Dynamic locales
---------------

Sometimes locales need to be dynamic. The following example illustrates how to setup
dynamic locales.


::

    translation_hybrid = TranslationHybrid(
        current_locale=get_locale,
        default_locale=lambda obj: obj.locale,
    )


    class Article(Base):
        __tablename__ = 'article'

        id = Column(Integer, primary_key=True)
        name_translations = Column(HSTORE)

        name = translation_hybrid(name_translations, default)
        locale = Column(String)


    article = Article(name_translations={'en': 'Some article'})
    session.add(article)
    session.commit()

    article.name  # Some article (even if current locale is other than 'en')




.. _SQLAlchemy-i18n: https://github.com/kvesteri/sqlalchemy-i18n
