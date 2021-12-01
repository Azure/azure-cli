import importlib
from azure.cli.core.aaz.exceptions import AAZInvalidShorthandSyntaxError
from collections import OrderedDict


def _get_profile_pkg(aaz_module_name, cloud):
    profile_module_name = cloud.profile.lower().replace('-', '_')
    try:
        return importlib.import_module(f'{aaz_module_name}.{profile_module_name}')
    except ModuleNotFoundError:
        return None


class AAZShortHandSyntaxParser:

    def __call__(self, data):
        assert isinstance(data, str)
        result, length = self.parse_shorthand(data)
        if length != len(data):
            raise AAZInvalidShorthandSyntaxError(data, length, "Redundant tail")
        return result

    def parse_shorthand(self, remain):
        if remain.startswith('{'):
            return self.parse_shorthand_dict(remain)
        elif remain.startswith('['):
            return self.parse_shorthand_list(remain)
        else:
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

            if key in result:
                raise AAZInvalidShorthandSyntaxError(remain, idx, f"Duplicate defined dict key '{key}'")

            idx += length
            if idx < len(remain) and remain[idx] == ':':
                idx += 1
            else:
                raise AAZInvalidShorthandSyntaxError(remain, idx, "Expect character ':'")

            if idx >= len(remain):
                raise AAZInvalidShorthandSyntaxError(remain, idx, "Cannot parse empty")

            try:
                value, length = self.parse_shorthand(remain[idx:])
            except AAZInvalidShorthandSyntaxError as ex:
                ex.error_data = remain
                ex.error_at += idx
                raise ex

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
                raise AAZInvalidShorthandSyntaxError(remain, idx, "Expect character ',' or '}'")

        if idx < len(remain) and remain[idx] == '}':
            idx += 1
        else:
            raise AAZInvalidShorthandSyntaxError(remain, idx, "Expect character '}'")

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
                value, length = self.parse_shorthand(remain[idx:])
            except AAZInvalidShorthandSyntaxError as ex:
                ex.error_data = remain
                ex.error_at += idx
                raise ex

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
                raise AAZInvalidShorthandSyntaxError(remain, idx, "Expect character ',' or ']'")
        if idx < len(remain) and remain[idx] == ']':
            idx += 1
        else:
            raise AAZInvalidShorthandSyntaxError(remain, idx, "Expect character ']'")
        return result, idx

    def parse_shorthand_string(self, remain):
        idx = 0
        if len(remain) and remain[0] in ('"', "'"):
            return self.parse_shorthand_quote_string(remain)

        while idx < len(remain):
            if remain[idx] in (',', ':', ']', '}'):
                break
            idx += 1
        if idx == 0:
            raise AAZInvalidShorthandSyntaxError(remain, idx, "Cannot parse empty")
        elif remain[:idx] in ('null', 'None'):
            return None, idx
        return remain[:idx], idx

    def parse_shorthand_quote_string(self, remain):
        assert remain[0] in ('"', "'")
        quote = remain[0]
        idx = 1
        result = ''
        while idx < len(remain):
            if remain[idx] == quote:
                quote = None
                idx += 1
                break

            if remain[idx] == '\\':
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
            raise AAZInvalidShorthandSyntaxError(remain, idx, f"Miss end quota character: {quote}")
        return result, idx

    @staticmethod
    def parse_escape_character(remain):
        assert remain[0] == '\\'
        if len(remain) < 2:
            raise AAZInvalidShorthandSyntaxError(remain, 0, f"Invalid escape character: {remain}")
        if remain[1] == '"':
            return '"', 2
        elif remain[1] == "'":
            return "'", 2
        elif remain[1] == '\\':
            return '\\', 2
        elif remain[1] == 'b':
            return '\b', 2
        elif remain[1] == 'f':
            return '\f', 2
        elif remain[1] == 'n':
            return '\n', 2
        elif remain[1] == 'r':
            return '\r', 2
        elif remain[1] == 't':
            return '\t', 2
        else:
            raise AAZInvalidShorthandSyntaxError(remain, 0, f"Invalid escape character: {remain[:2]}")
