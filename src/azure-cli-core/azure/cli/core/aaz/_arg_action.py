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
        dest_dict = getattr(namespace, self.dest, OrderedDict())
        if values is None:
            key_parts = tuple()
            dest_dict[key_parts] = self._schema._blank
        else:
            for key, key_parts, data in self.decode_values(values):
                schema = self._schema
                for k in key_parts:
                    schema = schema[k]
                action = schema.to_cmd_arg(name=key)
                dest_dict[key_parts] = action.format_data(data)
        setattr(namespace, self.dest, dest_dict)

    @classmethod
    def decode_values(cls, values):
        for value in values:
            assert isinstance(value, str)
            match = cls.key_pattern.fullmatch(value)
            if not match:
                key = None
                body = value
            else:
                key = match[1]
                body = match[len(match.regs) - 1]
            key_parts = cls._split_key(key)
            body = cls._decode_body(key_parts, body)
            yield key, key_parts, body

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
    def _decode_body(cls, key_items, body):
        from ._arg import AAZSimpleTypeArg
        from azure.cli.core.util import get_file_json, shell_safe_json_parse

        schema = cls._schema
        for item in key_items:
            schema = schema[item]

        if len(body) == 0:
            # the express "a=" will return the blank value of schema a
            return schema._blank

        if isinstance(schema, AAZSimpleTypeArg):
            # simple type
            try:
                data = cls._str_parser(body, is_simple=True)
            except Exception as shorthand_ex:
                msg = f"Failed to parse Shorthand Syntax: \nError detail: {shorthand_ex}"
                raise azclierror.InvalidArgumentValueError(msg) from shorthand_ex
        else:
            # compound type
            # read from file
            path = os.path.expanduser(body)
            if os.path.exists(path):
                data = get_file_json(path, preserve_order=True)
            else:
                try:
                    data = cls._str_parser(body)
                except ValueError as shorthand_ex:
                    try:
                        data = shell_safe_json_parse(body, True)
                    except Exception as ex:
                        logger.debug(ex)
                        msg = f"Failed to parse Shorthand Syntax: \nError detail: {shorthand_ex}"
                        raise azclierror.InvalidArgumentValueError(msg) from shorthand_ex
        return data


class AAZObjectArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        # TODO:
        pass


class AAZDictArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        # TODO:
        pass


class AAZListArgAction(AAZCompoundTypeArgAction):

    @classmethod
    def format_data(cls, data):
        # TODO:
        pass


# class AAZListElementArgAction(AAZArgAction):
#
#     def __call__(self, parser, namespace, values, option_string=None):
#         print(values, option_string)
