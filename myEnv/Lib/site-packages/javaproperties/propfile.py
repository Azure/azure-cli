from   __future__  import print_function
from   collections import OrderedDict, namedtuple
import re
import six
from   .reading    import loads, parse
from   .writing    import join_key_value

if six.PY2:
    from collections     import Mapping, MutableMapping
else:
    from collections.abc import Mapping, MutableMapping

_type_err = 'Keys & values of PropertiesFile objects must be strings'

PropertyLine = namedtuple('PropertyLine', 'key value source')

class PropertiesFile(MutableMapping):
    """
    .. versionadded:: 0.3.0

    A custom mapping class for reading from, editing, and writing to a
    ``.properties`` file while preserving comments & whitespace in the original
    input.

    A `PropertiesFile` instance can be constructed from another mapping and/or
    iterable of pairs, after which it will act like an
    `~collections.OrderedDict`.  Alternatively, an instance can be constructed
    from a file or string with `PropertiesFile.load()` or
    `PropertiesFile.loads()`, and the resulting instance will remember the
    formatting of its input and retain that formatting when written back to a
    file or string with the `~PropertiesFile.dump()` or
    `~PropertiesFile.dumps()` method.  The formatting information attached to
    an instance ``pf`` can be forgotten by constructing another mapping from it
    via ``dict(pf)``, ``OrderedDict(pf)``, or even ``PropertiesFile(pf)`` (Use
    the `copy()` method if you want to create another `PropertiesFile` instance
    with the same data & formatting).

    When not reading or writing, `PropertiesFile` behaves like a normal
    `~collections.abc.MutableMapping` class (i.e., you can do ``props[key] =
    value`` and so forth), except that (a) like `~collections.OrderedDict`, key
    insertion order is remembered and is used when iterating & dumping (and
    `reversed` is supported), and (b) like `Properties`, it may only be used to
    store strings and will raise a `TypeError` if passed a non-string object as
    key or value.

    Two `PropertiesFile` instances compare equal iff both their key-value pairs
    and comment & whitespace lines are equal and in the same order.  When
    comparing a `PropertiesFile` to any other type of mapping, only the
    key-value pairs are considered, and order is ignored.

    `PropertiesFile` currently only supports reading & writing the simple
    line-oriented format, not XML.
    """

    def __init__(self, mapping=None, **kwargs):
        #: mapping from keys to list of line numbers
        self._indices = OrderedDict()
        #: mapping from line numbers to (key, value, source) tuples
        self._lines = OrderedDict()
        if mapping is not None:
            self.update(mapping)
        self.update(kwargs)

    def _check(self):
        """
        Assert the internal consistency of the instance's data structures.
        This method is for debugging only.
        """
        for k,ix in six.iteritems(self._indices):
            assert k is not None, 'null key'
            assert ix, 'Key does not map to any indices'
            assert ix == sorted(ix), "Key's indices are not in order"
            for i in ix:
                assert i in self._lines, 'Key index does not map to line'
                assert self._lines[i].key is not None, 'Key maps to comment'
                assert self._lines[i].key == k, 'Key does not map to itself'
                assert self._lines[i].value is not None, 'Key has null value'
        prev = None
        for i, line in six.iteritems(self._lines):
            assert prev is None or prev < i, 'Line indices out of order'
            prev = i
            if line.key is None:
                assert line.value is None, 'Comment/blank has value'
                assert line.source is not None, 'Comment source not stored'
                assert loads(line.source) == {}, 'Comment source is not comment'
            else:
                assert line.value is not None, 'Key has null value'
                if line.source is not None:
                    assert loads(line.source) == {line.key: line.value}, \
                        'Key source does not deserialize to itself'
                assert line.key in self._indices, 'Key is missing from map'
                assert i in self._indices[line.key], \
                    'Key does not map to itself'

    def __getitem__(self, key):
        if not isinstance(key, six.string_types):
            raise TypeError(_type_err)
        return self._lines[self._indices[key][-1]].value

    def __setitem__(self, key, value):
        if not isinstance(key, six.string_types) or \
                not isinstance(value, six.string_types):
            raise TypeError(_type_err)
        try:
            ixes = self._indices[key]
        except KeyError:
            try:
                lasti = next(reversed(self._lines))
            except StopIteration:
                ix = 0
            else:
                ix = lasti + 1
                # We're adding a line to the end of the file, so make sure the
                # line before it ends with a newline and (if it's not a
                # comment) doesn't end with a trailing line continuation.
                lastline = self._lines[lasti]
                if lastline.source is not None:
                    lastsrc = lastline.source
                    if lastline.key is not None:
                        lastsrc=re.sub(r'(?<!\\)((?:\\\\)*)\\$', r'\1', lastsrc)
                    if not lastsrc.endswith(('\r', '\n')):
                        lastsrc += '\n'
                    self._lines[lasti] = lastline._replace(source=lastsrc)
        else:
            # Update the first occurrence of the key and discard the rest.
            # This way, the order in which the keys are listed in the file and
            # dict will be preserved.
            ix = ixes.pop(0)
            for i in ixes:
                del self._lines[i]
        self._indices[key] = [ix]
        self._lines[ix] = PropertyLine(key, value, None)

    def __delitem__(self, key):
        if not isinstance(key, six.string_types):
            raise TypeError(_type_err)
        for i in self._indices.pop(key):
            del self._lines[i]

    def __iter__(self):
        return iter(self._indices)

    def __reversed__(self):
        return reversed(self._indices)

    def __len__(self):
        return len(self._indices)

    def _comparable(self):
        return [
            (None, line.source) if line.key is None else (line.key, line.value)
            for i, line in six.iteritems(self._lines)
            ### TODO: Also include non-final repeated keys???
            if line.key is None or self._indices[line.key][-1] == i
        ]

    def __eq__(self, other):
        if isinstance(other, PropertiesFile):
            return self._comparable() == other._comparable()
        ### TODO: Special-case OrderedDict?
        elif isinstance(other, Mapping):
            return dict(self) == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def load(cls, fp):
        """
        Parse the contents of the `~io.IOBase.readline`-supporting file-like
        object ``fp`` as a simple line-oriented ``.properties`` file and return
        a `PropertiesFile` instance.

        ``fp`` may be either a text or binary filehandle, with or without
        universal newlines enabled.  If it is a binary filehandle, its contents
        are decoded as Latin-1.

        .. versionchanged:: 0.5.0
            Invalid ``\\uXXXX`` escape sequences will now cause an
            `InvalidUEscapeError` to be raised

        :param fp: the file from which to read the ``.properties`` document
        :type fp: file-like object
        :rtype: PropertiesFile
        :raises InvalidUEscapeError: if an invalid ``\\uXXXX`` escape sequence
            occurs in the input
        """
        obj = cls()
        for i, (k, v, src) in enumerate(parse(fp)):
            if k is not None:
                obj._indices.setdefault(k, []).append(i)
            obj._lines[i] = PropertyLine(k, v, src)
        return obj

    @classmethod
    def loads(cls, s):
        """
        Parse the contents of the string ``s`` as a simple line-oriented
        ``.properties`` file and return a `PropertiesFile` instance.

        ``s`` may be either a text string or bytes string.  If it is a bytes
        string, its contents are decoded as Latin-1.

        .. versionchanged:: 0.5.0
            Invalid ``\\uXXXX`` escape sequences will now cause an
            `InvalidUEscapeError` to be raised

        :param string s: the string from which to read the ``.properties``
            document
        :rtype: PropertiesFile
        :raises InvalidUEscapeError: if an invalid ``\\uXXXX`` escape sequence
            occurs in the input
        """
        if isinstance(s, six.binary_type):
            fp = six.BytesIO(s)
        else:
            fp = six.StringIO(s)
        return cls.load(fp)

    def dump(self, fp, separator='='):
        """
        Write the mapping to a file in simple line-oriented ``.properties``
        format.

        If the instance was originally created from a file or string with
        `PropertiesFile.load()` or `PropertiesFile.loads()`, then the output
        will include the comments and whitespace from the original input, and
        any keys that haven't been deleted or reassigned will retain their
        original formatting and multiplicity.  Key-value pairs that have been
        modified or added to the mapping will be reformatted with
        `join_key_value()` using the given separator.  All key-value pairs are
        output in the order they were defined, with new keys added to the end.

        .. note::

            Serializing a `PropertiesFile` instance with the :func:`dump()`
            function instead will cause all formatting information to be
            ignored, as :func:`dump()` will treat the instance like a normal
            mapping.

        :param fp: A file-like object to write the mapping to.  It must have
            been opened as a text file with a Latin-1-compatible encoding.
        :param separator: The string to use for separating new or modified keys
            & values.  Only ``" "``, ``"="``, and ``":"`` (possibly with added
            whitespace) should ever be used as the separator.
        :type separator: text string
        :return: `None`
        """
        ### TODO: Support setting the timestamp
        for line in six.itervalues(self._lines):
            if line.source is None:
                print(join_key_value(line.key, line.value, separator), file=fp)
            else:
                fp.write(line.source)

    def dumps(self, separator='='):
        """
        Convert the mapping to a text string in simple line-oriented
        ``.properties`` format.

        If the instance was originally created from a file or string with
        `PropertiesFile.load()` or `PropertiesFile.loads()`, then the output
        will include the comments and whitespace from the original input, and
        any keys that haven't been deleted or reassigned will retain their
        original formatting and multiplicity.  Key-value pairs that have been
        modified or added to the mapping will be reformatted with
        `join_key_value()` using the given separator.  All key-value pairs are
        output in the order they were defined, with new keys added to the end.

        .. note::

            Serializing a `PropertiesFile` instance with the :func:`dumps()`
            function instead will cause all formatting information to be
            ignored, as :func:`dumps()` will treat the instance like a normal
            mapping.

        :param separator: The string to use for separating new or modified keys
            & values.  Only ``" "``, ``"="``, and ``":"`` (possibly with added
            whitespace) should ever be used as the separator.
        :type separator: text string
        :rtype: text string
        """
        s = six.StringIO()
        self.dump(s, separator=separator)
        return s.getvalue()

    def copy(self):
        """ Create a copy of the mapping, including formatting information """
        dup = type(self)()
        dup._indices = OrderedDict(
            (k, list(v)) for k,v in six.iteritems(self._indices)
        )
        dup._lines = self._lines.copy()
        return dup
