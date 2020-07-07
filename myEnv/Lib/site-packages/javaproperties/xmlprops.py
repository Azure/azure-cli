from   __future__            import print_function, unicode_literals
import codecs
import xml.etree.ElementTree as ET
from   xml.sax.saxutils      import escape, quoteattr
from   .util                 import itemize

def load_xml(fp, object_pairs_hook=dict):
    r"""
    Parse the contents of the file-like object ``fp`` as an XML properties file
    and return a `dict` of the key-value pairs.

    Beyond basic XML well-formedness, `load_xml` only checks that the root
    element is named "``properties``" and that all of its ``<entry>`` children
    have ``key`` attributes.  No further validation is performed; if any
    ``<entry>``\ s happen to contain nested tags, the behavior is undefined.

    By default, the key-value pairs extracted from ``fp`` are combined into a
    `dict` with later occurrences of a key overriding previous occurrences of
    the same key.  To change this behavior, pass a callable as the
    ``object_pairs_hook`` argument; it will be called with one argument, a
    generator of ``(key, value)`` pairs representing the key-value entries in
    ``fp`` (including duplicates) in order of occurrence.  `load_xml` will then
    return the value returned by ``object_pairs_hook``.

    .. note::

        This uses `xml.etree.ElementTree` for parsing, which does not have
        decent support for |unicode|_ input in Python 2.  Files containing
        non-ASCII characters need to be opened in binary mode in Python 2,
        while Python 3 accepts both binary and text input.

    :param fp: the file from which to read the XML properties document
    :type fp: file-like object
    :param callable object_pairs_hook: class or function for combining the
        key-value pairs
    :rtype: `dict` or the return value of ``object_pairs_hook``
    :raises ValueError: if the root of the XML tree is not a ``<properties>``
        tag or an ``<entry>`` element is missing a ``key`` attribute
    """
    tree = ET.parse(fp)
    return object_pairs_hook(_fromXML(tree.getroot()))

def loads_xml(s, object_pairs_hook=dict):
    r"""
    Parse the contents of the string ``s`` as an XML properties document and
    return a `dict` of the key-value pairs.

    Beyond basic XML well-formedness, `loads_xml` only checks that the root
    element is named "``properties``" and that all of its ``<entry>`` children
    have ``key`` attributes.  No further validation is performed; if any
    ``<entry>``\ s happen to contain nested tags, the behavior is undefined.

    By default, the key-value pairs extracted from ``s`` are combined into a
    `dict` with later occurrences of a key overriding previous occurrences of
    the same key.  To change this behavior, pass a callable as the
    ``object_pairs_hook`` argument; it will be called with one argument, a
    generator of ``(key, value)`` pairs representing the key-value entries in
    ``s`` (including duplicates) in order of occurrence.  `loads_xml` will then
    return the value returned by ``object_pairs_hook``.

    .. note::

        This uses `xml.etree.ElementTree` for parsing, which does not have
        decent support for |unicode|_ input in Python 2.  Strings containing
        non-ASCII characters need to be encoded as bytes in Python 2 (Use
        either UTF-8 or UTF-16 if the XML document does not contain an encoding
        declaration), while Python 3 accepts both binary and text input.

    :param string s: the string from which to read the XML properties document
    :param callable object_pairs_hook: class or function for combining the
        key-value pairs
    :rtype: `dict` or the return value of ``object_pairs_hook``
    :raises ValueError: if the root of the XML tree is not a ``<properties>``
        tag or an ``<entry>`` element is missing a ``key`` attribute
    """
    elem = ET.fromstring(s)
    return object_pairs_hook(_fromXML(elem))

def _fromXML(root):
    if root.tag != 'properties':
        raise ValueError('XML tree is not rooted at <properties>')
    for entry in root.findall('entry'):
        key = entry.get('key')
        if key is None:
            raise ValueError('<entry> is missing "key" attribute')
        yield (key, entry.text)

def dump_xml(props, fp, comment=None, encoding='UTF-8', sort_keys=False):
    """
    Write a series ``props`` of key-value pairs to a binary filehandle ``fp``
    in the format of an XML properties file.  The file will include both an XML
    declaration and a doctype declaration.

    :param props: A mapping or iterable of ``(key, value)`` pairs to write to
        ``fp``.  All keys and values in ``props`` must be text strings.  If
        ``sort_keys`` is `False`, the entries are output in iteration order.
    :param fp: a file-like object to write the values of ``props`` to
    :type fp: binary file-like object
    :param comment: if non-`None`, ``comment`` will be output as a
        ``<comment>`` element before the ``<entry>`` elements
    :type comment: text string or `None`
    :param string encoding: the name of the encoding to use for the XML
        document (also included in the XML declaration)
    :param bool sort_keys: if true, the elements of ``props`` are sorted
        lexicographically by key in the output
    :return: `None`
    """
    fp = codecs.lookup(encoding).streamwriter(fp, errors='xmlcharrefreplace')
    print('<?xml version="1.0" encoding={0} standalone="no"?>'
          .format(quoteattr(encoding)), file=fp)
    for s in _stream_xml(props, comment, sort_keys):
        print(s, file=fp)

def dumps_xml(props, comment=None, sort_keys=False):
    """
    Convert a series ``props`` of key-value pairs to a text string containing
    an XML properties document.  The document will include a doctype
    declaration but not an XML declaration.

    :param props: A mapping or iterable of ``(key, value)`` pairs to serialize.
        All keys and values in ``props`` must be text strings.  If
        ``sort_keys`` is `False`, the entries are output in iteration order.
    :param comment: if non-`None`, ``comment`` will be output as a
        ``<comment>`` element before the ``<entry>`` elements
    :type comment: text string or `None`
    :param bool sort_keys: if true, the elements of ``props`` are sorted
        lexicographically by key in the output
    :rtype: text string
    """
    return ''.join(s + '\n' for s in _stream_xml(props, comment, sort_keys))

def _stream_xml(props, comment=None, sort_keys=False):
    yield '<!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">'
    yield '<properties>'
    if comment is not None:
        yield '<comment>' + escape(comment) + '</comment>'
    for k,v in itemize(props, sort_keys=sort_keys):
        yield '<entry key={0}>{1}</entry>'.format(quoteattr(k), escape(v))
    yield '</properties>'
