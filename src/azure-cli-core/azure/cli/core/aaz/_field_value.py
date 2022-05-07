from ._base import AAZBaseValue, AAZValuePatch, AAZUndefined


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

    def to_serialized_data(self):
        return self._data


class AAZObject(AAZBaseValue):

    def __init__(self, schema, data):
        super().__init__(schema, data)
        assert isinstance(self._data, dict)

    def __getitem__(self, key):
        attr_schema = self._schema[key]
        name = self._schema.get_attr_name(key)
        if name not in self._data:
            # is key is not set before, then create a patch, and value updated in patch will be partial updated
            self._data[name] = AAZValuePatch.build(attr_schema)
        return attr_schema.ValueCls(attr_schema, self._data[name])

    def __setitem__(self, key, data):
        assert not key.startswith('_')
        attr_schema = self._schema[key]
        name = self._schema.get_attr_name(key)
        self._data[name] = attr_schema.process_data(data, key=name)

    def __delitem__(self, key):
        name = self._schema.get_attr_name(key)
        if name in self._data:
            del self._data[name]
        elif name is None:
            raise KeyError(f"Attribute {key} not exist")

    def __getattr__(self, key) -> AAZBaseValue:
        return self[key]

    def __setattr__(self, key, data):
        if key.startswith('_'):
            self.__dict__[key] = data
        else:
            self[key] = data

    def __delattr__(self, key):
        if key.startswith('_'):
            del self.__dict__[key]
        else:
            del self[key]

    def to_serialized_data(self):
        results = {}
        for name, field_schema in self._schema._fields.items():
            v = self[name].to_serialized_data()
            if v == AAZUndefined:
                continue
            if field_schema._serialized_name:
                name = field_schema._serialized_name
            results[name] = v
        if not results and self._is_patch:
            return AAZUndefined
        return results


class AAZDict(AAZBaseValue):

    def __init__(self, schema, data):
        from ._field_type import AAZDictType
        assert isinstance(schema, AAZDictType)
        super().__init__(schema, data)
        assert isinstance(self._data, dict)

    def __getitem__(self, key) -> AAZBaseValue:
        item_schema = self._schema.Element
        if key not in self._data:
            self._data[key] = AAZValuePatch.build(item_schema)
        return item_schema.ValueCls(item_schema, self._data[key])

    def __setitem__(self, key, data):
        item_schema = self._schema.Element
        self._data[key] = item_schema.process_data(data, key=key)

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
        for key in self._data:
            yield self[key]

    def items(self):
        for key in self._data:
            yield key, self[key]

    def to_serialized_data(self):
        results = {}
        for key, v in self.items():
            v = v.to_serialized_data()
            if v == AAZUndefined:
                continue
            results[key] = v
        if not results and self._is_patch:
            return AAZUndefined
        return results


class AAZList(AAZBaseValue):

    def __init__(self, schema, data):
        from ._field_type import AAZListType
        assert isinstance(schema, AAZListType)
        super().__init__(schema, data)
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

        item_schema = self._schema.Element
        if idx not in self._data:
            self._data[idx] = AAZValuePatch.build(item_schema)

            if idx + 1 > self._len:
                self._len = idx + 1

        return item_schema.ValueCls(item_schema, self._data[idx])

    def __setitem__(self, idx, data):
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len:
            raise IndexError(f"list index out of range")
        if idx < 0:
            idx += self._len

        schema = self._schema.Element
        self._data[idx] = schema.process_data(data, key=idx)

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

    def to_serialized_data(self):
        results = []
        for v in self:
            v = v.to_serialized_data()
            results.append(v)
        if not results and self._is_patch:
            return AAZUndefined
        return results
