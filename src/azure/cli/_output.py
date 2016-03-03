from __future__ import print_function, unicode_literals

import sys
import json
import re

try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO #pylint: disable=import-error

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
    lo = ListOutput()
    return lo.dump(obj)

class OutputProducer(object): #pylint: disable=too-few-public-methods

    def __init__(self, formatter=format_list, file=sys.stdout): #pylint: disable=redefined-builtin
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        print(self.formatter(obj), file=self.file)

class ListOutput(object): #pylint: disable=too-few-public-methods

    def __init__(self):
        self._formatted_keys_cache = {}

    @staticmethod
    def _get_max_key_len(keys):
        return len(max(keys, key=len)) if keys else 0

    @staticmethod
    def _sort_key_func(key, item):
        # we want dictionaries to be last so use ASCII char 126 ~ to
        # prefix dictionary key names.
        return '~'+key if isinstance(item[key], dict) else key

    def _get_formatted_key(self, key):
        def _format_key(key):
            words = [word for word in re.split('([A-Z][^A-Z]*)', key) if word]
            return ' '.join(words).title()

        try:
            return self._formatted_keys_cache[key]
        except KeyError:
            self._formatted_keys_cache[key] = _format_key(key)
            return self._formatted_keys_cache[key]

    def _dump_object(self, io, item, indent):
        # get the formatted keys for this item
        # skip dicts because those will be handled recursively later.
        item_f_keys = {k: self._get_formatted_key(k) for k in item if not isinstance(item[k], dict)}
        key_width = ListOutput._get_max_key_len(item_f_keys.values())
        for key in sorted(item, key=lambda x: ListOutput._sort_key_func(x, item)):
            if isinstance(item[key], dict):
                # complex object
                io.write('\n')
                io.write('\t' * (indent+1))
                io.write(self._get_formatted_key(key).upper())
                io.write('\n')
                if item[key]:
                    self._dump_object(io, item[key], indent+1)
                else:
                    io.write('\t' * (indent+1))
                    io.write('None')
                    io.write('\n')
            else:
                # non-complex so write it
                io.write('\t' * indent)
                io.write('%s : %s' % (self._get_formatted_key(key).ljust(key_width), item[key]))
                io.write('\n')

    def dump(self, data):
        with StringIO() as io:
            for item in sorted(data, key=lambda x: sorted(x.keys())):
                self._dump_object(io, item, 0)
                io.write('\n')
            return io.getvalue()

class TableOutput(object):
    def __init__(self):
        self._rows = [{}]
        self._columns = {}
        self._column_order = []

    def dump(self):
        if len(self._rows) == 1:
            return

        with StringIO() as io:
            cols = [(c, self._columns[c]) for c in self._column_order]
            io.write(' | '.join(c.center(w) for c, w in cols))
            io.write('\n')
            io.write('-|-'.join('-' * w for c, w in cols))
            io.write('\n')
            for r in self._rows[:-1]:
                io.write(' | '.join(r[c].ljust(w) for c, w in cols))
                io.write('\n')
            return io.getvalue()

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
        with StringIO() as io:
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
            return io.getvalue()

