# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import array
from hashlib import md5
import os
import platform
import sys
import threading

PY2 = sys.version_info.major == 2

WIN = platform.system() == 'Windows'

if WIN:
    datadir = os.path.join(os.environ['APPDATA'], 'azure-datalake-store')
else:
    datadir = os.sep.join([os.path.expanduser("~"), '.config', 'azure-datalake-store'])

try:
    os.makedirs(datadir)
except:
    pass

def ensure_writable(b):
    if PY2 and isinstance(b, array.array):
        return b.tostring()
    return b


def write_stdout(data):
    """ Write bytes or strings to standard output
    """
    try:
        sys.stdout.buffer.write(data)
    except AttributeError:
        sys.stdout.write(data.decode('ascii', 'replace'))


def read_block(f, offset, length, delimiter=None):
    """ Read a block of bytes from a file

    Parameters
    ----------
    fn: file object
        a file object that supports seek, tell and read.
    offset: int
        Byte offset to start read
    length: int
        Maximum number of bytes to read
    delimiter: bytes (optional)
        Ensure reading stops at delimiter bytestring

    If using the ``delimiter=`` keyword argument we ensure that the read
    stops at or before the delimiter boundaries that follow the location
    ``offset + length``. For ADL, if no delimiter is found and the data
    requested is > 4MB an exception is raised, since a single record cannot
    exceed 4MB and be guaranteed to land contiguously in ADL.
    The bytestring returned WILL include the
    terminating delimiter string.

    Examples
    --------

    >>> from io import BytesIO  # doctest: +SKIP
    >>> f = BytesIO(b'Alice, 100\\nBob, 200\\nCharlie, 300')  # doctest: +SKIP
    >>> read_block(f, 0, 13)  # doctest: +SKIP
    b'Alice, 100\\nBo'

    >>> read_block(f, 0, 13, delimiter=b'\\n')  # doctest: +SKIP
    b'Alice, 100\\n'

    >>> read_block(f, 10, 10, delimiter=b'\\n')  # doctest: +SKIP
    b'\\nCharlie, 300'
    >>> f  = BytesIO(bytearray(2**22))  # doctest: +SKIP
    >>> read_block(f,0,2**22, delimiter=b'\\n')  # doctest: +SKIP
    IndexError: No delimiter found within max record size of 4MB. 
    Transfer without specifying a delimiter (as binary) instead.
    """
    f.seek(offset)
    bytes = f.read(length)
    if delimiter:
        # max record size is 4MB
        max_record = 2**22
        if length > max_record:
            raise IndexError('Records larger than ' + str(max_record) + ' bytes are not supported. The length requested was: ' + str(length) + 'bytes')
        # get the last index of the delimiter if it exists
        try:
            last_delim_index = len(bytes) -1 - bytes[::-1].index(delimiter)
            # this ensures the length includes all of the last delimiter (in the event that it is more than one character)
            length = last_delim_index + len(delimiter)
            return bytes[0:length]
        except ValueError:
            # TODO: Before delimters can be supported through the ADLUploader logic, the number of chunks being uploaded 
            # needs to be visible to this method, since it needs to throw if:
            # 1. We cannot find a delimiter in <= 4MB of data
            # 2. If the remaining size is less than 4MB but there are multiple chunks that need to be stitched together,
            #   since the delimiter could be split across chunks.
            # 3. If delimiters are specified, there must be logic during segment determination that ensures all chunks
            #   terminate at the end of a record (on a new line), even if that makes the chunk < 256MB.
            if length >= max_record:
                raise IndexError('No delimiter found within max record size of ' + str(max_record) + ' bytes. Transfer without specifying a delimiter (as binary) instead.')
    
    return bytes

def tokenize(*args, **kwargs):
    """ Deterministic token

    >>> tokenize('Hello') == tokenize('Hello')
    True
    """
    if kwargs:
        args = args + (kwargs,)
    return md5(str(tuple(args)).encode()).hexdigest()


def commonprefix(paths):
    """ Find common directory for all paths

    Python's ``os.path.commonprefix`` will not return a valid directory path in
    some cases, so we wrote this convenience method.

    Examples
    --------

    >>> # os.path.commonprefix returns '/disk1/foo'
    >>> commonprefix(['/disk1/foobar', '/disk1/foobaz'])
    '/disk1'

    >>> commonprefix(['a/b/c', 'a/b/d', 'a/c/d'])
    'a'

    >>> commonprefix(['a/b/c', 'd/e/f', 'g/h/i'])
    ''
    """
    return os.path.dirname(os.path.commonprefix(paths))


def clamp(n, smallest, largest):
    """ Limit a value to a given range

    This is equivalent to smallest <= n <= largest.

    Examples
    --------

    >>> clamp(0, 1, 100)
    1

    >>> clamp(42, 2, 128)
    42

    >>> clamp(1024, 1, 32)
    32
    """
    return max(smallest, min(n, largest))


class CountUpDownLatch:
    """CountUpDownLatch provides a thread safe implementation of Up Down latch
    """
    def __init__(self):
        self.lock = threading.Condition()
        self.val = 0
        self.total = 0

    def increment(self):
        self.lock.acquire()
        self.val += 1
        self.total += 1
        self.lock.release()

    def decrement(self):
        self.lock.acquire()
        self.val -= 1
        if self.val <= 0:
            self.lock.notifyAll()
        self.lock.release()

    def total_processed(self):
        self.lock.acquire()
        temp = self.total
        self.lock.release()
        return temp

    def is_zero(self):
        self.lock.acquire()
        while self.val > 0:
            self.lock.wait()
        self.lock.release()
        return True
