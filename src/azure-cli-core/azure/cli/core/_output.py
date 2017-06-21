# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function, unicode_literals

import errno
import sys
import platform
import json
import traceback
from collections import OrderedDict
from six import StringIO, text_type, u, string_types
import colorama
from tabulate import tabulate

from azure.cli.core.util import CLIError
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


def _decode_str(output):
    if not isinstance(output, text_type):
        output = u(str(output))
    return output


class ComplexEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, bytes) and not isinstance(o, str):
            return o.decode()
        return json.JSONEncoder.default(self, o)


def format_json(obj):
    result = obj.result
    # OrderedDict.__dict__ is always '{}', to persist the data, convert to dict first.
    input_dict = dict(result) if hasattr(result, '__dict__') else result
    return json.dumps(input_dict, indent=2, sort_keys=True, cls=ComplexEncoder,
                      separators=(',', ': ')) + '\n'


def format_json_color(obj):
    from pygments import highlight, lexers, formatters
    return highlight(format_json(obj), lexers.JsonLexer(), formatters.TerminalFormatter())  # pylint: disable=no-member


def format_text(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    to = TextOutput()
    try:
        for item in result_list:
            for item_key in sorted(item):
                to.add(item_key, item[item_key])
        return to.dump()
    except TypeError:
        return ''


def format_table(obj):
    result = obj.result
    try:
        if obj.table_transformer and not obj.is_query_active:
            if isinstance(obj.table_transformer, str):
                from jmespath import compile as compile_jmes, Options
                result = compile_jmes(obj.table_transformer).search(result, Options(OrderedDict))
            else:
                result = obj.table_transformer(result)
        result_list = result if isinstance(result, list) else [result]
        should_sort_keys = not obj.is_query_active and not obj.table_transformer
        to = TableOutput(should_sort_keys)
        return to.dump(result_list)
    except:
        logger.debug(traceback.format_exc())
        raise CLIError("Table output unavailable. "
                       "Use the --query option to specify an appropriate query. "
                       "Use --debug for more info.")


def format_tsv(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    return TsvOutput.dump(result_list)


class CommandResultItem(object):  # pylint: disable=too-few-public-methods

    def __init__(self, result, table_transformer=None, is_query_active=False):
        self.result = result
        self.table_transformer = table_transformer
        self.is_query_active = is_query_active


class OutputProducer(object):  # pylint: disable=too-few-public-methods

    format_dict = {
        'json': format_json,
        'jsonc': format_json_color,
        'table': format_table,
        'text': format_text,
        'tsv': format_tsv,
    }

    def __init__(self, formatter, file=sys.stdout):  # pylint: disable=redefined-builtin
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        if platform.system() == 'Windows':
            self.file = colorama.AnsiToWin32(self.file).stream
        output = self.formatter(obj)
        try:
            print(output, file=self.file, end='')
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                pass
            else:
                raise
        except UnicodeEncodeError:
            print(output.encode('ascii', 'ignore').decode('utf-8', 'ignore'),
                  file=self.file, end='')

    @staticmethod
    def get_formatter(format_type):
        return OutputProducer.format_dict.get(format_type)


class TableOutput(object):  # pylint: disable=too-few-public-methods

    SKIP_KEYS = ['id', 'type', 'etag']

    def __init__(self, should_sort_keys=False):
        self.should_sort_keys = should_sort_keys

    @staticmethod
    def _capitalize_first_char(x):
        return x[0].upper() + x[1:] if x else x

    def _auto_table_item(self, item):
        new_entry = OrderedDict()
        try:
            keys = sorted(item) if self.should_sort_keys and isinstance(item, dict) else item.keys()
            for k in keys:
                if k in TableOutput.SKIP_KEYS:
                    continue
                if item[k] and not isinstance(item[k], (list, dict, set)):
                    new_entry[TableOutput._capitalize_first_char(k)] = item[k]
        except AttributeError:
            # handles odd cases where a string/bool/etc. is returned
            if isinstance(item, list):
                for col, val in enumerate(item):
                    new_entry['Column{}'.format(col + 1)] = val
            else:
                new_entry['Result'] = item
        return new_entry

    def _auto_table(self, result):
        if isinstance(result, list):
            new_result = []
            for item in result:
                new_result.append(self._auto_table_item(item))
            return new_result
        return self._auto_table_item(result)

    def dump(self, data):
        table_data = self._auto_table(data)
        table_str = tabulate(table_data, headers="keys", tablefmt="simple") if table_data else ''
        if table_str == '\n':
            raise ValueError('Unable to extract fields for table.')
        return table_str + '\n'


class TextOutput(object):

    def __init__(self):
        self.identifiers = {}

    def add(self, identifier, value):
        if identifier in self.identifiers:
            self.identifiers[identifier].append(value)
        else:
            self.identifiers[identifier] = [value]

    def dump(self):
        io = StringIO()
        for identifier in sorted(self.identifiers):
            io.write(identifier.upper())
            io.write('\t')
            for col in self.identifiers[identifier]:
                if isinstance(col, (list, dict)):
                    # TODO: Need to handle complex objects
                    io.write("null")
                else:
                    io.write(str(col))
                io.write('\t')
            io.write('\n')
        result = io.getvalue()
        io.close()
        return result


class TsvOutput(object):  # pylint: disable=too-few-public-methods

    @staticmethod
    def _dump_obj(data, stream):
        if isinstance(data, list):
            stream.write(str(len(data)))
        elif isinstance(data, dict):
            # We need to print something to avoid mismatching
            # number of columns if the value is None for some instances
            # and a dictionary value in other...
            stream.write('')
        else:
            to_write = data if isinstance(data, string_types) else str(data)
            stream.write(to_write)

    @staticmethod
    def _dump_row(data, stream):
        separator = ''
        if isinstance(data, (dict, list)):
            if isinstance(data, OrderedDict):
                values = data.values()
            elif isinstance(data, dict):
                values = [value for _, value in sorted(data.items())]
            else:
                values = data

            # Iterate through the items either sorted by key value (if dict) or in the order
            # they were added (in the cases of an ordered dict) in order to make the output
            # stable
            for value in values:
                stream.write(separator)
                TsvOutput._dump_obj(value, stream)
                separator = '\t'
        elif isinstance(data, list):
            for value in data:
                stream.write(separator)
                TsvOutput._dump_obj(value, stream)
                separator = '\t'
        elif isinstance(data, bool):
            TsvOutput._dump_obj(str(data).lower(), stream)
        else:
            TsvOutput._dump_obj(data, stream)
        stream.write('\n')

    @staticmethod
    def dump(data):
        io = StringIO()
        for item in data:
            TsvOutput._dump_row(item, io)

        result = io.getvalue()
        io.close()
        return result
