import re
import os
from argparse import Action, ArgumentTypeError
from azure.cli.core import azclierror
from collections import OrderedDict
from ._utils import AAZShortHandSyntaxParser
from knack.log import get_logger

logger = get_logger(__name__)


class AAZArgAction(Action):

    _schema = None

    _str_parser = AAZShortHandSyntaxParser()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def format_data(cls, data):
        """format input data"""
        raise NotImplementedError()


class AAZArgActionOperations:

    def apply(self, args, dest):
        raise NotImplementedError()


class AAZSimpleTypeArgAction(AAZArgAction):

    class Operations(AAZArgActionOperations):

        def __init__(self, data):
            self._data = data

        def apply(self, args, dest):
            args[dest] = self._data

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            data = self._schema._blank
        else:
            if isinstance(values, str):
                data = self._str_parser(values, is_simple=True)
            else:
                data = values
            data = self.format_data(data)
        op = self.Operations(data)
        setattr(namespace, self.dest, op)

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
            raise ArgumentTypeError(f"{cls._schema.DataType} type value expected, got '{data}'({type(data)})")


class AAZCompoundTypeArgAction(AAZArgAction):

    class Operations(AAZArgActionOperations):

        def __init__(self):
            self._ops = []

        def add(self, key_parts, data):
            self._ops.append((key_parts, data))

        def apply(self, args, dest):
            for key_parts, data in self._ops:
                arg = args
                key = dest
                i = 0
                while i < len(key_parts):
                    arg = arg[key]
                    key = key_parts[i]
                    i += 1
                arg[key] = data

    key_pattern = re.compile(
        r'^(((\[[0-9]+])|(([a-zA-Z0-9_\-]+)(\[[0-9]+])?))(\.([a-zA-Z0-9_\-]+)(\[[0-9]+])?)*)=(.*)$'
    )

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, self.Operations())
        dest_ops = getattr(namespace, self.dest)

        if values is None:
            dest_ops.add(tuple(), self._schema._blank)
        else:
            for key, key_parts, value in self.decode_values(values):
                schema = self._schema
                for k in key_parts:
                    schema = schema[k]
                action = schema._build_cmd_action()
                data = action.format_data(value)
                dest_ops.add(key_parts, data)

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
            try:
                v = cls._str_parser(value, is_simple=True)
            except Exception as shorthand_ex:
                msg = f"Failed to parse Shorthand Syntax: \nError detail: {shorthand_ex}"
                raise azclierror.InvalidArgumentValueError(msg) from shorthand_ex
        else:
            # compound type
            # read from file
            path = os.path.expanduser(value)
            if os.path.exists(path):
                v = get_file_json(path, preserve_order=True)
            else:
                try:
                    v = cls._str_parser(value)
                except ValueError as shorthand_ex:
                    try:
                        v = shell_safe_json_parse(value, True)
                    except Exception as ex:
                        logger.debug(ex)
                        msg = f"Failed to parse Shorthand Syntax: \nError detail: {shorthand_ex}"
                        raise azclierror.InvalidArgumentValueError(msg) from shorthand_ex
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
            raise ArgumentTypeError(f"dict type value expected, got '{data}'({type(data)})")


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
            raise ArgumentTypeError(f"dict type value expected, got '{data}'({type(data)})")


class AAZListArgAction(AAZCompoundTypeArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, self.Operations())
        dest_ops = getattr(namespace, self.dest)

        if values is None:
            dest_ops.add(tuple(), self._schema._blank)
        else:
            inputs = [*self.decode_values(values)]
            try:
                # standard expression
                ops = []
                for key, key_parts, value in inputs:
                    schema = self._schema
                    for k in key_parts:
                        schema = schema[k]
                    action = schema._build_cmd_action()
                    data = action.format_data(value)
                    ops.append((key_parts, data))
                for key_parts, data in ops:
                    dest_ops.add(key_parts, data)
            except Exception as ex:
                for key, _, _ in inputs:
                    if key:
                        # it's not a valid separate expression.
                        raise ex

                # This part of logic is to support separate element expression which is widely used in current command,
                # such as:
                #       --args val1 val2 val3.
                # The standard expression of it should be:
                #       --args [val1,val2,val3]

                elements = []
                element_action = self._schema.Element._build_cmd_action()
                for _, _, value in inputs:
                    elements.append(element_action.format_data(value))
                dest_ops.add(tuple(), elements)

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
            raise ArgumentTypeError(f"list type value expected, got '{data}'({type(data)})")


# class AAZListElementArgAction(AAZArgAction):
#
#     def __call__(self, parser, namespace, values, option_string=None):
#         dest_dict = getattr(namespace, self.dest)
#         if dest_dict is None:
#             dest_dict = OrderedDict()
#
#         key_parts = tuple()
#         if key_parts not in dest_dict:
#             dest_dict[key_parts] = []
#         elements = dest_dict[key_parts]
#
#         # if values is None:
#         #

