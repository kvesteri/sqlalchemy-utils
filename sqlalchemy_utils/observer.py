import sqlalchemy as sa

from collections import defaultdict, namedtuple, Iterable
import itertools
from sqlalchemy_utils.functions import getdotattr
from sqlalchemy_utils.path import AttrPath
from sqlalchemy_utils.utils import is_sequence


Callback = namedtuple('Callback', ['func', 'path', 'backref', 'fullpath'])


class PropertyObserver(object):
    def __init__(self):
        self.listener_args = [
            (
                sa.orm.mapper,
                'mapper_configured',
                self.update_generator_registry
            ),
            (
                sa.orm.mapper,
                'after_configured',
                self.gather_paths
            ),
            (
                sa.orm.session.Session,
                'before_flush',
                self.invoke_callbacks
            )
        ]
        self.callback_map = defaultdict(list)
        # TODO: make the registry a WeakKey dict
        self.generator_registry = defaultdict(list)

    def remove_listeners(self):
        for args in self.listener_args:
            sa.event.remove(*args)

    def register_listeners(self):
        for args in self.listener_args:
            if not sa.event.contains(*args):
                sa.event.listen(*args)

    def update_generator_registry(self, mapper, class_):
        """
        Adds generator functions to generator_registry.
        """

        for generator in class_.__dict__.values():
            if hasattr(generator, '__observes__'):
                self.generator_registry[class_].append(
                    generator
                )

    def gather_paths(self):
        for class_, callbacks in self.generator_registry.items():
            for callback in callbacks:
                path = AttrPath(class_, callback.__observes__)

                self.callback_map[class_].append(
                    Callback(
                        func=callback,
                        path=path,
                        backref=None,
                        fullpath=path
                    )
                )

                for index in range(len(path)):
                    i = index + 1
                    prop_class = path[index].property.mapper.class_
                    self.callback_map[prop_class].append(
                        Callback(
                            func=callback,
                            path=path[i:],
                            backref=~ (path[:i]),
                            fullpath=path
                        )
                    )

    def gather_callback_args(self, obj, callbacks):
        session = sa.orm.object_session(obj)
        for callback in callbacks:
            backref = callback.backref

            root_objs = getdotattr(obj, backref) if backref else obj
            if root_objs:
                if not isinstance(root_objs, Iterable):
                    root_objs = [root_objs]

                for root_obj in root_objs:
                    objects = getdotattr(
                        root_obj,
                        callback.fullpath,
                        lambda obj: obj not in session.deleted
                    )

                    yield (
                        root_obj,
                        callback.func,
                        objects
                    )

    def changed_objects(self, session):
        objs = itertools.chain(session.new, session.dirty, session.deleted)
        for obj in objs:
            for class_, callbacks in self.callback_map.items():
                if isinstance(obj, class_):
                    yield obj, callbacks

    def invoke_callbacks(self, session, ctx, instances):
        callback_args = defaultdict(lambda: defaultdict(set))
        for obj, callbacks in self.changed_objects(session):
            args = self.gather_callback_args(obj, callbacks)
            for (root_obj, func, objects) in args:
                if is_sequence(objects):
                    callback_args[root_obj][func] = (
                        callback_args[root_obj][func] | set(objects)
                    )
                else:
                    callback_args[root_obj][func] = objects

        for root_obj, callback_objs in callback_args.items():
            for callback, objs in callback_objs.items():
                callback(root_obj, objs)

observer = PropertyObserver()


def observes(path, observer=observer):
    observer.register_listeners()

    def wraps(func):
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        wrapper.__observes__ = path
        return wrapper
    return wraps
