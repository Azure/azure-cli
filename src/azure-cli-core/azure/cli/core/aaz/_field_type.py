from ._base import AAZBaseType, AAZValuePatch, AAZUndefined
from .exceptions import AAZUnknownFieldError, AAZConflictFieldDefinitionError, AAZValuePrecisionLossError
from ._field_value import AAZModelValue, AAZDictValue, AAZListValue, AAZSimpleValue


# build in types
class AAZSimpleType(AAZBaseType):
    _data_type = None

    def __init__(self):
        super().__init__()

    @staticmethod
    def new_patch():
        return AAZValuePatch(data=AAZUndefined)

    def value(self, name, data):
        return AAZSimpleValue(name=name, schema=self, data=data)

    def process(self, name, data):
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

    def process(self, name, data):
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

    def __init__(self):
        super().__init__()
        self._fields = {}

    def __getattr__(self, key):
        if key in self._fields:
            return self._fields[key]
        else:
            raise AAZUnknownFieldError(self, key)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            assert not isinstance(value, AAZBaseType)
            self.__dict__[key] = value
        elif isinstance(value, AAZBaseType):
            self._fields[key] = value
        else:
            raise AAZUnknownFieldError(self, key)

    @property
    def fields(self):
        return self._fields

    @staticmethod
    def new_patch():
        return AAZValuePatch(data={})

    def value(self, name, data):
        assert isinstance(data, (AAZValuePatch, dict))
        return AAZModelValue(name=name, schema=self, data=data)

    def process(self, name, data):
        value = AAZModelValue(name=name, schema=self, data={})
        if isinstance(data, AAZModelValue):
            data = data._data
        else:
            assert isinstance(data, (dict, ))

        for key, sub_data in data.items():
            setattr(value, key, sub_data)
        return value._data


class AAZDictType(AAZBaseType):

    def __init__(self):
        super().__init__()
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
        elif self._element != value:
            raise AAZConflictFieldDefinitionError("Element")

    def __getitem__(self, key):
        return self.Element

    @staticmethod
    def new_patch():
        return AAZValuePatch(data={})

    def value(self, name, data):
        assert isinstance(data, (AAZValuePatch, dict))
        return AAZDictValue(name=name, schema=self, data=data)

    def process(self, name, data):
        value = AAZDictValue(name, schema=self, data={})
        if isinstance(data, AAZDictValue):
            data = data._data
        else:
            assert isinstance(data, (dict,))

        for key, sub_data in data.items():
            value[key] = sub_data
        return value._data


class AAZListType(AAZBaseType):

    def __init__(self):
        super().__init__()
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
        elif self._element != value:
            raise AAZConflictFieldDefinitionError("element")

    def __getitem__(self, key):
        return self.Element

    @staticmethod
    def new_patch():
        return AAZValuePatch(data={})

    def value(self, name, data):
        assert isinstance(data, (AAZValuePatch, dict))
        return AAZListValue(name=name, schema=self, data=data)

    def process(self, name, data):
        value = AAZListValue(name, schema=self, data={})

        if isinstance(data, AAZListValue):
            data = data._data
            assert isinstance(data, dict)
        else:
            assert isinstance(data, list)
            data = dict([(idx, sub_data) for idx, sub_data in enumerate(data)])

        for idx, sub_data in data.items():
            value[idx] = sub_data

        return value._data
