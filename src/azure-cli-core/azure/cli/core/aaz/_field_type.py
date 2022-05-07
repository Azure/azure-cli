from ._base import AAZBaseType
from .exceptions import AAZUnknownFieldError, AAZConflictFieldDefinitionError, AAZValuePrecisionLossError
from ._field_value import AAZModelValue, AAZDictValue, AAZListValue, AAZSimpleValue


# build in types
class AAZSimpleType(AAZBaseType):
    _data_type = None

    ValueCls = AAZSimpleValue

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_data(self, data, **kwargs):
        if isinstance(data, AAZSimpleValue):
            data = data._data
        assert isinstance(data, self._data_type)
        return data


class AAZIntType(AAZSimpleType):
    _data_type = int


class AAZStrType(AAZSimpleType):
    _data_type = str


class AAZBoolType(AAZSimpleType):
    _data_type = bool


class AAZFloatType(AAZSimpleType):
    _data_type = float

    def process_data(self, data, **kwargs):
        if isinstance(data, AAZSimpleValue):
            data = data._data
        if isinstance(data, int):
            # transform int to float
            if float(data) != data:
                raise AAZValuePrecisionLossError(data, float(data))
            data = float(data)
        assert isinstance(data, self._data_type)
        return data


# compound types

class AAZModelType(AAZBaseType):
    _PROTECTED_KEYWORDS = ("ValueCls", "PatchDataCls", "get_attr_name", "process_data")

    ValueCls = AAZModelValue
    PatchDataCls = dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields = {}
        self._fields_alias_map = {}  # key is the option, value is field

    def __getattr__(self, key):
        name = self.get_attr_name(key)
        if name not in self._fields:
            raise AAZUnknownFieldError(self, key)
        return self._fields[name]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            assert not isinstance(value, AAZBaseType)
            self.__dict__[key] = value
        elif isinstance(value, AAZBaseType):
            if self.get_attr_name(key):
                # key should not be defined before
                raise AAZConflictFieldDefinitionError(f"{key}")
            assert key not in self._PROTECTED_KEYWORDS
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
                    raise AAZConflictFieldDefinitionError(f"{name}")
                self._fields_alias_map[alias] = name
        else:
            raise AAZUnknownFieldError(self, key)

    def get_attr_name(self, key):
        if key in self._fields:
            return key
        elif key in self._fields_alias_map:
            return self._fields_alias_map[key]
        return None

    def process_data(self, data, **kwargs):
        result = {}
        value = AAZModelValue(schema=self, data=result)
        if isinstance(data, AAZModelValue):
            data = data._data
        else:
            assert isinstance(data, (dict, ))

        for key, sub_data in data.items():
            name = self.get_attr_name(key)
            setattr(value, name, sub_data)
        return result


class AAZDictType(AAZBaseType):

    ValueCls = AAZDictValue
    PatchDataCls = dict

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
            raise AAZConflictFieldDefinitionError("Element")

    def __getitem__(self, key):
        return self.Element

    def process_data(self, data, **kwargs):
        result = {}
        value = AAZDictValue(schema=self, data=result)
        if isinstance(data, AAZDictValue):
            data = data._data
        else:
            assert isinstance(data, (dict,))

        for key, sub_data in data.items():
            value[key] = sub_data
        return result


class AAZListType(AAZBaseType):

    ValueCls = AAZListValue
    PatchDataCls = dict

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
            raise AAZConflictFieldDefinitionError("element")

    def __getitem__(self, key):
        return self.Element

    def process_data(self, data, **kwargs):
        result = {}
        value = AAZListValue(schema=self, data=result)

        if isinstance(data, AAZListValue):
            data = data._data
            for idx, sub_data in data.items():
                value[idx] = sub_data
        else:
            assert isinstance(data, list)
            for idx, sub_data in enumerate(data):
                value[idx] = sub_data
        return result
