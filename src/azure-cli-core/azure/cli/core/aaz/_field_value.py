# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access
from ._base import AAZBaseValue, AAZValuePatch, AAZUndefined
import abc


class AAZSimpleValue(AAZBaseValue):
    """ Simple build-in values such as int, float, boolean and string"""

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def __eq__(self, other):
        if isinstance(other, AAZBaseValue):
            other = other._data
        return self._data == other

    def __ne__(self, other):
        return not self == other

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

    def to_serialized_data(self, processor=None, **kwargs):
        result = self._data
        if processor:
            result = processor(self._schema, result)
        return result


class AAZAnyValue(AAZSimpleValue):  # pylint: disable=too-few-public-methods
    # TODO: may need to override the __getitem__, __setitem__, __delitem__, __getattr__, __setattr__, __delattr__,
    pass


class AAZObject(AAZBaseValue):

    def __init__(self, schema, data):
        super().__init__(schema, data)
        assert isinstance(self._data, dict) or self._data is None or self._data == AAZUndefined

    def __getitem__(self, key):
        attr_schema, name = self._get_attr_schema_and_name(key)

        if name not in self._data:
            # is key is not set before, then create a patch, and value updated in patch will be partial updated
            self._data[name] = AAZValuePatch.build(attr_schema)
        return attr_schema._ValueCls(attr_schema, self._data[name])  # return as AAZValue

    def __setitem__(self, key, data):
        assert not key.startswith('_')
        attr_schema, name = self._get_attr_schema_and_name(key)
        self._data[name] = attr_schema.process_data(data, key=name)

    def __delitem__(self, key):
        _, name = self._get_attr_schema_and_name(key)
        if name in self._data:
            del self._data[name]

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

    def __eq__(self, other):
        if isinstance(other, AAZBaseValue):
            return self._data == other._data

        # other is buld-in type value
        if other is None:
            return self._data is None

        if (not isinstance(other, dict)) or len(other) != len(self._data):
            return False

        for key in other.keys():
            if other[key] != self[key]:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def to_serialized_data(self, processor=None, **kwargs):
        if self._data == AAZUndefined:
            result = AAZUndefined
        elif self._data is None:
            result = None
        else:
            result = {}
            schemas = [self._schema]

            disc_schema = self._schema.get_discriminator(self._data)
            if disc_schema:
                schemas.append(disc_schema)

            for schema in schemas:
                for name, field_schema in schema._fields.items():
                    if name in self._data:
                        v = self[name].to_serialized_data(processor=processor, **kwargs)
                        if v == AAZUndefined:
                            continue
                        if field_schema._serialized_name:   # pylint: disable=protected-access
                            name = field_schema._serialized_name  # pylint: disable=protected-access
                        result[name] = v

        if not result and self._is_patch:
            result = AAZUndefined

        if processor:
            result = processor(self._schema, result)
        return result

    def _get_attr_schema_and_name(self, key):
        """ get attribute schema and it's name based in key """
        disc_schema = self._schema.get_discriminator(self._data)
        if not hasattr(self._schema, key) and disc_schema is not None:
            attr_schema = disc_schema[key]  # will raise error if key not exist
            schema = disc_schema
        else:
            attr_schema = self._schema[key]  # will raise error if key not exist
            schema = self._schema
        name = schema.get_attr_name(key)
        assert name is not None
        return attr_schema, name


class AAZBaseDictValue(AAZBaseValue):

    def __init__(self, schema, data):
        super().__init__(schema, data)
        assert isinstance(self._data, dict) or self._data is None or self._data == AAZUndefined

    @abc.abstractmethod
    def __getitem__(self, key) -> AAZBaseValue:
        raise NotImplementedError()

    @abc.abstractmethod
    def __setitem__(self, key, data):
        raise NotImplementedError()

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        yield from self._data

    def __eq__(self, other):
        if isinstance(other, AAZBaseValue):
            return self._data == other._data

        # other is buld-in type value
        if other is None:
            return self._data is None

        if (not isinstance(other, dict)) or len(other) != len(self._data):
            return False

        for key, _ in other.items():
            if other[key] != self[key]:
                return False
        return True

    def __ne__(self, other):
        return not self == other

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


class AAZDict(AAZBaseDictValue):

    def __init__(self, schema, data):
        from ._field_type import AAZDictType
        assert isinstance(schema, AAZDictType)
        super().__init__(schema, data)

    def __getitem__(self, key) -> AAZBaseValue:
        item_schema = self._schema[key]
        if key not in self._data:
            self._data[key] = AAZValuePatch.build(item_schema)
        return item_schema._ValueCls(item_schema, self._data[key])  # return as AAZValue

    def __setitem__(self, key, data):
        try:
            item_schema = self._schema[key]
        except AttributeError:
            # ignore undefined element
            return
        self._data[key] = item_schema.process_data(data, key=key)

    def to_serialized_data(self, processor=None, **kwargs):
        if self._data == AAZUndefined:
            result = AAZUndefined
        elif self._data is None:
            result = None
        else:
            result = {}
            for key, v in self.items():
                v = v.to_serialized_data(processor=processor, **kwargs)
                if v == AAZUndefined:
                    continue
                result[key] = v

        if not result and self._is_patch:
            result = AAZUndefined

        if processor:
            result = processor(self._schema, result)
        return result


class AAZFreeFormDict(AAZDict):

    def __init__(self, schema, data):
        from ._field_type import AAZFreeFormDictType
        assert isinstance(schema, AAZFreeFormDictType)
        super().__init__(schema, data)


class AAZList(AAZBaseValue):

    def __init__(self, schema, data):
        from ._field_type import AAZListType
        assert isinstance(schema, AAZListType)
        super().__init__(schema, data)
        assert isinstance(self._data, dict) or self._data is None or self._data == AAZUndefined  # the key is the idx
        self._len = 0
        if self._data is not None and self._data != AAZUndefined:
            for idx in self._data:
                self._len = max(self._len, idx + 1)

    def __getitem__(self, idx) -> AAZBaseValue:
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len:
            raise IndexError("list index out of range")
        if idx < 0:
            idx += self._len

        item_schema = self._schema.Element
        if idx not in self._data:
            self._data[idx] = AAZValuePatch.build(item_schema)

            self._len = max(self._len, idx + 1)

        return item_schema._ValueCls(item_schema, self._data[idx])

    def __setitem__(self, idx, data):
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len:
            raise IndexError("list index out of range")
        if idx < 0:
            idx += self._len

        try:
            item_schema = self._schema.Element
        except AttributeError:
            # ignore undefined element
            return

        self._data[idx] = item_schema.process_data(data, key=idx)

        self._len = max(self._len, idx + 1)

    def __delitem__(self, idx):
        if not isinstance(idx, int):
            raise IndexError(f"list indices must be integers, not {type(idx)}")
        if idx < -self._len or idx + 1 > self._len:
            raise IndexError("list index out of range")
        if idx < 0:
            idx += self._len

        for i in range(idx, self._len - 1):
            if i in self._data:
                del self._data[i]
            if i + 1 in self._data:
                self._data[i] = self._data[i + 1]

        if self._len - 1 in self._data:
            del self._data[self._len - 1]
        self._len -= 1

    def __len__(self):
        return self._len

    def __iter__(self):
        for i in range(self._len):
            yield self[i]

    def __eq__(self, other):
        if isinstance(other, AAZBaseValue):
            return self._data == other._data

        # other is buld-in type value
        if other is None:
            return self._data is None

        if (not isinstance(other, list)) or len(other) != self._len:
            return False

        for idx, v in enumerate(other):
            if self[idx] != v:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def append(self, data):
        self[self._len] = data

    def extend(self, iterable):
        for value in iterable:
            self.append(value)

    def clear(self):
        self._data.clear()
        self._len = 0

    def to_serialized_data(self, processor=None, keep_undefined_in_list=False,  # pylint: disable=arguments-differ
                           **kwargs):
        if self._data == AAZUndefined:
            result = AAZUndefined
        elif self._data is None:
            result = None
        else:
            result = []
            has_valid = False
            for v in self:
                v = v.to_serialized_data(
                    processor=processor, keep_undefined_in_list=keep_undefined_in_list, **kwargs)
                if v == AAZUndefined and not keep_undefined_in_list:
                    # When AAZUndefined is ignore it, the index of the following value will be changed.
                    continue
                if v != AAZUndefined:
                    has_valid = True
                result.append(v)
            if not has_valid:
                # when elements are all undefined, the result will be empty.
                result = []

        if not result and self._is_patch:
            result = AAZUndefined

        if processor:
            result = processor(self._schema, result)
        return result


class AAZIdentityObject(AAZObject):  # pylint: disable=too-few-public-methods
    def to_serialized_data(self, processor=None, **kwargs):
        calculate_data = {}
        if self._data == AAZUndefined:
            result = AAZUndefined

        elif self._data is None:
            result = None

        else:
            result = {}
            schema = self._schema

            for name, field_schema in schema._fields.items():
                if name in self._data:
                    v = self[name].to_serialized_data(processor=processor, **kwargs)
                    if v == AAZUndefined:
                        continue

                    if field_schema._serialized_name:
                        name = field_schema._serialized_name

                    if name in {"userAssigned", "systemAssigned"}:
                        calculate_data[name] = v
                        calculate_data["action"] = field_schema._flags.get("action", None)  # no action in GET operation

                    else:
                        result[name] = v

        result = self._build_identity(calculate_data, result)

        if not result and calculate_data.get("action", None) == "remove":
            result = {"type": "None"}  # empty identity

        if not result and self._is_patch:
            result = AAZUndefined

        if processor:
            result = processor(self._schema, result)

        return result

    def _build_identity(self, calculate_data, result):
        action = calculate_data.get("action", None)
        if not action:
            return result

        user_assigned = calculate_data.get("userAssigned", None)
        system_assigned = calculate_data.get("systemAssigned", None)

        identities = set(result.pop("userAssignedIdentities", {}).keys())
        has_system_identity = "systemassigned" in result.pop("type", "").lower()

        if action == "remove":
            if user_assigned is not None:
                if len(user_assigned) > 1:  # remove each
                    identities -= set(user_assigned)

                else:  # remove all
                    identities = {}

            if identities:
                result["userAssignedIdentities"] = {k: {} for k in identities}
                if system_assigned or not has_system_identity:
                    result["type"] = "UserAssigned"

                else:
                    result["type"] = "SystemAssigned,UserAssigned"

            elif not system_assigned and has_system_identity:
                result["type"] = "SystemAssigned"

        else:  # assign or create
            if user_assigned:
                identities |= set(user_assigned)

            if identities:
                result["userAssignedIdentities"] = {k: {} for k in identities}
                if system_assigned or has_system_identity:
                    result["type"] = "SystemAssigned,UserAssigned"

                else:
                    result["type"] = "UserAssigned"

            elif system_assigned or has_system_identity:
                result["type"] = "SystemAssigned"

        return result
