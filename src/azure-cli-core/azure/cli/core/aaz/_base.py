import abc


class _AAZUndefinedType:

    def __str__(self):
        return 'Undefined'

    def __repr__(self):
        return 'Undefined'

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __bool__(self):
        return False

    def __lt__(self, other):
        self._cmp_err(other, '<')

    def __gt__(self, other):
        self._cmp_err(other, '>')

    def __le__(self, other):
        self._cmp_err(other, '<=')

    def __ge__(self, other):
        self._cmp_err(other, '>=')

    def _cmp_err(self, other, op):
        raise TypeError(f"unorderable types: {self.__class__.__name__}() {op} {other.__class__.__name__}()")


AAZUndefined = _AAZUndefinedType()


class AAZValuePatch:

    @classmethod
    def build(cls, schema):
        if schema._PatchDataCls:
            return cls(data=schema._PatchDataCls())
        else:
            return cls(data=AAZUndefined)

    def __init__(self, data):
        self.data = data


class AAZBaseValue:

    def __init__(self, schema, data):
        self._schema = schema
        if isinstance(data, AAZValuePatch):
            self._data = data.data
            self._is_patch = True
        else:
            self._data = data
            self._is_patch = False

    @abc.abstractmethod
    def to_serialized_data(self, processor=None):
        raise NotImplementedError()


class AAZBaseType:
    _ValueCls = None
    _PatchDataCls = None

    def __init__(self, options=None, nullable=False, serialized_name=None, flags={}):
        assert issubclass(self._ValueCls, AAZBaseValue)
        self._serialized_name = serialized_name
        self._options = options
        self._name = None
        self._nullable = nullable   # when true, specifies that null is a valid value
        self._flags = flags

    @abc.abstractmethod
    def process_data(self, data, **kwargs):
        raise NotImplementedError()


