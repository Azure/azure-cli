import types

class TableOutput(object):
    def __enter__(self):
        self._rows = [{}]
        self._columns = {}
        self._column_order = []
        return self

    def __exit__(self, ex_type, ex_value, ex_tb):
        if ex_type:
            return
        if len(self._rows) == 1:
            return

        cols = [(c, self._columns[c]) for c in self._column_order]
        print(' | '.join(c.center(w) for c, w in cols))
        print('-|-'.join('-' * w for c, w in cols))
        for r in self._rows[:-1]:
            print(' | '.join(r[c].ljust(w) for c, w in cols))
        print()

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
