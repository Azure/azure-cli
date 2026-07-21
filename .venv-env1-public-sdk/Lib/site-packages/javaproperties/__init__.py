# -*- coding: utf-8 -*-
"""
Read & write Java .properties files

``javaproperties`` provides support for reading & writing Java ``.properties``
files (both the simple line-oriented format and XML) with a simple API based on
the ``json`` module — though, for recovering Java addicts, it also includes a
``Properties`` class intended to match the behavior of Java 8's
``java.util.Properties`` as much as is Pythonically possible.

Visit <https://github.com/jwodder/javaproperties> or
<http://javaproperties.rtfd.io> for more information.
"""

from .propclass import Properties
from .propfile  import PropertiesFile
from .reading   import InvalidUEscapeError, load, loads, parse, unescape
from .writing   import dump, dumps, java_timestamp, join_key_value, escape, \
                        to_comment
from .xmlprops  import load_xml, loads_xml, dump_xml, dumps_xml

__version__      = '0.5.2'
__author__       = 'John Thorvald Wodder II'
__author_email__ = 'javaproperties@varonathe.org'
__license__      = 'MIT'
__url__          = 'https://github.com/jwodder/javaproperties'

__all__ = [
    'InvalidUEscapeError',
    'Properties',
    'PropertiesFile',
    'dump',
    'dump_xml',
    'dumps',
    'dumps_xml',
    'escape',
    'java_timestamp',
    'join_key_value',
    'load',
    'load_xml',
    'loads',
    'loads_xml',
    'parse',
    'to_comment',
    'unescape',
]
