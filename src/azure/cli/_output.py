from __future__ import print_function, unicode_literals

import sys
import json

try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO

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

class OutputProducer(object):
    
    def __init__(self, formatter=format_json, file=sys.stdout):
        self.formatter = formatter
        self.file = file

    def out(self, obj):
        print(self.formatter(obj), file=self.file)

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
            for id in sorted(self.identifiers):
                io.write(id.upper())
                io.write('\t')
                for col in self.identifiers[id]:
                    if isinstance(col, str):
                        io.write(col)
                    else:
                        # TODO: Handle complex objects
                        io.write("null")
                    io.write('\t')
                io.write('\n')
            return io.getvalue()

