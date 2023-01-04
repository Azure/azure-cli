# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

import copy
import os
from argparse import Action
from collections import OrderedDict

from knack.log import get_logger

from azure.cli.core import azclierror
from ._base import AAZUndefined, AAZBlankArgValue
from ._help import AAZShowHelp
from ._utils import AAZShortHandSyntaxParser
from .exceptions import AAZInvalidShorthandSyntaxError, AAZInvalidValueError

logger = get_logger(__name__)

_ELEMENT_APPEND_KEY = "_+_"  # used for list append


class AAZArgActionOperations:
    """AAZArg operations container"""

    def __init__(self):
        self._ops = []

    def add(self, data, *keys):
        self._ops.append((keys, data))

    def apply(self, args, dest):
        for keys, data in self._ops:
            self._assign_data(args, data, dest, *keys)

    @staticmethod
    def _assign_data(args, data, dest, *keys):
        from ._field_value import AAZList
        arg = args
        key = dest
        i = 0
        while i < len(keys):
            arg = arg[key]
            key = keys[i]
            if key == _ELEMENT_APPEND_KEY:
                assert isinstance(arg, AAZList)
                key = len(arg)
            i += 1
        arg[key] = data


class AAZArgAction(Action):
    _schema = None

    _str_parser = AAZShortHandSyntaxParser()  # support to parse normal string or short hand syntax string

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(getattr(namespace, self.dest), AAZArgActionOperations):
            # overwrite existing namespace value which is not an instance of AAZArgActionOperations.
            # especially the default value of argument.
            setattr(namespace, self.dest, AAZArgActionOperations())
        dest_ops = getattr(namespace, self.dest)
        try:
            self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise azclierror.InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex
        except AAZShowHelp as aaz_help:
            # show help message
            aaz_help.keys = (option_string, *aaz_help.keys)
            self.show_aaz_help(parser, aaz_help)

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        raise NotImplementedError()

    @classmethod
    def format_data(cls, data):
        """format input data"""
        raise NotImplementedError()

    @staticmethod
    def show_aaz_help(parser, aaz_help):
        aaz_help.show()
        parser.exit()


class AAZSimpleTypeArgAction(AAZArgAction):

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None:
            data = AAZBlankArgValue  # use blank data when values string is None
        else:
            if isinstance(values, list):
                assert prefix_keys  # the values will be input as an list when parse singular option of a list argument
                if len(values) != 1:
                    raise AAZInvalidValueError(f"only support 1 value, got {len(values)}: {values}")
                values = values[0]

            if isinstance(values, str) and len(values) > 0:
                try:
                    data = cls.decode_str(values)
                except AAZShowHelp as aaz_help:
                    aaz_help.schema = cls._schema
                    raise aaz_help
            else:
                data = values
        data = cls.format_data(data)
        dest_ops.add(data, *prefix_keys)

    @classmethod
    def decode_str(cls, value):
        return cls._str_parser(value, is_simple=True)

    @classmethod
    def format_data(cls, data):
        if data == AAZBlankArgValue:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument value cannot be blank")
            data = copy.deepcopy(cls._schema._blank)

        if isinstance(data, str):
            # transfer string into correct data
            if cls._schema.enum:
                return cls._schema.enum[data]
            return cls._schema.DataType(data)   # str, int, float, boolean

        if isinstance(data, cls._schema.DataType):
            return data

        if data is None:
            if cls._schema._nullable:
                return data
            raise AAZInvalidValueError("field is not nullable")

        raise AAZInvalidValueError(f"{cls._schema.DataType} type value expected, got '{data}'({type(data)})")


class AAZCompoundTypeArgAction(AAZArgAction):  # pylint: disable=abstract-method

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument cannot be blank")
            dest_ops.add(copy.deepcopy(cls._schema._blank), *prefix_keys)
        else:
            assert isinstance(values, list)
            for _, key_parts, value in cls.decode_values(values):
                schema = cls._schema
                for k in key_parts:
                    schema = schema[k]  # pylint: disable=unsubscriptable-object
                action = schema._build_cmd_action()
                data = action.format_data(value)
                dest_ops.add(data, *prefix_keys, *key_parts)

    @classmethod
    def decode_values(cls, values):
        for v in values:
            key, key_parts, v = cls._str_parser.split_partial_value(v)
            v = cls._decode_value(key, key_parts, v)
            yield key, key_parts, v

    @classmethod
    def _decode_value(cls, key, key_items, value):  # pylint: disable=unused-argument
        from ._arg import AAZSimpleTypeArg
        from azure.cli.core.util import get_file_json, shell_safe_json_parse, get_file_yaml

        schema = cls._schema
        for item in key_items:
            schema = schema[item]  # pylint: disable=unsubscriptable-object

        if len(value) == 0:
            # the express "a=" will return the blank value of schema 'a'
            return AAZBlankArgValue

        try:
            if isinstance(schema, AAZSimpleTypeArg):
                # simple type
                v = cls._str_parser(value, is_simple=True)
            else:
                # compound type
                # read from file
                path = os.path.expanduser(value)
                if os.path.exists(path):
                    if path.endswith('.yml') or path.endswith('.yaml'):
                        # read from yaml file
                        v = get_file_yaml(path)
                    else:
                        # read from json file
                        v = get_file_json(path, preserve_order=True)
                else:
                    try:
                        v = cls._str_parser(value)
                    except AAZInvalidShorthandSyntaxError as shorthand_ex:
                        try:
                            v = shell_safe_json_parse(value, True)
                        except Exception as ex:
                            logger.debug(ex)  # log parse json failed expression
                            raise shorthand_ex  # raise shorthand syntax exception
        except AAZShowHelp as aaz_help:
            aaz_help.schema = cls._schema
            aaz_help.keys = (*key_items, *aaz_help.keys)
            raise aaz_help
        return v


class AAZObjectArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        if data == AAZBlankArgValue:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument value cannot be blank")
            data = copy.deepcopy(cls._schema._blank)

        if data is None:
            if cls._schema._nullable:
                return data
            raise AAZInvalidValueError("field is not nullable")

        if isinstance(data, dict):
            result = OrderedDict()
            for key, value in data.items():
                action = cls._schema[key]._build_cmd_action()  # pylint: disable=unsubscriptable-object
                try:
                    result[key] = action.format_data(value)
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid '{key}' : {ex}") from ex
            return result

        raise AAZInvalidValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZDictArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        if data == AAZBlankArgValue:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument value cannot be blank")
            data = copy.deepcopy(cls._schema._blank)

        if data is None:
            if cls._schema._nullable:
                return data
            raise AAZInvalidValueError("field is not nullable")

        if isinstance(data, dict):
            result = OrderedDict()
            action = cls._schema.Element._build_cmd_action()
            for key, value in data.items():
                try:
                    result[key] = action.format_data(value)
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid '{key}' : {ex}") from ex
            return result

        raise AAZInvalidValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZFreeFormDictArgAction(AAZSimpleTypeArgAction):

    @classmethod
    def decode_str(cls, value):
        from azure.cli.core.util import get_file_json, shell_safe_json_parse, get_file_yaml

        if len(value) == 0:
            # the express "a=" will return the blank value of schema 'a'
            return AAZBlankArgValue

        path = os.path.expanduser(value)
        if os.path.exists(path):
            if path.endswith('.yml') or path.endswith('.yaml'):
                # read from yaml file
                v = get_file_yaml(path)
            else:
                # read from json file
                v = get_file_json(path, preserve_order=True)
        else:
            try:
                v = shell_safe_json_parse(value, True)
            except Exception as ex:
                logger.debug(ex)  # log parse json failed expression
                raise
        return v

    @classmethod
    def format_data(cls, data):
        if data == AAZBlankArgValue:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument value cannot be blank")
            data = copy.deepcopy(cls._schema._blank)

        if isinstance(data, dict):
            return data

        if data is None:
            if cls._schema._nullable:
                return data
            raise AAZInvalidValueError("field is not nullable")

        raise AAZInvalidValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZListArgAction(AAZCompoundTypeArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(getattr(namespace, self.dest), AAZArgActionOperations):
            # overwrite existing namespace value which is not an instance of AAZArgActionOperations.
            # especially the default value of argument.
            setattr(namespace, self.dest, AAZArgActionOperations())
        dest_ops = getattr(namespace, self.dest)
        try:
            if self._schema.singular_options and option_string in self._schema.singular_options:
                # if singular option is used then parsed values by element action
                action = self._schema.Element._build_cmd_action()
                action.setup_operations(dest_ops, values, prefix_keys=[_ELEMENT_APPEND_KEY])
            else:
                self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise azclierror.InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex
        except AAZShowHelp as aaz_help:
            aaz_help.keys = (option_string, *aaz_help.keys)
            self.show_aaz_help(parser, aaz_help)

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument cannot be blank")
            dest_ops.add(copy.deepcopy(cls._schema._blank), *prefix_keys)
        else:
            assert isinstance(values, list)
            ops = []
            try:
                # Standard Expression
                for key, key_parts, value in cls.decode_values(values):
                    schema = cls._schema
                    for k in key_parts:
                        schema = schema[k]  # pylint: disable=unsubscriptable-object
                    action = schema._build_cmd_action()
                    data = action.format_data(value)
                    ops.append((key_parts, data))
            except AAZShowHelp as aaz_help:
                raise aaz_help
            except Exception as ex:  # pylint: disable=broad-except
                # This part of logic is to support Separate Elements Expression which is widely used in current command,
                # such as:
                #       --args val1 val2 val3.
                # The standard expression of it should be:
                #       --args [val1,val2,val3]

                for value in values:
                    key, _, _ = cls._str_parser.split_partial_value(value)
                    if key is not None:
                        # key should always be None
                        raise ex

                element_action = cls._schema.Element._build_cmd_action()
                if not issubclass(element_action, AAZSimpleTypeArgAction):
                    # Separate Elements Expression only supported for simple type element array
                    raise ex

                # dest_ops
                try:
                    element_ops = AAZArgActionOperations()
                    for value in values:
                        element_action.setup_operations(element_ops, value, prefix_keys=[_ELEMENT_APPEND_KEY])
                except AAZShowHelp as aaz_help:
                    aaz_help.schema = cls._schema
                    aaz_help.keys = (0, *aaz_help.keys)
                    raise aaz_help

                elements = []
                for _, data in element_ops._ops:
                    elements.append(data)
                ops = [([], elements)]

            for key_parts, data in ops:
                dest_ops.add(data, *prefix_keys, *key_parts)

    @classmethod
    def format_data(cls, data):
        if data == AAZBlankArgValue:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument value cannot be blank")
            data = copy.deepcopy(cls._schema._blank)

        if data is None:
            if cls._schema._nullable:
                return data
            raise AAZInvalidValueError("field is not nullable")

        if isinstance(data, list):
            result = []
            action = cls._schema.Element._build_cmd_action()
            for idx, value in enumerate(data):
                try:
                    result.append(action.format_data(value))
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid at [{idx}] : {ex}") from ex
            return result

        raise AAZInvalidValueError(f"list type value expected, got '{data}'({type(data)})")


class AAZGenericUpdateAction(Action):  # pylint: disable=too-few-public-methods
    DEST = 'generic_update_args'
    ACTION_NAME = None

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, self.DEST, None):
            setattr(namespace, self.DEST, {"actions": []})
        getattr(namespace, self.DEST)["actions"].append((self.ACTION_NAME or option_string, values))


class AAZGenericUpdateForceStringAction(AAZSimpleTypeArgAction):
    DEST = 'generic_update_args'

    def __call__(self, parser, namespace, values, option_string=None):
        dest_ops = AAZArgActionOperations()
        try:
            self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise azclierror.InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex
        except AAZShowHelp as aaz_help:
            # show help message
            aaz_help.keys = (option_string, *aaz_help.keys)
            self.show_aaz_help(parser, aaz_help)

        if not getattr(namespace, self.DEST, None):
            setattr(namespace, self.DEST, {"actions": []})
        dest_ops.apply(getattr(namespace, self.DEST), dest='force_string')
