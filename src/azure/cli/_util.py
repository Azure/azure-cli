import types
import json

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

class TableOutput(object):
    def __enter__(self):
        self._rows = [{}]
        self._columns = {}
        self._column_order = []
        self.io = StringIO()
        return self

    def dump(self):
        """Return the dump of the table as a string
        """
        if len(self._rows) == 1:
            return

        cols = [(c, self._columns[c]) for c in self._column_order]
        self.io.write(' | '.join(c.center(w) for c, w in cols))
        self.io.write('\n')
        self.io.write('-|-'.join('-' * w for c, w in cols))
        self.io.write('\n')
        for r in self._rows[:-1]:
            self.io.write(' | '.join(r[c].ljust(w) for c, w in cols))
            self.io.write('\n')
        return self.io.getvalue()

    def __exit__(self, ex_type, ex_value, ex_tb):
        self.io.close()

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

    def __enter__(self):
        self.identifiers = {}
        self.io = StringIO()
        return self

    def __exit__(self, ex_type, ex_value, ex_tb):
        self.io.close()
    
    def add(self, identifier, value):
        if identifier in self.identifiers:
            self.identifiers[identifier].append(value)
        else:
            self.identifiers[identifier] = [value]

    def dump(self):
        for id in sorted(self.identifiers):
            self.io.write(id.upper())
            self.io.write('\t')
            for col in self.identifiers[id]:
                if isinstance(col, str):
                    self.io.write(col)
                else:
                    # TODO: Handle complex objects
                    self.io.write("null")
                self.io.write('\t')
            self.io.write('\n')
        return self.io.getvalue()
