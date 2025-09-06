# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import re
from collections import OrderedDict
import json
from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
from ._help import AAZShowHelp
from ._base import AAZBlankArgValue


def to_snack_case(name, separator='_'):
    assert isinstance(name, str)
    name = re.sub('(.)([A-Z][a-z]+)', r'\1' + separator + r'\2', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1' + separator + r'\2', name).lower()
    return name.replace('-', separator).replace('_', separator)


class AAZShortHandSyntaxParser:

    NULL_EXPRESSIONS = ('null',)  # user can use "null" string to pass `None` value
    HELP_EXPRESSIONS = ('??', )  # the mark to show detail help.

    partial_value_key_pattern = re.compile(
        r"^(((\[-?[0-9]+])|((([a-zA-Z0-9_\-]+)|('([^']*)'(/([^']*)')*))(\[-?[0-9]+])?))(\.(([a-zA-Z0-9_\-]+)|('([^']*)'(/([^']*)')*))(\[-?[0-9]+])?)*)=(.*)$"  # pylint: disable=line-too-long
    )  # 'Partial Value' format

    def __call__(self, data, is_simple=False):
        assert isinstance(data, str)
        if len(data) == 0:
            raise AAZInvalidShorthandSyntaxError(data, 0, 1, "Cannot parse empty")

        if is_simple:
            # simple element type
            if data in self.NULL_EXPRESSIONS:
                result = None
            elif data in self.HELP_EXPRESSIONS:
                raise AAZShowHelp()
            elif len(data) and data[0] == "'":
                result, length = self.parse_single_quotes_string(data)
                if length != len(data):
                    raise AAZInvalidShorthandSyntaxError(
                        data, length, len(data) - length, "Redundant tail for quota expression")
            else:
                result = data
        else:
            result, length = self.parse_value(data)
            if length != len(data):
                raise AAZInvalidShorthandSyntaxError(data, length, len(data) - length, "Redundant tail")
        return result

    def parse_value(self, remain):
        if remain.startswith('{'):
            return self.parse_dict(remain)

        if remain.startswith('['):
            return self.parse_list(remain)

        return self.parse_string(remain, convert_simple_type=True)

    def parse_dict(self, remain):  # pylint: disable=too-many-statements
        result = OrderedDict()
        assert remain.startswith('{')
        idx = 1

        # handle empty dict
        if idx < len(remain) and remain[idx] == '}':
            return result, idx + 1

        while idx < len(remain):
            try:
                key, length = self.parse_string(remain[idx:])
            except AAZInvalidShorthandSyntaxError as ex:
                ex.error_data = remain
                ex.error_at += idx
                raise ex
            except AAZShowHelp as aaz_help:
                raise aaz_help

            if '"' in key:
                raise AAZInvalidShorthandSyntaxError(remain, idx, length,
                                                     f"Dict key should not contain double quotes '{key}'")
            if "'" in key:
                raise AAZInvalidShorthandSyntaxError(remain, idx, length,
                                                     f"Dict key should not contain single quotes '{key}'")
            if key in result:
                raise AAZInvalidShorthandSyntaxError(remain, idx, length, f"Duplicate defined dict key '{key}'")

            idx += length
            if idx < len(remain) and remain[idx] == ':':
                idx += 1
                if idx >= len(remain):
                    raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Cannot parse empty")

                try:
                    value, length = self.parse_value(remain[idx:])
                except AAZInvalidShorthandSyntaxError as ex:
                    ex.error_data = remain
                    ex.error_at += idx
                    raise ex
                except AAZShowHelp as aaz_help:
                    aaz_help.keys = [key, *aaz_help.keys]
                    raise aaz_help
            elif idx < len(remain) and remain[idx] in (',', '}'):
                # use blank value
                value = AAZBlankArgValue
                length = 0
            else:
                raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect characters ':' or ','")

            result[key] = value
            idx += length
            if idx < len(remain) and remain[idx] == ',':
                idx += 1
                if idx < len(remain) and remain[idx] == '}':
                    # support to parse '{a:b,}' suffix
                    break
            elif idx < len(remain) and remain[idx] == '}':
                break
            else:
                raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect character ',' or '}'")

        if idx < len(remain) and remain[idx] == '}':
            idx += 1
        else:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect character '}'")

        return result, idx

    def parse_list(self, remain):
        result = []
        assert remain.startswith('[')
        idx = 1

        # handle empty list
        if idx < len(remain) and remain[idx] == ']':
            return result, idx + 1

        while idx < len(remain):
            try:
                value, length = self.parse_value(remain[idx:])
            except AAZInvalidShorthandSyntaxError as ex:
                ex.error_data = remain
                ex.error_at += idx
                raise ex
            except AAZShowHelp as aaz_help:
                aaz_help.keys = [0, *aaz_help.keys]
                raise aaz_help

            result.append(value)
            idx += length
            if idx < len(remain) and remain[idx] == ',':
                idx += 1
                if idx < len(remain) and remain[idx] == ']':
                    # support to parse '[a,]' suffix
                    break
            elif idx < len(remain) and remain[idx] == ']':
                break
            else:
                raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect character ',' or ']'")
        if idx < len(remain) and remain[idx] == ']':
            idx += 1
        else:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect character ']'")
        return result, idx

    def parse_string(self, remain, convert_simple_type=False):
        idx = 0
        if len(remain) and remain[0] == "'":
            return self.parse_single_quotes_string(remain)

        while idx < len(remain):
            if remain[idx] in (',', ':', ']', '}'):
                break
            if remain[idx].strip() == '':
                raise AAZInvalidShorthandSyntaxError(
                    remain, idx, 1, "Please wrap whitespace character in single quotes")
            if remain[idx] in ('"', "'"):
                raise AAZInvalidShorthandSyntaxError(
                    remain, idx, 1, f"Please wrap {remain[idx]} character in single quotes")

            idx += 1

        if idx == 0:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Cannot parse empty")

        if remain[:idx] in self.NULL_EXPRESSIONS:
            return None, idx

        if remain[:idx] in self.HELP_EXPRESSIONS:
            raise AAZShowHelp()

        if convert_simple_type:
            try:
                converted = json.loads(remain[:idx])
                if isinstance(converted, (str, int, float, bool)):
                    return converted, idx
            except ValueError:
                pass

        return remain[:idx], idx

    @staticmethod
    def parse_single_quotes_string(remain):
        assert remain[0] == "'"
        quote = remain[0]
        idx = 1
        result = ''
        while idx < len(remain):
            if remain[idx] == quote:
                if len(remain) > idx + 1 and remain[idx + 1] == '/':
                    # parse '/ as '
                    result += quote
                    idx += 2
                else:
                    quote = None
                    idx += 1
                    break
            else:
                result += remain[idx]
                idx += 1

        if quote is not None:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, f"Miss end quota character: {quote}")
        return result, idx

    @classmethod
    def split_partial_value(cls, v):
        """ split 'Partial Value' format """
        assert isinstance(v, str)
        match = cls.partial_value_key_pattern.fullmatch(v)
        if not match:
            key = None
        else:
            key = match[1]
            v = match[len(match.regs) - 1]
        key_parts = cls.parse_partial_value_key(key)
        return key, key_parts, v

    @classmethod
    def parse_partial_value_key(cls, key):
        if key is None:
            return tuple()
        key_items = []
        idx = 0
        while idx < len(key):
            if key[idx] == '[':
                try:
                    key_item, length = cls.parse_partial_value_idx_key(key[idx:])
                except AAZInvalidShorthandSyntaxError as ex:
                    ex.error_data = key
                    ex.error_at += idx
                    raise ex
                idx += length
            else:
                try:
                    key_item, length = cls.parse_partial_value_prop_key(key[idx:])
                except AAZInvalidShorthandSyntaxError as ex:
                    ex.error_data = key
                    ex.error_at += idx
                    raise ex
                idx += length
            key_items.append(key_item)
        return tuple(key_items)

    @classmethod
    def parse_partial_value_idx_key(cls, remain):
        assert remain[0] == '['
        idx = 1
        while idx < len(remain) and remain[idx] != ']':
            idx += 1
        if idx < len(remain) and remain[idx] == ']':
            result = remain[1:idx]
            idx += 1
        else:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect character ']'")

        if len(result) == 0:
            raise AAZInvalidShorthandSyntaxError(remain, 0, 2, "Miss index")
        if idx < len(remain) and remain[idx] == '.':
            idx += 1
        return int(result), idx

    @classmethod
    def parse_partial_value_prop_key(cls, remain):
        idx = 0
        if remain[0] == "'":
            result, length = cls.parse_single_quotes_string(remain)
            idx += length
        else:
            while idx < len(remain) and remain[idx] not in ('.', '['):
                idx += 1
            result = remain[:idx]
        if len(result) == 0:
            raise AAZInvalidShorthandSyntaxError(remain, 0, idx, "Miss prop name")
        if idx < len(remain) and remain[idx] == '.':
            idx += 1
        return result, idx
