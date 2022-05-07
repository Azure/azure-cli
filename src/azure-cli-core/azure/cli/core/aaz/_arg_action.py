import re
import os
from argparse import Action
from azure.cli.core import azclierror
from collections import OrderedDict
from ._utils import AAZShortHandSyntaxParser, AAZInvalidShorthandSyntaxError
from knack.log import get_logger

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
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, AAZArgActionOperations())
        dest_ops = getattr(namespace, self.dest)
        try:
            self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise azclierror.InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=[]):
        raise NotImplementedError()

    @classmethod
    def format_data(cls, data):
        """format input data"""
        raise NotImplementedError()


class AAZSimpleTypeArgAction(AAZArgAction):

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=[]):
        if values is None:
            data = cls._schema._blank
        else:
            if isinstance(values, list):
                assert prefix_keys  # the values will be input as an list when parse singular option of a list argument
                if len(values) != 1:
                    raise ValueError(f"only support 1 value, got {len(values)}: {values}")
                values = values[0]

            if isinstance(values, str):
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
        elif isinstance(data, cls._schema.DataType) or data is None:
            return data
        else:
            raise ValueError(f"{cls._schema.DataType} type value expected, got '{data}'({type(data)})")


class AAZCompoundTypeArgAction(AAZArgAction):

    key_pattern = re.compile(
        r'^(((\[[0-9]+])|(([a-zA-Z0-9_\-]+)(\[[0-9]+])?))(\.([a-zA-Z0-9_\-]+)(\[[0-9]+])?)*)=(.*)$'
    )

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=[]):
        if values is None:
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
            assert isinstance(v, str)
            match = cls.key_pattern.fullmatch(v)
            if not match:
                key = None
            else:
                key = match[1]
                v = match[len(match.regs) - 1]
            key_parts = cls._split_key(key)
            v = cls._decode_value(key_parts, v)
            yield key, key_parts, v

    @staticmethod
    def _split_key(key):
        if key is None:
            return tuple()
        key_items = []
        for part in key.replace('[', '.[').split('.'):
            if part.startswith('['):
                assert part.endswith(']')
                part = int(part[1:-1])
            key_items.append(part)
        return tuple(key_items)

    @classmethod
    def _decode_value(cls, key_items, value):
        from ._arg import AAZSimpleTypeArg
        from azure.cli.core.util import get_file_json, shell_safe_json_parse

        schema = cls._schema
        for item in key_items:
            schema = schema[item]

        if len(value) == 0:
            # the express "a=" will return the blank value of schema a
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
                        logger.debug(ex)    # log parse json failed expression
                        raise shorthand_ex  # raise shorthand syntax exception
        return v


class AAZObjectArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        if data is None:
            return None
        elif isinstance(data, dict):
            result = OrderedDict()
            for key, value in data.items():
                action = cls._schema[key]._build_cmd_action()
                result[key] = action.format_data(value)
            return result
        else:
            raise ValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZDictArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        if data is None:
            return None
        elif isinstance(data, dict):
            result = OrderedDict()
            action = cls._schema.Element._build_cmd_action()
            for key, value in data.items():
                result[key] = action.format_data(value)
            return result
        else:
            raise ValueError(f"dict type value expected, got '{data}'({type(data)})")


class AAZListArgAction(AAZCompoundTypeArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, AAZArgActionOperations())
        dest_ops = getattr(namespace, self.dest)
        try:
            if self._schema.singular_options and option_string in self._schema.singular_options:
                # if singular option is used then parsed values by element action
                action =self._schema.Element._build_cmd_action()
                action.setup_operations(dest_ops, values, prefix_keys=[_ELEMENT_APPEND_KEY])
            else:
                self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise azclierror.InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=[]):
        if values is None:
            dest_ops.add(cls._schema._blank, *prefix_keys)
        else:
            assert isinstance(values, list)
            inputs = [*cls.decode_values(values)]
            ops = []
            try:
                # Standard Expression
                for key, key_parts, value in inputs:
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

                element_action = cls._schema.Element._build_cmd_action()
                if not issubclass(element_action, AAZSimpleTypeArgAction):
                    # Separate Elements Expression only supported for simple type element array
                    raise ex

                elements = []
                for _, _, value in inputs:
                    elements.append(element_action.format_data(value))
                ops = [([], elements)]

            for key_parts, data in ops:
                dest_ops.add(data, *prefix_keys, *key_parts)

    @classmethod
    def format_data(cls, data):
        if data is None:
            return None
        elif isinstance(data, list):
            result = []
            action = cls._schema.Element._build_cmd_action()
            for idx, value in enumerate(data):
                result.append(action.format_data(value))
            return result
        else:
            raise ValueError(f"list type value expected, got '{data}'({type(data)})")
