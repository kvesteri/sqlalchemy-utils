"""
SQLAlchemy-Utils provides some helpers for defining EAV_ models.


.. _EAV:
    http://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model

Why?
----

Consider you have a catalog of products with each Product having very different
set of attributes. Clearly adding separate tables for each product with
distinct columns for each table becomes very time consuming task. Not to
mention it would be impossible for anyone but database admin to add new
attributes to each product.


One solution is to store product attributes in a JSON / XML typed column. This
has some benefits:

    * Schema is easy to define
    * Needs no 'magic'

::


    from sqlalchemy_utils import JSONType


    class Product(self.Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        category = sa.Column(sa.Unicode(255))
        attributes = sa.Column(JSONType)


    product = Product(
        name='Porsche 911',
        category='car',
        attributes={
            'manufactured': '1991',
            'color': 'red',
            'maxspeed': '300'
        }
    )


All good? We have easily defined a model for product which is extendable and
supports all kinds of attributes for products. However what if you want to make
queries such as:

    * Find all red cars with maximum speed reaching atleast 300 km/h?
    * Find all cars that were manufactured before 1990?


This is very JSON / XML columns fall short. You could switch to using NoSQL
databases but those have their own limitations compared to RDBMS.

::


    from sqlalchemy_utils import MetaType, MetaValue


    class Product(self.Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))


    class ProductAttribute(self.Base):
        __tablename__ = 'product_attribute'
        id = sa.Column(sa.Integer, primary_key=True)
        data_type = sa.Column(
            MetaType({
                'unicode': sa.UnicodeText,
                'int': sa.Integer,
                'datetime': sa.DateTime
            })
        )
        name = sa.Column(sa.Unicode(255))
        product_id = sa.Column(
            sa.Integer, sa.ForeignKey(Product.id)
        )
        product = sa.orm.relationship(Product)


    class ProductAttributeValue(self.Base):
        __tablename__ = 'product_attribute_value'
        id = sa.Column(sa.Integer, primary_key=True)

        product_attr_id = sa.Column(
            sa.Integer, sa.ForeignKey(ProductAttribute.id)
        )
        product_attr = sa.orm.relationship(ProductAttribute)

        value = MetaValue('product_attr', 'data_type')


"""

from inspect import isclass
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
import six


class MetaType(sa.types.TypeDecorator):
    impl = sa.types.UnicodeText

    def __init__(self, data_types):
        sa.types.TypeDecorator.__init__(self)
        self.data_types = data_types

    def type_key(self, data_type):
        for key, type_ in six.iteritems(self.data_types):
            if (
                isinstance(data_type, type_) or
                (isclass(data_type) and issubclass(data_type, type_))
            ):
                return six.text_type(key)

    def process_bind_param(self, value, dialect):
        if value is None:
            return
        return self.type_key(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.data_types[value]


class MetaValue(object):
    def __init__(self, attr, type_column):
        self.attr = attr
        self.type_column = type_column


def coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


@sa.event.listens_for(sa.orm.mapper, 'mapper_configured')
def instrument_meta_values(mapper, class_):
    operations = []
    for key, attr_value in six.iteritems(class_.__dict__):
        if isinstance(attr_value, MetaValue):
            attr = attr_value.attr
            type_column = attr_value.type_column

            parent_class = getattr(class_, attr).mapper.class_
            type_prop = getattr(parent_class, type_column).property
            type_ = type_prop.columns[0].type
            generated_keys = []
            for type_key, data_type in six.iteritems(type_.data_types):
                generated_key = key + '_' + type_key
                operations.append((
                    class_,
                    generated_key,
                    sa.Column(generated_key, data_type)
                ))
                generated_keys.append(generated_key)

            def getter(self):
                return coalesce(
                    *map(lambda key: getattr(self, key), generated_keys)
                )

            def setter(self, value):
                setattr(
                    self,
                    key + '_' +
                    type_.type_key(
                        getattr(
                            getattr(self, attr),
                            type_column
                        )
                    ),
                    value
                )

            def expression(self):
                return sa.func.coalesce(
                    *map(lambda key: getattr(self, key), generated_keys)
                )

            operations.append((
                class_,
                key,
                hybrid_property(
                    getter,
                    setter,
                    expr=expression
                )
            ))

    for operation in operations:
        setattr(*operation)
