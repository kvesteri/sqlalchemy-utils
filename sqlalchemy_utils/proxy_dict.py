import sqlalchemy as sa


class ProxyDict(object):
    def __init__(self, parent, collection_name, mapping_attr):
        self.parent = parent
        self.collection_name = collection_name
        self.child_class = mapping_attr.class_
        self.key_name = mapping_attr.key
        self.cache = {}

    @property
    def collection(self):
        return getattr(self.parent, self.collection_name)

    def keys(self):
        descriptor = getattr(self.child_class, self.key_name)
        return [x[0] for x in self.collection.values(descriptor)]

    def __contains__(self, key):
        try:
            return key in self.cache or self[key]
        except KeyError:
            return False

    def fetch(self, key):
        return self.collection.filter_by(**{self.key_name: key}).first()

    def create_new_instance(self, key):
        value = self.child_class(**{self.key_name: key})
        self.collection.append(value)
        return value

    def __getitem__(self, key):
        if key in self.cache:
            return self.cache[key]

        session = sa.orm.object_session(self.parent)
        if not session or not sa.orm.util.has_identity(self.parent):
            value = self.create_new_instance(key)
        else:
            value = self.fetch(key)
            if not value:
                value = self.create_new_instance(key)
        self.cache[key] = value
        return value

    def __setitem__(self, key, value):
        try:
            existing = self[key]
            self.collection.remove(existing)
        except KeyError:
            pass
        self.collection.append(value)
        self.cache[key] = value


def proxy_dict(parent, collection_name, mapping_attr):
    try:
        parent._proxy_dicts
    except AttributeError:
        parent._proxy_dicts = {}

    try:
        return parent._proxy_dicts[collection_name]
    except KeyError:
        parent._proxy_dicts[collection_name] = ProxyDict(
            parent,
            collection_name,
            mapping_attr
        )
    return parent._proxy_dicts[collection_name]


def expire_proxy_dicts(target, context):
    if hasattr(target, '_proxy_dicts'):
        target._proxy_dicts = {}


sa.event.listen(sa.orm.mapper, 'expire', expire_proxy_dicts)
