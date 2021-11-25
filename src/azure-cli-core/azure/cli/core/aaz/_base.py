import abc


class AAZValuePatch:

    def __init__(self, data):
        self.data = data


class AAZBaseType:
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def new_patch():
        raise NotImplementedError()

    @abc.abstractmethod
    def value(self, name, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def process(self, name, data):
        raise NotImplementedError()


class AAZBaseValue:

    def __init__(self, name, schema, data):
        self._name = name
        self._schema = schema
        if isinstance(data, AAZValuePatch):
            self._data = data.data
            self._is_patch = True
        else:
            self._data = data
            self._is_patch = False

    @property
    def is_patch(self):
        return self._is_patch


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
