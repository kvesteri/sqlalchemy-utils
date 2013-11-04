from collections import defaultdict

import sqlalchemy as sa
import six
from sqlalchemy.ext.declarative import declared_attr


class aggregated_attr(declared_attr):
    def __init__(self, fget, *arg, **kw):
        super(aggregated_attr, self).__init__(fget, *arg, **kw)
        self.__doc__ = fget.__doc__

    def __get__(desc, self, cls):
        result = desc.fget(cls)
        cls.__aggregates__ = {
            desc.fget.__name__: desc.__aggregate__
        }
        return result


class AggregateValueGenerator(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.generator_registry = defaultdict(list)
        self.pending_queries = defaultdict(list)

    def generator_wrapper(self, func, aggregate_func, relationship):
        func = aggregated_attr(func)
        func.__aggregate__ = {
            'func': aggregate_func,
            'relationship': relationship
        }
        return func

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
        #self.reset()
        if hasattr(class_, '__aggregates__'):
            for key, value in six.iteritems(class_.__aggregates__):
                relationships = []
                rel_class = class_

                for path_name in value['relationship'].split('.'):
                    rel = getattr(rel_class, path_name)
                    relationships.append(rel)
                    rel_class = rel.mapper.class_

                self.generator_registry[rel_class.__name__].append({
                    'class': class_,
                    'attr': key,
                    'relationship': list(reversed(relationships)),
                    'aggregate': value['func']
                })

    def construct_aggregate_queries(self, session, ctx):
        for obj in session:
            class_ = obj.__class__.__name__
            if class_ in self.generator_registry:
                for func in self.generator_registry[class_]:
                    if isinstance(func['aggregate'], six.string_types):
                        agg_func = eval(func['aggregate'])
                    else:
                        agg_func = func['aggregate'](obj.__class__.id)

                    aggregate_value = (
                        session.query(agg_func)
                    )

                    for rel in func['relationship'][0:-1]:
                        aggregate_value = (
                            aggregate_value
                            .join(
                                rel.property.parent.class_,
                                rel.property.primaryjoin
                            )
                        )
                    aggregate_value = aggregate_value.filter(
                        func['relationship'][-1]
                    )

                    aggregate_value = (
                        aggregate_value.correlate(func['class']).as_scalar()
                    )
                    query = func['class'].__table__.update().values(
                        {func['attr']: aggregate_value}
                    )
                    session.execute(query)


generator = AggregateValueGenerator()
generator.register_listeners()


def aggregate(aggregate_func, relationship, generator=generator):
    """

    Non-atomic implementation:

    http://stackoverflow.com/questions/13693872/


    We should avoid deadlocks:

    http://mina.naguib.ca/blog/2010/11/22/postgresql-foreign-key-deadlocks.html


    ::


        class Thread(Base):
            __tablename__ = 'thread'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregate(sa.func.count, 'comments')
            def comment_count(self):
                return sa.Column(sa.Integer)

            @aggregate(sa.func.max, 'comments')
            def latest_comment_id(self):
                return sa.Column(sa.Integer)

            latest_comment = sa.orm.relationship('Comment', viewonly=True)


        class Comment(Base):
            __tablename__ = 'comment'
            id = sa.Column(sa.Integer, primary_key=True)
            content = sa.Column(sa.Unicode(255))
            thread_id = sa.Column(sa.Integer, sa.ForeignKey(Thread.id))

            thread = sa.orm.relationship(Thread, backref='comments')



    ::


        class Catalog(Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregate(
                sa.func.sum(price) +
                sa.func.coalesce(monthly_license_price, 0),
                'products'
            )
            def net_worth(self):
                return sa.Column(sa.Integer)

            products = sa.orm.relationship('Product')


        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)
            monthly_license_price = sa.Column(sa.Numeric)

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey(Catalog.id))


    """
    def wraps(func):
        return generator.generator_wrapper(
            func,
            aggregate_func,
            relationship
        )
    return wraps
