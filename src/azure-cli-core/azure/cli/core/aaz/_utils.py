# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
from collections import OrderedDict

from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
from ._help import AAZShowHelp


def _get_profile_pkg(aaz_module_name, cloud):
    profile_module_name = cloud.profile.lower().replace('-', '_')
    try:
        return importlib.import_module(f'{aaz_module_name}.{profile_module_name}')
    except ModuleNotFoundError:
        return None


class AAZShortHandSyntaxParser:
    NULL_EXPRESSIONS = ('null', 'None')
    HELP_EXPRESSIONS = ('??', )

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
                result, length = self.parse_shorthand_quote_string(data)
                if length != len(data):
                    raise AAZInvalidShorthandSyntaxError(
                        data, length, len(data) - length, "Redundant tail for quota expression")
            else:
                result = data
        else:
            result, length = self.parse_shorthand_value(data)
            if length != len(data):
                raise AAZInvalidShorthandSyntaxError(data, length, len(data) - length, "Redundant tail")
        return result

    def parse_shorthand_value(self, remain):
        if remain.startswith('{'):
            return self.parse_shorthand_dict(remain)

        if remain.startswith('['):
            return self.parse_shorthand_list(remain)

        return self.parse_shorthand_string(remain)

    def parse_shorthand_dict(self, remain):
        result = OrderedDict()
        assert remain.startswith('{')
        idx = 1

        # handle empty dict
        if idx < len(remain) and remain[idx] == '}':
            return result, idx + 1

        while idx < len(remain):
            try:
                key, length = self.parse_shorthand_string(remain[idx:])
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
            else:
                raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Expect character ':'")

            if idx >= len(remain):
                raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Cannot parse empty")

            try:
                value, length = self.parse_shorthand_value(remain[idx:])
            except AAZInvalidShorthandSyntaxError as ex:
                ex.error_data = remain
                ex.error_at += idx
                raise ex
            except AAZShowHelp as aaz_help:
                aaz_help.keys = [key, *aaz_help.keys]
                raise aaz_help

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

    def parse_shorthand_list(self, remain):
        result = []
        assert remain.startswith('[')
        idx = 1

        # handle empty list
        if idx < len(remain) and remain[idx] == ']':
            return result, idx + 1

        while idx < len(remain):
            try:
                value, length = self.parse_shorthand_value(remain[idx:])
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

    def parse_shorthand_string(self, remain):
        idx = 0
        if len(remain) and remain[0] == "'":
            return self.parse_shorthand_quote_string(remain)

        while idx < len(remain):
            if remain[idx] in (',', ':', ']', '}'):
                break
            elif remain[idx].strip() == '':
                raise AAZInvalidShorthandSyntaxError(
                    remain, idx, 1, "Please wrap whitespace character in single quotes")
            elif remain[idx] in ('"', "'"):
                raise AAZInvalidShorthandSyntaxError(
                    remain, idx, 1, f"Please wrap {remain[idx]} character in single quotes")
            idx += 1

        if idx == 0:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, "Cannot parse empty")

        if remain[:idx] in self.NULL_EXPRESSIONS:
            return None, idx

        if remain[:idx] in self.HELP_EXPRESSIONS:
            raise AAZShowHelp()

        return remain[:idx], idx

    def parse_shorthand_quote_string(self, remain):
        assert remain[0] == "'"
        quote = remain[0]
        idx = 1
        result = ''
        while idx < len(remain):
            if remain[idx] == quote:
                quote = None
                idx += 1
                break

            if remain[idx] == '/':
                try:
                    c, length = self.parse_escape_character(remain[idx:])
                except AAZInvalidShorthandSyntaxError as ex:
                    ex.error_data = remain
                    ex.error_at += idx
                    raise ex

                result += c
                idx += length
            else:
                result += remain[idx]
                idx += 1
        if quote is not None:
            raise AAZInvalidShorthandSyntaxError(remain, idx, 1, f"Miss end quota character: {quote}")
        return result, idx

    @staticmethod
    def parse_escape_character(remain):
        assert remain[0] == '/'
        if len(remain) < 2:
            raise AAZInvalidShorthandSyntaxError(remain, 0, 1, f"Invalid escape character: {remain}")
        if remain[1] == "'":
            return "'", 2
        if remain[1] == '/':
            return '/', 2
        if remain[1] == '\\':
            return '\\', 2
        raise AAZInvalidShorthandSyntaxError(remain, 0, 2, f"Invalid escape character: {remain[:2]}")
