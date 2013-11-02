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
        self.listeners_registered = False

    def generator_wrapper(self, func, aggregate_func, relationship):
        func = aggregated_attr(func)
        func.__aggregate__ = {
            'func': aggregate_func,
            'relationship': relationship
        }
        return func

    def register_listeners(self):
        if not self.listeners_registered:
            sa.event.listen(
                sa.orm.mapper,
                'mapper_configured',
                self.update_generator_registry
            )
            sa.event.listen(
                sa.orm.session.Session,
                'after_flush',
                self.update_generated_properties
            )
            self.listeners_registered = True

    def update_generator_registry(self, mapper, class_):
        if hasattr(class_, '__aggregates__'):
            for key, value in six.iteritems(class_.__aggregates__):
                rel = getattr(class_, value['relationship'])
                rel_class = rel.mapper.class_
                self.generator_registry[rel_class.__name__].append({
                    'class': class_,
                    'attr': key,
                    'relationship': rel,
                    'aggregate': value['func']
                })

    def update_generated_properties(self, session, ctx):
        for obj in session:
            class_ = obj.__class__.__name__
            if class_ in self.generator_registry:
                for func in self.generator_registry[class_]:
                    aggregate_value = (
                        session.query(func['aggregate'](obj.__class__.id))
                        .filter(func['relationship'].property.primaryjoin)
                        .correlate(func['class']).as_scalar()
                    )
                    query = func['class'].__table__.update().values(
                        {func['attr']: aggregate_value}
                    )
                    session.execute(query)


generator = AggregateValueGenerator()


def aggregate(aggregate_func, relationship, generator=generator):
    """

    Non-atomic implementation:

    http://stackoverflow.com/questions/13693872/


    We should avoid deadlocks:

    http://mina.naguib.ca/blog/2010/11/22/postgresql-foreign-key-deadlocks.html


    ::


        class Thread(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            # _comment_count = sa.Column(sa.Integer)

            # comment_count = aggregate(
            #     '_comment_count',
            #     sa.func.count,
            #     'comments'
            # )
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


    """
    generator.register_listeners()

    def wraps(func):
        return generator.generator_wrapper(
            func,
            aggregate_func,
            relationship
        )
    return wraps
