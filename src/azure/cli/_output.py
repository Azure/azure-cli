from __future__ import print_function, unicode_literals

import sys
import json
import re

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

    def __init__(self, formatter=format_list, file=sys.stdout): #pylint: disable=redefined-builtin
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        print(self.formatter(obj), file=self.file)

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
        io.write('  ' * indent)
        io.write(line)
        io.write('\n')

    def _dump_object(self, io, obj, indent):
        if isinstance(obj, list):
            for array_item in obj:
                self._dump_object(io, array_item, indent+1)
        elif isinstance(obj, dict):
            # Get the formatted keys for this item
            # Skip dicts/lists because those will be handled recursively later.
            # We use this object to calc key width and don't want to dicts/lists in this.
            obj_fk = {k: self._get_formatted_key(k)
                      for k in obj if not isinstance(obj[k], dict) and not isinstance(obj[k], list)}
            key_width = ListOutput._get_max_key_len(obj_fk.values())
            for key in sorted(obj, key=lambda x: ListOutput._sort_key_func(x, obj)):
                if isinstance(obj[key], dict):
                    # complex object
                    io.write('\n')
                    ListOutput._dump_line(io, self._get_formatted_key(key).upper(), indent+1)
                    if obj[key]:
                        self._dump_object(io, obj[key], indent+1)
                    else:
                        ListOutput._dump_line(io, 'None', indent+1)
                elif isinstance(obj[key], list):
                    # list object
                    io.write('\n')
                    ListOutput._dump_line(io, self._get_formatted_key(key).upper(), indent+1)
                    if obj[key]:
                        for array_item in obj[key]:
                            self._dump_object(io, array_item, indent+1)
                    else:
                        ListOutput._dump_line(io, 'None', indent+1)
                else:
                    # non-complex so write it
                    line = '%s : %s' % (self._get_formatted_key(key).ljust(key_width), obj[key])
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
            io.write(' | '.join(r[c].ljust(w) for c, w in cols))
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
                if isinstance(col, str):
                    io.write(col)
                else:
                    # TODO: Need to handle complex objects
                    io.write("null")
                io.write('\t')
            io.write('\n')
        result = io.getvalue()
        io.close()
        return result

