#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function, unicode_literals

import errno
import sys
import platform
import json
import re
import traceback
from collections import OrderedDict
from six import StringIO, text_type, u
import colorama
from tabulate import tabulate

from azure.cli.core._util import CLIError
import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)

def _decode_str(output):
    if not isinstance(output, text_type):
        output = u(str(output))
    return output

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj): #pylint: disable=method-hidden
        if isinstance(obj, bytes) and not isinstance(obj, str):
            return obj.decode()
        return json.JSONEncoder.default(self, obj)

def format_json(obj):
    result = obj.result
    input_dict = result.__dict__ if hasattr(result, '__dict__') else result
    return json.dumps(input_dict, indent=2, sort_keys=True, cls=ComplexEncoder,
                      separators=(',', ': ')) + '\n'

def format_json_color(obj):
    from pygments import highlight, lexers, formatters
    return highlight(format_json(obj), lexers.JsonLexer(), formatters.TerminalFormatter()) # pylint: disable=no-member


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
            result = obj.table_transformer(result)
        result_list = result if isinstance(result, list) else [result]
        return TableOutput.dump(result_list)
    except:
        logger.debug(traceback.format_exc())
        raise CLIError("Table output unavailable. "\
                       "Use the --query option to specify an appropriate query. "\
                       "Use --debug for more info.")

def format_list(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    lo = ListOutput()
    return lo.dump(result_list)

def format_tsv(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    return TsvOutput.dump(result_list)

class CommandResultItem(object): #pylint: disable=too-few-public-methods

    def __init__(self, result, table_transformer=None, is_query_active=False):
        self.result = result
        self.table_transformer = table_transformer
        self.is_query_active = is_query_active

class OutputProducer(object): #pylint: disable=too-few-public-methods

    format_dict = {
        'json': format_json,
        'jsonc': format_json_color,
        'table': format_table,
        'text': format_text,
        'list': format_list,
        'tsv': format_tsv,
    }

    def __init__(self, formatter=format_list, file=sys.stdout): #pylint: disable=redefined-builtin
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
        return OutputProducer.format_dict.get(format_type, format_list)

class TableOutput(object): #pylint: disable=too-few-public-methods

    SKIP_KEYS = ['id', 'type']

    @staticmethod
    def _capitalize_first_char(x):
        return x[0].upper() + x[1:] if x and len(x) > 0 else x

    @staticmethod
    def _auto_table_item(item):
        new_entry = OrderedDict()
        try:
            for k in item.keys():
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

    @staticmethod
    def _auto_table(result):
        if isinstance(result, list):
            new_result = []
            for item in result:
                new_result.append(TableOutput._auto_table_item(item))
            return new_result
        else:
            return TableOutput._auto_table_item(result)

    @staticmethod
    def dump(data):
        table_data = TableOutput._auto_table(data)
        table_str = tabulate(table_data, headers="keys", tablefmt="simple") if table_data else ''
        if table_str == '\n':
            raise ValueError('Unable to extract fields for table.')
        return table_str + '\n'

class ListOutput(object): #pylint: disable=too-few-public-methods

    # Match the capital letters in a camel case string
    FORMAT_KEYS_PATTERN = re.compile('([A-Z]+(?![a-z])|[A-Z]{1}[a-z]+)')

    def __init__(self):
        self._formatted_keys_cache = {}

    @staticmethod
    def _get_max_key_len(keys):
        return len(max(keys, key=len)) if keys else 0

    @staticmethod
    def _sort_key_func(key, item):
        # We want dictionaries to be last so use ASCII char 126 ~ to
        # prefix dictionary and list key names.
        if isinstance(item[key], dict):
            return '~~'+key
        elif isinstance(item[key], list):
            return '~'+key
        else:
            return key

    def _get_formatted_key(self, key):
        def _format_key(key):
            words = [word for word in re.split(ListOutput.FORMAT_KEYS_PATTERN, key) if word]
            return ' '.join(words).title()

        try:
            return self._formatted_keys_cache[key]
        except KeyError:
            self._formatted_keys_cache[key] = _format_key(key)
            return self._formatted_keys_cache[key]

    @staticmethod
    def _dump_line(io, line, indent):
        io.write('   ' * indent)
        io.write(_decode_str(line))
        io.write('\n')

    def _dump_object(self, io, obj, indent):
        if isinstance(obj, list):
            for array_item in obj:
                self._dump_object(io, array_item, indent)
        elif isinstance(obj, dict):
            obj_fk = {k: self._get_formatted_key(k) for k in obj}
            key_width = ListOutput._get_max_key_len(obj_fk.values())
            for key in sorted(obj, key=lambda x: ListOutput._sort_key_func(x, obj)):
                if isinstance(obj[key], dict) or isinstance(obj[key], list):
                    # complex object
                    line = '%s :' % (self._get_formatted_key(key).ljust(key_width))
                    ListOutput._dump_line(io, line, indent)
                    self._dump_object(io, obj[key] if obj[key] else 'None', indent+1)
                else:
                    # non-complex so write it
                    line = '%s : %s' % (self._get_formatted_key(key).ljust(key_width),
                                        'None' if obj[key] is None else obj[key])
                    ListOutput._dump_line(io, line, indent)
        else:
            ListOutput._dump_line(io, obj, indent)

    def dump(self, data):
        io = StringIO()
        for obj in data:
            self._dump_object(io, obj, 0)
            io.write('\n')
        io.write('\n')
        result = io.getvalue()
        io.close()
        return result

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

class TsvOutput(object): #pylint: disable=too-few-public-methods

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
            stream.write(str(data))

    @staticmethod
    def _dump_row(data, stream):
        separator = ''
        if isinstance(data, dict) or isinstance(data, list):
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
