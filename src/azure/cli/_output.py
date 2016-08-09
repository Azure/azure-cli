#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function, unicode_literals

import sys
import json
import re
import traceback
from collections import OrderedDict
from six import StringIO, text_type, u

from azure.cli._util import CLIError
import azure.cli._logging as _logging

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

def format_table(obj):
    result = obj.result
    try:
        if not obj.simple_output_query and not obj.is_query_active:
            raise ValueError('No query specified and no built-in query available.')
        if obj.simple_output_query and not obj.is_query_active:
            if callable(obj.simple_output_query):
                result = obj.simple_output_query(result)
            else:
                from jmespath import compile as compile_jmespath, search, Options
                result = compile_jmespath(obj.simple_output_query).search(result, Options(OrderedDict))
        obj_list = result if isinstance(result, list) else [result]
        to = TableOutput()
        for item in obj_list:
            for item_key in item:
                to.cell(item_key, item[item_key])
            to.end_row()
        return to.dump()
    except (ValueError, KeyError, TypeError):
        logger.debug(traceback.format_exc())
        raise CLIError("Table output unavailable. "\
                       "Change output type with --output or use "\
                       "the --query option to specify an appropriate query. "\
                       "Use --debug for more info.")

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

    def __init__(self, result, simple_output_query=None, is_query_active=False):
        self.result = result
        self.simple_output_query = simple_output_query
        self.is_query_active = is_query_active

class OutputProducer(object): #pylint: disable=too-few-public-methods

    format_dict = {
        'json': format_json,
        'table': format_table,
        'text': format_text,
        'list': format_list,
        'tsv': format_tsv,
    }

    def __init__(self, formatter=format_list, file=sys.stdout): #pylint: disable=redefined-builtin
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        output = self.formatter(obj)
        try:
            print(output, file=self.file, end='')
        except UnicodeEncodeError:
            print(output.encode('ascii', 'ignore').decode('utf-8', 'ignore'),
                  file=self.file, end='')

    @staticmethod
    def get_formatter(format_type):
        return OutputProducer.format_dict.get(format_type, format_list)

class ListOutput(object): #pylint: disable=too-few-public-methods

    # Match the capital letters in a camel case string
    FORMAT_KEYS_PATTERN = re.compile('([A-Z][^A-Z]*)')

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

class TableOutput(object):

    unsupported_types = (list, dict, set)

    def __init__(self):
        self._rows = [{}]
        self._columns = {}
        self._column_order = []

    def dump(self):
        if len(self._rows) == 1:
            return

        io = StringIO()
        cols = [(c, self._columns[c]) for c in self._column_order]
        io.write(' | '.join(c.center(w) for c, w in cols))
        io.write('\n')
        io.write('-|-'.join('-' * w for c, w in cols))
        io.write('\n')
        for r in self._rows[:-1]:
            io.write(' | '.join(r.get(c, '-').ljust(w) for c, w in cols))
            io.write('\n')
        result = io.getvalue()
        io.close()
        return result

    @property
    def any_rows(self):
        return len(self._rows) > 1

    def cell(self, name, value):
        if isinstance(value, TableOutput.unsupported_types):
            raise TypeError('Table output does not support objects of type {}.\n'\
                            'Offending object name={} value={}'.format(
                                [ut.__name__ for ut in TableOutput.unsupported_types], name, value))
        n = str(name)
        v = str(value)
        max_width = self._columns.get(n)
        if max_width is None:
            self._column_order.append(n)
            max_width = len(n)
        self._rows[-1][n] = v
        self._columns[n] = max(max_width, len(v))

    def end_row(self):
        self._rows.append({})

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
