import re
import os
from argparse import Action, ArgumentTypeError
from azure.cli.core import azclierror
from ._utils import AAZShortHandSyntaxParser
from knack.log import get_logger

logger = get_logger(__name__)


class AAZArgAction(Action):

    _schema = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        data = self.format_data(values)
        setattr(namespace, self.dest, data)

    @classmethod
    def format_data(cls, data):
        """format input data"""
        # fill blank argument
        if data is None:
            return cls._schema._blank
        return data


class AAZSimpleTypeArgAction(AAZArgAction):

    @classmethod
    def format_data(cls, data):
        data = super().format_data(data)
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

    _shorthand_parser = AAZShortHandSyntaxParser()

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
            key_items = cls._split_key(key)
            body = cls._decode_body(key, key_items, body)
            yield key_items, body

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
    def _decode_body(cls, key, key_items, body):
        from ._arg import AAZSimpleTypeArg
        from azure.cli.core.util import get_file_json, shell_safe_json_parse

        schema = cls._schema
        for item in key_items:
            schema = schema[item]

        action = schema.to_cmd_arg(name=key)
        if isinstance(schema, AAZSimpleTypeArg):
            # simple type
            try:
                data = cls._shorthand_parser(body)
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
                    data = cls._shorthand_parser(body)
                except ValueError as shorthand_ex:
                    try:
                        data = shell_safe_json_parse(body, True)
                    except Exception as ex:
                        logger.debug(ex)
                        msg = f"Failed to parse Shorthand Syntax: \nError detail: {shorthand_ex}"
                        raise azclierror.InvalidArgumentValueError(msg) from shorthand_ex
        return action.format_data(data=data)


class AAZObjectArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        print(values, option_string)


class AAZDictArgAction(AAZArgAction):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class AAZListArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        print(values, option_string)


class AAZListElementArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        print(values, option_string)
