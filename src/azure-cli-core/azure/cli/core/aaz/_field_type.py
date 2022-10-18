# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc

from collections import OrderedDict
from ._base import AAZBaseType, AAZValuePatch, AAZUndefined
from ._field_value import AAZObject, AAZDict, AAZFreeFormDict, AAZList, AAZSimpleValue
from .exceptions import AAZUnknownFieldError, AAZConflictFieldDefinitionError, AAZValuePrecisionLossError, \
    AAZInvalidFieldError

# pylint: disable=protected-access, too-few-public-methods, isinstance-second-argument-not-valid-type
# pylint: disable=too-many-instance-attributes


# build in types
class AAZSimpleType(AAZBaseType):
    """Simple value type"""

    DataType = None

    _ValueCls = AAZSimpleValue

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_data(self, data, **kwargs):
        if data == None:  # noqa: E711, pylint: disable=singleton-comparison
            # data can be None or AAZSimpleValue == None
            if self._nullable:
                return None
            return AAZValuePatch.build(self)

        if isinstance(data, AAZSimpleValue):
            if data._is_patch:
                # return value patch
                return AAZValuePatch.build(self)

            data = data._data

        assert self.DataType is not None and isinstance(data, self.DataType), \
            f'Expect {self.DataType}, got {data} ({type(data)}'
        return data


class AAZIntType(AAZSimpleType):
    DataType = int


class AAZStrType(AAZSimpleType):
    DataType = str


class AAZBoolType(AAZSimpleType):
    DataType = bool


class AAZFloatType(AAZSimpleType):
    DataType = float

    def process_data(self, data, **kwargs):
        if data == None:  # noqa: E711, pylint: disable=singleton-comparison
            # data can be None or AAZSimpleValue == None
            if self._nullable:
                return None
            return AAZValuePatch.build(self)

        if isinstance(data, AAZSimpleValue):
            if data._is_patch:
                # return value patch
                return AAZValuePatch.build(self)

            data = data._data

        if isinstance(data, int):
            # transform int to float
            if float(data) != data:
                raise AAZValuePrecisionLossError(data, float(data))
            data = float(data)
        assert isinstance(data, self.DataType), f'Expect {self.DataType}, got {data} ({type(data)}'
        return data


# compound types
class AAZObjectType(AAZBaseType):
    """Object value type"""

    _PROTECTED_KEYWORDS = (
        "get_attr_name",
        "process_data",
        "to_serialized_data",
        "discriminate_by",
        "get_discriminator"
    )   # these keywords are used in AAZObjectValue and AAZObjectType, object should not use them as a field name.

    _ValueCls = AAZObject
    _PatchDataCls = dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # It's important to keep the order of fields.
        # This feature can help to resolve arguments interdependent problem.
        # aaz-dev should register fields based on the interdependent order.
        self._fields = OrderedDict()
        self._fields_alias_map = {}  # key is the option, value is field

        # Polymorphism support
        self._discriminator_field_name = None
        self._discriminators = OrderedDict()

    def __getitem__(self, key):
        name = self.get_attr_name(key)
        if name not in self._fields:
            # must raise AttributeError to support hasattr check
            raise AAZUnknownFieldError(self, key)
        return self._fields[name]

    def __setitem__(self, key, value):
        assert not key.startswith('_')
        assert key not in self._PROTECTED_KEYWORDS

        if not isinstance(value, AAZBaseType):
            raise AAZInvalidFieldError(self, key, f"unknown field type {type(value)}")

        if hasattr(self, key):
            # key should not be defined before
            raise AAZConflictFieldDefinitionError(
                self, key, "Key already been defined before")

        name = key
        value._name = name
        self._fields[name] = value

        # update alias map
        aliases = [*value._options] if value._options else []
        if value._serialized_name:
            aliases.append(value._serialized_name)

        for alias in aliases:
            if alias == name:
                continue

            assert not alias.startswith('_')
            assert alias not in self._PROTECTED_KEYWORDS

            if alias in self._fields_alias_map and self._fields_alias_map[alias] != name:
                raise AAZConflictFieldDefinitionError(
                    self, name, f"Alias is already used by other field: {self._fields_alias_map[alias]}")
            self._fields_alias_map[alias] = name

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            assert not isinstance(value, AAZBaseType)
            self.__dict__[key] = value
        else:
            self[key] = value

    def get_attr_name(self, key):
        if key in self._fields:
            return key
        if key in self._fields_alias_map:
            return self._fields_alias_map[key]
        return None

    def process_data(self, data, **kwargs):
        if data == None:  # noqa: E711, pylint: disable=singleton-comparison
            # data can be None or AAZSimpleValue == None
            if self._nullable:
                return None
            return AAZValuePatch.build(self)

        if isinstance(data, AAZObject) and data._is_patch:
            # use value patch
            result = AAZValuePatch.build(self)
        else:
            result = {}
        value = AAZObject(schema=self, data=result)

        if isinstance(data, AAZObject):
            if self._discriminator_field_name:
                # assign discriminator field first
                for key in data._data.keys():
                    name = self.get_attr_name(key)
                    if name == self._discriminator_field_name:
                        value[name] = data[key]
                        break

            for key in data._data.keys():
                if not hasattr(value, key):
                    # ignore undefined key
                    continue
                value[key] = data[key]

        else:
            assert isinstance(data, (dict,))

            if self._discriminator_field_name:
                # assign discriminator field first
                for key, sub_data in data.items():
                    name = self.get_attr_name(key)
                    if name == self._discriminator_field_name:
                        value[name] = sub_data
                        break

            for key, sub_data in data.items():
                if not hasattr(value, key):
                    # ignore undefined key
                    continue
                value[key] = sub_data

        return result

    # Polymorphism support
    def discriminate_by(self, key, data, schema=None):

        name = self.get_attr_name(key)
        if name not in self._fields:
            raise AAZUnknownFieldError(self, key)
        field = self._fields[name]
        if not isinstance(field, AAZStrType):
            raise AAZInvalidFieldError(self, name, f"Invalid discriminator field type: {type(field)}")
        data = field.process_data(data)
        if self._discriminator_field_name is None:
            self._discriminator_field_name = name
        elif self._discriminator_field_name != name:
            raise AAZConflictFieldDefinitionError(
                self, name, f"Conflict discriminator field name with: {self._discriminator_field_name}")
        schema = schema or AAZObjectType()  # use provided schema or create a object type
        assert isinstance(schema, AAZObjectType)
        return self._discriminators.setdefault(data, schema)

    def get_discriminator(self, data):
        if self._discriminator_field_name is None:
            return None
        if data == AAZUndefined or not data:
            return None
        if isinstance(data, AAZObject):
            data = data._data
        assert isinstance(data, dict)
        for key, field_data in data.items():
            name = self.get_attr_name(key)
            if name == self._discriminator_field_name:
                return self._discriminators.get(field_data, None)
        return None


class AAZBaseDictType(AAZBaseType):

    _PatchDataCls = dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def __getitem__(self, key):
        raise NotImplementedError()

    def process_data(self, data, **kwargs):
        if data == None:  # noqa: E711, pylint: disable=singleton-comparison
            # data can be None or AAZSimpleValue == None
            if self._nullable:
                return None
            return AAZValuePatch.build(self)

        if isinstance(data, self._ValueCls) and data._is_patch:
            # use value patch
            result = AAZValuePatch.build(self)
        else:
            result = {}

        value = self._ValueCls(schema=self, data=result)  # pylint: disable=not-callable

        if isinstance(data, self._ValueCls):
            for key in data._data.keys():
                value[key] = data[key]
        else:
            assert isinstance(data, (dict,))
            for key, sub_data in data.items():
                value[key] = sub_data
        return result


class AAZDictType(AAZBaseDictType):
    """Dict value type"""

    _ValueCls = AAZDict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._element = None

    @property
    def Element(self):
        if self._element is None:
            raise AAZUnknownFieldError(self, "Element")
        return self._element

    @Element.setter
    def Element(self, value):
        if self._element is None:
            assert isinstance(value, AAZBaseType)
            self._element = value
            assert self._element._name is None
            assert not self._element._options
            assert self._element._serialized_name is None
        elif self._element != value:
            raise AAZConflictFieldDefinitionError(self, "Element", "Redefine element in different schema")

    def __getitem__(self, key):
        return self.Element


class AAZFreeFormDictType(AAZBaseDictType):
    """Free form dict value type"""

    _ValueCls = AAZFreeFormDict

    def __getitem__(self, key):
        return None


class AAZListType(AAZBaseType):
    """List value type"""

    _ValueCls = AAZList
    _PatchDataCls = dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._element = None

    @property
    def Element(self):
        if self._element is None:
            raise AAZUnknownFieldError(self, "Element")
        return self._element

    @Element.setter
    def Element(self, value):
        if self._element is None:
            assert isinstance(value, AAZBaseType)
            self._element = value
            assert self._element._name is None
            assert not self._element._options
            assert self._element._serialized_name is None
        elif self._element != value:
            raise AAZConflictFieldDefinitionError(self, "Element", "Redefine element in different schema")

    def __getitem__(self, key):
        return self.Element

    def process_data(self, data, **kwargs):
        if data == None:  # noqa: E711, pylint: disable=singleton-comparison
            # data can be None or AAZSimpleValue == None
            if self._nullable:
                return None
            return AAZValuePatch.build(self)

        if isinstance(data, AAZList) and data._is_patch:
            # use value patch
            result = AAZValuePatch.build(self)
        else:
            result = {}
        value = AAZList(schema=self, data=result)

        if isinstance(data, AAZList):
            for idx in data._data.keys():
                value[idx] = data[idx]
        else:
            assert isinstance(data, list)
            for idx, sub_data in enumerate(data):
                value[idx] = sub_data

        return result
