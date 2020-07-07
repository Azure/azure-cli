from   __future__ import unicode_literals
import re
from   six        import binary_type, StringIO, BytesIO, unichr
from   .util      import ascii_splitlines

def load(fp, object_pairs_hook=dict):
    """
    Parse the contents of the `~io.IOBase.readline`-supporting file-like object
    ``fp`` as a simple line-oriented ``.properties`` file and return a `dict`
    of the key-value pairs.

    ``fp`` may be either a text or binary filehandle, with or without universal
    newlines enabled.  If it is a binary filehandle, its contents are decoded
    as Latin-1.

    By default, the key-value pairs extracted from ``fp`` are combined into a
    `dict` with later occurrences of a key overriding previous occurrences of
    the same key.  To change this behavior, pass a callable as the
    ``object_pairs_hook`` argument; it will be called with one argument, a
    generator of ``(key, value)`` pairs representing the key-value entries in
    ``fp`` (including duplicates) in order of occurrence.  `load` will then
    return the value returned by ``object_pairs_hook``.

    .. versionchanged:: 0.5.0
        Invalid ``\\uXXXX`` escape sequences will now cause an
        `InvalidUEscapeError` to be raised

    :param fp: the file from which to read the ``.properties`` document
    :type fp: file-like object
    :param callable object_pairs_hook: class or function for combining the
        key-value pairs
    :rtype: `dict` of text strings or the return value of ``object_pairs_hook``
    :raises InvalidUEscapeError: if an invalid ``\\uXXXX`` escape sequence
        occurs in the input
    """
    return object_pairs_hook((k,v) for k,v,_ in parse(fp) if k is not None)

def loads(s, object_pairs_hook=dict):
    """
    Parse the contents of the string ``s`` as a simple line-oriented
    ``.properties`` file and return a `dict` of the key-value pairs.

    ``s`` may be either a text string or bytes string.  If it is a bytes
    string, its contents are decoded as Latin-1.

    By default, the key-value pairs extracted from ``s`` are combined into a
    `dict` with later occurrences of a key overriding previous occurrences of
    the same key.  To change this behavior, pass a callable as the
    ``object_pairs_hook`` argument; it will be called with one argument, a
    generator of ``(key, value)`` pairs representing the key-value entries in
    ``s`` (including duplicates) in order of occurrence.  `loads` will then
    return the value returned by ``object_pairs_hook``.

    .. versionchanged:: 0.5.0
        Invalid ``\\uXXXX`` escape sequences will now cause an
        `InvalidUEscapeError` to be raised

    :param string s: the string from which to read the ``.properties`` document
    :param callable object_pairs_hook: class or function for combining the
        key-value pairs
    :rtype: `dict` of text strings or the return value of ``object_pairs_hook``
    :raises InvalidUEscapeError: if an invalid ``\\uXXXX`` escape sequence
        occurs in the input
    """
    fp = BytesIO(s) if isinstance(s, binary_type) else StringIO(s)
    return load(fp, object_pairs_hook=object_pairs_hook)

def parse(fp):
    """
    Parse the contents of the `~io.IOBase.readline`-supporting file-like object
    ``fp`` as a simple line-oriented ``.properties`` file and return a
    generator of ``(key, value, original_lines)`` triples for every entry in
    ``fp`` (including duplicate keys) in order of occurrence.  The third
    element of each triple is the concatenation of the unmodified lines in
    ``fp`` (including trailing newlines) from which the key and value were
    extracted.  The generator also includes comments and blank/all-whitespace
    lines found in ``fp``, one triple per line, with the first two elements of
    the triples set to `None`.  This is the only way to extract comments from a
    ``.properties`` file with this library.

    ``fp`` may be either a text or binary filehandle, with or without universal
    newlines enabled.  If it is a binary filehandle, its contents are decoded
    as Latin-1.

    .. versionchanged:: 0.5.0
        Invalid ``\\uXXXX`` escape sequences will now cause an
        `InvalidUEscapeError` to be raised

    :param fp: the file from which to read the ``.properties`` document
    :type fp: file-like object
    :rtype: generator of triples of text strings
    :raises InvalidUEscapeError: if an invalid ``\\uXXXX`` escape sequence
        occurs in the input
    """
    def lineiter():
        while True:
            ln = fp.readline()
            if isinstance(ln, binary_type):
                ln = ln.decode('iso-8859-1')
            if ln == '':
                return
            for l in ascii_splitlines(ln):
                yield l
    liter = lineiter()
    for source in liter:
        line = source
        if re.match(r'^[ \t\f]*(?:[#!]|\r?\n?$)', line):
            yield (None, None, source)
            continue
        line = line.lstrip(' \t\f').rstrip('\r\n')
        while re.search(r'(?<!\\)(?:\\\\)*\\$', line):
            line = line[:-1]
            nextline = next(liter, '')
            source += nextline
            line += nextline.lstrip(' \t\f').rstrip('\r\n')
        if line == '':  # series of otherwise-blank lines with continuations
            yield (None, None, source)
            continue
        m = re.search(r'(?<!\\)(?:\\\\)*([ \t\f]*[=:]|[ \t\f])[ \t\f]*', line)
        if m:
            yield (unescape(line[:m.start(1)]),unescape(line[m.end():]),source)
        else:
            yield (unescape(line), '', source)

def unescape(field):
    """
    Decode escape sequences in a ``.properties`` key or value.  The following
    escape sequences are recognized::

        \\t \\n \\f \\r \\uXXXX \\\\

    If a backslash is followed by any other character, the backslash is
    dropped.

    In addition, any valid UTF-16 surrogate pairs in the string after
    escape-decoding are further decoded into the non-BMP characters they
    represent.  (Invalid & isolated surrogate code points are left as-is.)

    .. versionchanged:: 0.5.0
        Invalid ``\\uXXXX`` escape sequences will now cause an
        `InvalidUEscapeError` to be raised

    :param field: the string to decode
    :type field: text string
    :rtype: text string
    :raises InvalidUEscapeError: if an invalid ``\\uXXXX`` escape sequence
        occurs in the input
    """
    return re.sub(r'[\uD800-\uDBFF][\uDC00-\uDFFF]', _unsurrogate,
                  re.sub(r'\\(u.{0,4}|.)', _unesc, field))

_unescapes = {'t': '\t', 'n': '\n', 'f': '\f', 'r': '\r'}

def _unesc(m):
    esc = m.group(1)
    if esc[0] == 'u':
        if not re.match(r'^u[0-9A-Fa-f]{4}\Z', esc):
            # We can't rely on `int` failing, because it succeeds when `esc`
            # has trailing whitespace or a leading minus.
            raise InvalidUEscapeError('\\' + esc)
        return unichr(int(esc[1:], 16))
    else:
        return _unescapes.get(esc, esc)

def _unsurrogate(m):
    c,d = map(ord, m.group())
    return unichr(((c - 0xD800) << 10) + (d - 0xDC00) + 0x10000)


class InvalidUEscapeError(ValueError):
    """
    .. versionadded:: 0.5.0

    Raised when an invalid ``\\uXXXX`` escape sequence (i.e., a ``\\u`` not
    immediately followed by four hexadecimal digits) is encountered in a simple
    line-oriented ``.properties`` file
    """

    def __init__(self, escape):
        #: The invalid ``\uXXXX`` escape sequence encountered
        self.escape = escape
        super(InvalidUEscapeError, self).__init__(escape)

    def __str__(self):
        return 'Invalid \\u escape sequence: ' + self.escape
