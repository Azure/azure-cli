from __future__ import print_function, unicode_literals

import sys
import json
import re
from datetime import datetime
from enum import Enum
from six import StringIO

class OutputFormatException(Exception):
    pass

def format_json(obj):
    input_dict = obj.__dict__ if hasattr(obj, '__dict__') else obj
    return json.dumps(input_dict, indent=2, sort_keys=True, separators=(',', ': '))

def format_table(obj):
    obj_list = obj if isinstance(obj, list) else [obj]
    to = TableOutput()
    try:
        for item in obj_list:
            for item_key in sorted(item):
                to.cell(item_key, item[item_key])
            to.end_row()
        return to.dump()
    except TypeError:
        return ''

def format_text(obj):
    obj_list = obj if isinstance(obj, list) else [obj]
    to = TextOutput()
    try:
        for item in obj_list:
            for item_key in sorted(item):
                to.add(item_key, item[item_key])
        return to.dump()
    except TypeError:
        return ''

def format_list(obj):
    obj_list = obj if isinstance(obj, list) else [obj]
    lo = ListOutput()
    return lo.dump(obj_list)

class OutputProducer(object): #pylint: disable=too-few-public-methods

    format_dict = {
        'json': format_json,
        'table': format_table,
        'text': format_text,
        'list': format_list
    }

    KEYS_CAMELCASE_PATTERN = re.compile('(?!^)_([a-zA-Z])')

    def __init__(self, formatter=format_list, file=sys.stdout): #pylint: disable=redefined-builtin
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        obj = OutputProducer.todict(obj)
        print(self.formatter(obj), file=self.file)

    @staticmethod
    def todict(obj): #pylint: disable=too-many-return-statements
        def to_camelcase(s):
            return re.sub(OutputProducer.KEYS_CAMELCASE_PATTERN, lambda x: x.group(1).upper(), s)

        if isinstance(obj, dict):
            return {k: OutputProducer.todict(v) for (k, v) in obj.items()}
        elif isinstance(obj, list):
            return [OutputProducer.todict(a) for a in obj]
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '_asdict'):
            return OutputProducer.todict(obj._asdict())
        elif hasattr(obj, '__dict__'):
            return dict([(to_camelcase(k), OutputProducer.todict(v))
                         for k, v in obj.__dict__.items()
                         if not callable(v) and not k.startswith('_')])
        else:
            return obj

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
        io.write(line)
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
        result = io.getvalue()
        io.close()
        return result

class TableOutput(object):
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
                    io.write(col)
                io.write('\t')
            io.write('\n')
        result = io.getvalue()
        io.close()
        return result

