import os
import re
from argparse import Action
from collections import OrderedDict

from azure.cli.core import azclierror
from knack.log import get_logger

from ._base import AAZUndefined
from ._utils import AAZShortHandSyntaxParser
from .exceptions import AAZInvalidShorthandSyntaxError, AAZInvalidValueError

logger = get_logger(__name__)

_ELEMENT_APPEND_KEY = "_+_"  # used for list append


class AAZArgActionOperations:

    def __init__(self):
        self._ops = []

    def add(self, data, *keys):
        self._ops.append((keys, data))

    def apply(self, args, dest):
        for keys, data in self._ops:
            self._assign_data(args, data, dest, *keys)

    def _assign_data(self, args, data, dest, *keys):
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

    _str_parser = AAZShortHandSyntaxParser()

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None or getattr(namespace, self.dest) == AAZUndefined:
            setattr(namespace, self.dest, AAZArgActionOperations())
        dest_ops = getattr(namespace, self.dest)
        try:
            self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise azclierror.InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        raise NotImplementedError()

    @classmethod
    def format_data(cls, data):
        """format input data"""
        raise NotImplementedError()


class AAZSimpleTypeArgAction(AAZArgAction):

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument cannot be blank")
            data = cls._schema._blank
        else:
            if isinstance(values, list):
                assert prefix_keys  # the values will be input as an list when parse singular option of a list argument
                if len(values) != 1:
                    raise AAZInvalidValueError(f"only support 1 value, got {len(values)}: {values}")
                values = values[0]

            if isinstance(values, str) and len(values) > 0:
                data = cls._str_parser(values, is_simple=True)
            else:
                data = values
            data = cls.format_data(data)
        dest_ops.add(data, *prefix_keys)

    @classmethod
    def format_data(cls, data):
        if isinstance(data, str):
            if cls._schema.enum:
                return cls._schema.enum[data]
            else:
                return cls._schema.DataType(data)
        elif isinstance(data, cls._schema.DataType):
            return data
        elif data is None:
            if cls._schema._nullable:
                return data
            else:
                raise AAZInvalidValueError(f"is not nullable")
        else:
            raise AAZInvalidValueError(f"{cls._schema.DataType} type value expected, got '{data}'({type(data)})")


class AAZCompoundTypeArgAction(AAZArgAction):
    key_pattern = re.compile(
        r'^(((\[-?[0-9]+])|(([a-zA-Z0-9_\-]+)(\[-?[0-9]+])?))(\.([a-zA-Z0-9_\-]+)(\[-?[0-9]+])?)*)=(.*)$'
    )

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument cannot be blank")
            dest_ops.add(cls._schema._blank, *prefix_keys)
        else:
            assert isinstance(values, list)
            for key, key_parts, value in cls.decode_values(values):
                schema = cls._schema
                for k in key_parts:
                    schema = schema[k]
                action = schema._build_cmd_action()
                data = action.format_data(value)
                dest_ops.add(data, *prefix_keys, *key_parts)

    @classmethod
    def decode_values(cls, values):
        for v in values:
            key, key_parts, v = cls._split_value_str(v)
            v = cls._decode_value(key, key_parts, v)
            yield key, key_parts, v

    @classmethod
    def _split_value_str(cls, v):
        assert isinstance(v, str)
        match = cls.key_pattern.fullmatch(v)
        if not match:
            key = None
        else:
            key = match[1]
            v = match[len(match.regs) - 1]
        key_parts = cls._split_key(key)
        return key, key_parts, v

    @staticmethod
    def _split_key(key):
        if key is None:
            return tuple()
        key_items = []
        key = key[0] + key[1:].replace('[', '.[')  # transform 'ab[2]' to 'ab.[2]', keep '[1]' unchanged
        for part in key.split('.'):
            assert part
            if part.startswith('['):
                assert part.endswith(']')
                part = int(part[1:-1])
            key_items.append(part)
        return tuple(key_items)

    @classmethod
    def _decode_value(cls, key, key_items, value):
        from ._arg import AAZSimpleTypeArg
        from azure.cli.core.util import get_file_json, shell_safe_json_parse

        schema = cls._schema
        for item in key_items:
            schema = schema[item]

        if len(value) == 0:
            # the express "a=" will return the blank value of schema 'a'
            return schema._blank

        if isinstance(schema, AAZSimpleTypeArg):
            # simple type
            v = cls._str_parser(value, is_simple=True)
        else:
            # compound type
            # read from file
            path = os.path.expanduser(value)
            if os.path.exists(path):
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
        return v


class AAZObjectArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        if data is None:
            if cls._schema._nullable:
                return data
            else:
                raise AAZInvalidValueError(f"is not nullable")
        elif isinstance(data, dict):
            result = OrderedDict()
            for key, value in data.items():
                action = cls._schema[key]._build_cmd_action()
                try:
                    result[key] = action.format_data(value)
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid '{key}' : {ex}") from ex
            return result
        else:
            raise AAZInvalidValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZDictArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        if data is None:
            if cls._schema._nullable:
                return data
            else:
                raise AAZInvalidValueError(f"is not nullable")
        elif isinstance(data, dict):
            result = OrderedDict()
            action = cls._schema.Element._build_cmd_action()
            for key, value in data.items():
                try:
                    result[key] = action.format_data(value)
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid '{key}' : {ex}") from ex
            return result
        else:
            raise AAZInvalidValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZListArgAction(AAZCompoundTypeArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None or getattr(namespace, self.dest) == AAZUndefined:
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

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument cannot be blank")
            dest_ops.add(cls._schema._blank, *prefix_keys)
        else:
            assert isinstance(values, list)
            ops = []
            try:
                # Standard Expression
                for key, key_parts, value in cls.decode_values(values):
                    schema = cls._schema
                    for k in key_parts:
                        schema = schema[k]
                    action = schema._build_cmd_action()
                    data = action.format_data(value)
                    ops.append((key_parts, data))
            except Exception as ex:
                # This part of logic is to support Separate Elements Expression which is widely used in current command,
                # such as:
                #       --args val1 val2 val3.
                # The standard expression of it should be:
                #       --args [val1,val2,val3]

                for value in values:
                    key, _, _ = cls._split_value_str(value)
                    if key is not None:
                        # key should always be None
                        raise ex

                element_action = cls._schema.Element._build_cmd_action()
                if not issubclass(element_action, AAZSimpleTypeArgAction):
                    # Separate Elements Expression only supported for simple type element array
                    raise ex

                # dest_ops
                element_ops = AAZArgActionOperations()
                for value in values:
                    element_action.setup_operations(element_ops, value, prefix_keys=[_ELEMENT_APPEND_KEY])

                elements = []
                for _, data in element_ops._ops:
                    elements.append(data)
                ops = [([], elements)]

            for key_parts, data in ops:
                dest_ops.add(data, *prefix_keys, *key_parts)

    @classmethod
    def format_data(cls, data):
        if data is None:
            if cls._schema._nullable:
                return data
            else:
                raise AAZInvalidValueError(f"is not nullable")
        elif isinstance(data, list):
            result = []
            action = cls._schema.Element._build_cmd_action()
            for idx, value in enumerate(data):
                try:
                    result.append(action.format_data(value))
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid at [{idx}] : {ex}") from ex
            return result
        else:
            raise AAZInvalidValueError(f"list type value expected, got '{data}'({type(data)})")
