import sqlalchemy as sa


class ProxyDict(object):
    def __init__(self, parent, collection_name, child_class, key_name):
        self.parent = parent
        self.collection_name = collection_name
        self.child_class = child_class
        self.key_name = key_name
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

    def __getitem__(self, key):
        if key in self.cache:
            return self.cache[key]

        session = sa.orm.object_session(self.parent)
        if not session or not sa.orm.util.has_identity(self.parent):
            value = self.child_class(**{self.key_name: key})
            self.collection.append(value)
        else:
            value = self.fetch(key)
            if not value:
                value = self.child_class(**{self.key_name: key})
                self.collection.append(value)

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
