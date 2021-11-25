from ._base import AAZBaseValue


class AAZSimpleValue(AAZBaseValue):

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def __eq__(self, other):
        if isinstance(other, AAZBaseValue):
            other = other._data
        return self._data == other

    def __ne__(self, other):
        return not (self == other)

    def __bool__(self):
        return bool(self._data)

    def __lt__(self, other):
        if isinstance(other, AAZBaseValue):
            other = other._data
        return self._data < other

    def __gt__(self, other):
        if isinstance(other, AAZBaseValue):
            other = other._data
        return self._data > other

    def __le__(self, other):
        if isinstance(other, AAZBaseValue):
            other = other._data
        return self._data <= other

    def __ge__(self, other):
        if isinstance(other, AAZBaseValue):
            other = other._data
        return self._data >= other


class AAZModelValue(AAZBaseValue):

    def __init__(self, name, schema, data):
        from ._field_type import AAZModelType
        assert isinstance(schema, AAZModelType)
        super().__init__(name, schema, data)
        assert isinstance(self._data, dict)

    def __getattr__(self, key) -> AAZBaseValue:
        key_schema = getattr(self._schema, key)
        if key not in self._data:
            # is key is not set before, then create a patch, and value updated in patch will be partial updated
            self._data[key] = key_schema.new_patch()
        return key_schema.value(key, self._data[key])

    def __setattr__(self, key, data):
        if key.startswith('_'):
            self.__dict__[key] = data
        else:
            key_schema = getattr(self._schema, key)
            self._data[key] = key_schema.process(key, data)

    def __delattr__(self, key):
        if key.startswith('_'):
            del self.__dict__[key]
        elif key in self._data:
            del self._data[key]
        elif key not in self._schema.fields:
            raise KeyError(f"Attribute {key} not exist")


class AAZDictValue(AAZBaseValue):

    def __init__(self, name, schema, data):
        from ._field_type import AAZDictType
        assert isinstance(schema, AAZDictType)
        super().__init__(name, schema, data)
        assert isinstance(self._data, dict)

    def __getitem__(self, key) -> AAZBaseValue:
        schema = self._schema.Element
        if key not in self._data:
            self._data[key] = schema.new_patch()
        return schema.value(key, self._data[key])

    def __setitem__(self, key, data):
        schema = self._schema.Element
        self._data[key] = schema.process(key, data)

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for key in self._data:
            yield key

    def clear(self):
        self._data.clear()

    def keys(self):
        return self._data.keys()

    def values(self):
        schema = self._schema.Element
        for key, data in self._data.items():
            yield schema.value(key, data)

    def items(self):
        schema = self._schema.Element
        for key, data in self._data.items():
            yield key, schema.value(key, data)


class AAZListValue(AAZBaseValue):

    def __init__(self, name, schema, data):
        from ._field_type import AAZListType
        assert isinstance(schema, AAZListType)
        super().__init__(name, schema, data)
        assert isinstance(self._data, dict) # the key is the idx
        self._len = 0
        for idx in self._data:
            if idx + 1 > self._len:
                self._len = idx + 1

    def __getitem__(self, idx) -> AAZBaseValue:
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len:
            raise IndexError(f"list index out of range")
        if idx < 0:
            idx += self._len

        schema = self._schema.Element
        if idx not in self._data:
            self._data[idx] = schema.new_patch()
            if idx + 1 > self._len:
                self._len = idx + 1
        return schema.value(idx, self._data[idx])

    def __setitem__(self, idx, data):
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len:
            raise IndexError(f"list index out of range")
        if idx < 0:
            idx += self._len

        schema = self._schema.Element
        self._data[idx] = schema.process(idx, data)
        if idx + 1 > self._len:
            self._len = idx + 1

    def __delitem__(self, idx):
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len or idx + 1 > self._len:
            raise IndexError(f"list index out of range")
        if idx < 0:
            idx += self._len

        for i in range(idx, self._len-1):
            if i in self._data:
                del self._data[i]
            if i + 1 in self._data:
                self._data[i] = self._data[i+1]
        if self._len - 1 in self._data:
            del self._data[self._len-1]
        self._len -= 1

    def __len__(self):
        return self._len

    def __iter__(self):
        for i in range(self._len):
            yield self[i]

    def append(self, data):
        self[self._len] = data

    def extend(self, iterable):
        for value in iterable:
            self.append(value)

    def clear(self):
        self._data.clear()
        self._len = 0
