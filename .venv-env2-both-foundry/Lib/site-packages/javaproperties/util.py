import re
from   six import PY2

if PY2:
    from collections     import Mapping
else:
    from collections.abc import Mapping

def itemize(kvs, sort_keys=False):
    if isinstance(kvs, Mapping):
        items = ((k, kvs[k]) for k in kvs)
    else:
        items = kvs
    if sort_keys:
        items = sorted(items)
    return items

def ascii_splitlines(s):
    lines = []
    lastend = 0
    for m in re.finditer(r'\r\n?|\n', s):
        lines.append(s[lastend:m.end()])
        lastend = m.end()
    if lastend < len(s):
        lines.append(s[lastend:])
    return lines
