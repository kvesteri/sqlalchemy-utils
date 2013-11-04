"""
SQLAlchemy-Utils provides way of automatically calculating aggregate values of related models and saving them to parent model.

This solution is inspired by RoR counter cache and especially counter_culture_.



.. _counter_culter:: https://github.com/magnusvk/counter_culture


Non-atomic implementation:

http://stackoverflow.com/questions/13693872/


We should avoid deadlocks:

http://mina.naguib.ca/blog/2010/11/22/postgresql-foreign-key-deadlocks.html


Simple aggregates
-----------------

::

    from sqlalchemy_utils import aggregated_attr


    class Thread(Base):
        __tablename__ = 'thread'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated_attr('comments')
        def comment_count(self):
            return sa.Column(sa.Integer)

        comments = sa.orm.relationship(
            'Comment',
            backref='thread'
        )


    class Comment(Base):
        __tablename__ = 'comment'
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.UnicodeText)
        thread_id = sa.Column(sa.Integer, sa.ForeignKey(Thread.id))

        thread = sa.orm.relationship(Thread, backref='comments')




Custom aggregate expressions
----------------------------


::


    from sqlalchemy_utils import aggregated_attr


    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated_attr
        def net_worth(self):
            return sa.Column(sa.Integer)

        @aggregated_attr.expression
        def net_worth(self):
            return sa.func.sum(Product.price)


        products = sa.orm.relationship('Product')


    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        price = sa.Column(sa.Numeric)
        monthly_license_price = sa.Column(sa.Numeric)

        catalog_id = sa.Column(sa.Integer, sa.ForeignKey(Catalog.id))



::


    from decimal import Decimal


    catalog = Catalog(
        name=u'My first catalog'
        products=[
            Product(name='Some product', price=Decimal(1000)),
            Product(name='Some other product', price=Decimal(500))
        ]
    )
    session.add(catalog)
    session.commit()

    catalog.net_worth  # 1500


"""


from collections import defaultdict

import sqlalchemy as sa
import six
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.expression import _FunctionGenerator


class AggregatedAttribute(declared_attr):
    def __init__(
        self,
        fget,
        relationship,
        expr,
        *arg,
        **kw
    ):
        super(AggregatedAttribute, self).__init__(fget, *arg, **kw)
        self.__doc__ = fget.__doc__
        self.expr = expr
        self.relationship = relationship

    def expression(self, expr):
        self.expr = expr
        return self

    def __get__(desc, self, cls):
        result = desc.fget(cls)
        if not hasattr(cls, '__aggregates__'):
            cls.__aggregates__ = {}
        cls.__aggregates__[desc.fget.__name__] = {
            'expression': desc.expr,
            'relationship': desc.relationship
        }
        return result


class AggregatedValue(object):
    def __init__(self, class_, attr, relationships, expr):
        self.class_ = class_
        self.attr = attr
        self.relationships = relationships

        if isinstance(expr, sa.sql.visitors.Visitable):
            self.expr = expr
        elif isinstance(expr, _FunctionGenerator):
            self.expr = expr(sa.sql.text('1'))
        else:
            self.expr = expr(class_)

    @property
    def aggregate_query(self):
        from_ = self.relationships[0].mapper.class_
        for relationship in self.relationships[0:-1]:
            property_ = relationship.property
            from_ = (
                from_.__table__
                .join(
                    property_.parent.class_,
                    property_.primaryjoin
                )
            )

        query = sa.select(
            [self.expr],
            from_obj=[from_]
        )

        query = query.where(self.relationships[-1])

        return query.correlate(self.class_).as_scalar()

    @property
    def update_query(self):
        return self.class_.__table__.update().values(
            {self.attr: self.aggregate_query}
        )


class AggregationManager(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.generator_registry = defaultdict(list)
        self.pending_queries = defaultdict(list)

    def register_listeners(self):
        sa.event.listen(
            sa.orm.mapper,
            'mapper_configured',
            self.update_generator_registry
        )
        sa.event.listen(
            sa.orm.session.Session,
            'after_flush',
            self.construct_aggregate_queries
        )

    def update_generator_registry(self, mapper, class_):
        if hasattr(class_, '__aggregates__'):
            for key, value in six.iteritems(class_.__aggregates__):
                relationships = []
                rel_class = class_

                for path_name in value['relationship'].split('.'):
                    rel = getattr(rel_class, path_name)
                    relationships.append(rel)
                    rel_class = rel.mapper.class_

                self.generator_registry[rel_class.__name__].append(
                    AggregatedValue(
                        class_=class_,
                        attr=key,
                        relationships=list(reversed(relationships)),
                        expr=value['expression']
                    )
                )

    def construct_aggregate_queries(self, session, ctx):
        for obj in session:
            class_ = obj.__class__.__name__
            if class_ in self.generator_registry:
                for aggregate_value in self.generator_registry[class_]:
                    query = aggregate_value.update_query
                    session.execute(query)


manager = AggregationManager()
manager.register_listeners()


def aggregated_attr(
    relationship,
    expression=sa.func.count
):
    def wraps(func):
        return AggregatedAttribute(
            func,
            relationship,
            expression
        )
    return wraps
