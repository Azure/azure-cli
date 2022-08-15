# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._base import AAZBaseValue, AAZUndefined
from ._field_value import AAZSimpleValue, AAZDict, AAZList, AAZObject
from ._field_type import AAZObjectType
from ._arg_browser import AAZArgBrowser

# pylint: disable=protected-access, too-many-nested-blocks, too-many-return-statements


class AAZContentBuilder:
    """Content Builder is used to build operation content"""

    def __init__(self, values, args, is_discriminated=False):
        assert len(args) > 0
        for arg in args:
            assert isinstance(arg, AAZArgBrowser)
        assert len(values) == len(args)
        for value in values:
            assert isinstance(value, AAZBaseValue)
        self._values = values
        self._args = args
        self._is_discriminated = is_discriminated

        self._sub_prop_builders = {}
        self._sub_elements_builder = None
        self._discriminator_prop_name = None
        self._discriminator_builders = {}

    def set_const(self, prop_name, prop_value, typ, arg_key=None, typ_kwargs=None):
        """Set const value for a property"""
        for value, arg in zip(self._values, self._args):
            schema = value._schema
            if self._is_discriminated:
                assert isinstance(schema, AAZObjectType)
                # use discriminator schema
                schema = schema.get_discriminator(value)

            sub_arg = arg.get_prop(arg_key)
            if sub_arg is not None and sub_arg.data != AAZUndefined:
                if schema.get_attr_name(prop_name) is None:
                    schema[prop_name] = typ(**typ_kwargs) if typ_kwargs else typ()
                else:
                    assert isinstance(schema[prop_name], typ)
                value[prop_name] = prop_value

    def set_prop(self, prop_name, typ, arg_key=None, typ_kwargs=None):
        """Set property value from argument"""
        sub_values = []
        sub_args = []
        for value, arg in zip(self._values, self._args):
            schema = value._schema
            if self._is_discriminated:
                assert isinstance(schema, AAZObjectType)
                # use discriminator schema
                schema = schema.get_discriminator(value)

            sub_arg = arg.get_prop(arg_key)
            if sub_arg is not None and sub_arg.data != AAZUndefined:
                if schema.get_attr_name(prop_name) is None:
                    schema[prop_name] = typ(**typ_kwargs) if typ_kwargs else typ()
                else:
                    assert isinstance(schema[prop_name], typ)
                if not sub_arg.is_patch and arg_key:
                    if isinstance(value[prop_name], AAZSimpleValue):
                        value[prop_name] = sub_arg.data
                    elif isinstance(value[prop_name], AAZList):
                        if sub_arg.data is None:
                            value[prop_name] = None
                        else:
                            value[prop_name] = []
                    elif isinstance(value[prop_name], (AAZDict, AAZObject)):
                        if sub_arg.data is None:
                            value[prop_name] = None
                        else:
                            value[prop_name] = {}
                    else:
                        raise NotImplementedError()
                sub_values.append(value[prop_name])
                sub_args.append(sub_arg)

        if sub_values:
            self._sub_prop_builders[prop_name] = AAZContentBuilder(sub_values, sub_args)
            return self._sub_prop_builders[prop_name]

        return None

    def set_elements(self, typ, arg_key=None, typ_kwargs=None):
        """Set elements of dict or list from argument"""
        sub_values = []
        sub_args = []
        for value, arg in zip(self._values, self._args):
            schema = value._schema
            if schema._element is None:
                schema.Element = typ(**typ_kwargs) if typ_kwargs else typ()
            else:
                assert isinstance(schema.Element, typ)
            if isinstance(value, (AAZDict, AAZList)):
                for key, sub_arg in arg.get_elements():
                    if sub_arg is not None and sub_arg.data != AAZUndefined:
                        sub_arg = sub_arg.get_prop(arg_key)

                    if sub_arg is not None and sub_arg.data != AAZUndefined:
                        if not sub_arg.is_patch and arg_key:
                            if isinstance(value[key], AAZSimpleValue):
                                value[key] = sub_arg.data
                            elif isinstance(value[key], AAZList):
                                if sub_arg.data is None:
                                    value[key] = None
                                else:
                                    value[key] = []
                            elif isinstance(value[key], (AAZDict, AAZObject)):
                                if sub_arg.data is None:
                                    value[key] = None
                                else:
                                    value[key] = {}
                            else:
                                raise NotImplementedError()
                        sub_values.append(value[key])
                        sub_args.append(sub_arg)
            else:
                raise NotImplementedError()

        if sub_values:
            self._sub_elements_builder = AAZContentBuilder(sub_values, sub_args)
            return self._sub_elements_builder

        return None

    def discriminate_by(self, prop_name, prop_value):
        """discriminate object by a specify property"""
        if self._discriminator_prop_name is None:
            self._discriminator_prop_name = prop_name
        if self._discriminator_prop_name != prop_name:
            raise KeyError(f"Conflict discriminator key: {self._discriminator_prop_name} and {prop_name}")
        disc_values = []
        disc_args = []
        for value, arg in zip(self._values, self._args):
            if not isinstance(value, (AAZObject,)):
                raise NotImplementedError()
            schema = value._schema
            schema.discriminate_by(prop_name, prop_value)
            if value[prop_name] == prop_value:
                disc_values.append(value)
                disc_args.append(arg)
        if disc_values:
            self._discriminator_builders[prop_value] = AAZContentBuilder(disc_values, disc_args, is_discriminated=True)
        else:
            self._discriminator_builders[prop_value] = None

        return self._discriminator_builders[prop_value]

    def get(self, key):
        """Get sub builder by key"""
        if not key or key == '.':
            return self
        parts = [part for part in key.replace('[', '.[').replace('{', '.{').split('.') if part]

        return self._get(*parts)

    def _get(self, *key_parts):
        if not key_parts:
            return self
        if key_parts[0] == '[]':
            # list elements builder
            if not self._sub_elements_builder:
                return None
            sub_builder = self._sub_elements_builder
        elif key_parts[0] == '{}':
            # dict elements builder
            if not self._sub_elements_builder:
                return None
            sub_builder = self._sub_elements_builder
        elif key_parts[0].startswith('{'):
            # discriminator
            key, value = key_parts[0][1:-1].split(":")
            if key != self._discriminator_prop_name:
                return None
            sub_builder = self._discriminator_builders.get(value, None)
            if not sub_builder:
                return None
        else:
            if key_parts[0] not in self._sub_prop_builders:
                return None
            sub_builder = self._sub_prop_builders[key_parts[0]]
        return sub_builder._get(*key_parts[1:])
