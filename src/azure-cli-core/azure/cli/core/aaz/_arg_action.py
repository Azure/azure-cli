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


class AAZSimpleTypeArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            data = self._schema._blank
        else:
            if isinstance(values, str):
                data = self._str_parser(values, is_simple=True)
            else:
                data = values
            data = self.format_data(data)
        setattr(namespace, self.dest, data)

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

    key_pattern = re.compile(
        r'^(((\[[0-9]+])|(([a-zA-Z0-9_\-]+)(\[[0-9]+])?))(\.([a-zA-Z0-9_\-]+)(\[[0-9]+])?)*)=(.*)$'
    )

    def __call__(self, parser, namespace, values, option_string=None):
        dest_dict = getattr(namespace, self.dest)
        if dest_dict is None:
            dest_dict = OrderedDict()

        if values is None:
            key_parts = tuple()
            dest_dict[key_parts] = self._schema._blank
        else:
            for key, key_parts, value in self.decode_values(values):
                schema = self._schema
                for k in key_parts:
                    schema = schema[k]
                action = schema._build_cmd_action()
                dest_dict[key_parts] = action.format_data(value)
        setattr(namespace, self.dest, dest_dict)

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
        dest_dict = getattr(namespace, self.dest)
        if dest_dict is None:
            dest_dict = OrderedDict()

        if values is None:
            key_parts = tuple()
            dest_dict[key_parts] = self._schema._blank
        else:
            inputs = [*self.decode_values(values)]
            try:
                # standard expression
                for key, key_parts, value in inputs:
                    schema = self._schema
                    for k in key_parts:
                        schema = schema[k]
                    action = schema._build_cmd_action()
                    dest_dict[key_parts] = action.format_data(value)
            except Exception as ex:
                for key, _, _ in inputs:
                    if key:
                        raise ex
                # separate element expression
                elements = []
                element_action = self._schema.Element._build_cmd_action()
                for _, _, value in inputs:
                    elements.append(element_action.format_data(value))
                key_parts = tuple()
                dest_dict[key_parts] = elements

        setattr(namespace, self.dest, dest_dict)

    @classmethod
    def format_data(cls, data):
        if data is None:
            return None
        elif isinstance(data, dict):
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
#         print(values, option_string)
