# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import abc

# pylint: disable=protected-access, too-few-public-methods


class AAZBaseValue:
    """ Base field value class. Value should combined with a value type definition. """

    def __init__(self, schema, data):
        self._schema = schema   # value type definition
        if isinstance(data, AAZValuePatch):
            self._data = data.data
            self._is_patch = True
        else:
            self._data = data
            self._is_patch = False

    @abc.abstractmethod
    def to_serialized_data(self, processor=None, **kwargs):
        """ serialize value into python build-in type """
        raise NotImplementedError()


class AAZBaseType:
    """ Base field type class. """

    _ValueCls = None
    _PatchDataCls = None

    def __init__(self, options=None, nullable=False, serialized_name=None, flags=None):
        assert issubclass(self._ValueCls, AAZBaseValue)
        self._serialized_name = serialized_name  # name used in serialization
        self._options = options
        self._name = None
        self._nullable = nullable   # when true, specifies that `None` is a valid value
        # support special properties such as `client_flatten` or `read_only`
        self._flags = {} if flags is None else flags

    @abc.abstractmethod
    def process_data(self, data, **kwargs):
        """Process data, make sure the return data followed the Type definition."""
        raise NotImplementedError()


class _AAZUndefinedType:
    """Internal class for AAZUndefined global const"""

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


# AAZ framework defines a global const called AAZUndefined. Which is used to show a field is not defined.
# In order to different with `None` value
# This value is used in aaz package only.
AAZUndefined = _AAZUndefinedType()


class AAZValuePatch:
    """Value patch is used to support partial value definition."""

    @classmethod
    def build(cls, schema):
        """build a value patch from value type"""
        if schema._PatchDataCls:
            return cls(data=schema._PatchDataCls())
        return cls(data=AAZUndefined)

    def __init__(self, data):
        self.data = data


class _AAZBlankArgValueType:
    """Internal class for AAZUndefined global const"""

    def __str__(self):
        return 'BlankArgValue'

    def __repr__(self):
        return 'BlankArgValue'

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


# AAZ framework defines a global const called AAZUndefined. Which is used to show a field is not defined.
# In order to different with `None` value
# This value is used in aaz package only.
AAZBlankArgValue = _AAZBlankArgValueType()
