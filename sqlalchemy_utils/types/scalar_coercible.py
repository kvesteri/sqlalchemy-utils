class ScalarCoercible:
    cache_ok = True

    def _coerce(self, value):
        raise NotImplementedError

    def coercion_listener(self, target, value, oldvalue, initiator):
        return self._coerce(value)
