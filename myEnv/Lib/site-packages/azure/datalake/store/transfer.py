# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Low-level classes for managing data transfer.
"""
from __future__ import print_function

from collections import namedtuple, Counter
from concurrent.futures import ThreadPoolExecutor
import logging
import multiprocessing
import signal
import sys
import threading
import time
import uuid
import operator
import os

from .exceptions import DatalakeIncompleteTransferException

logger = logging.getLogger(__name__)


class StateManager(object):
    """
    Manages state for any hashable object.

    When tracking multiple files and their chunks, each file/chunk can be in
    any valid state for that particular type.

    At the simplest level, we need to set and retrieve an object's current
    state, while only allowing valid states to be used. In addition, we also
    need to give statistics about a group of objects (are all objects in one
    state? how many objects are in each available state?).

    Parameters
    ----------
    states: list of valid states
        Managed objects can only use these defined states.

    Examples
    --------
    >>> StateManager('draft', 'review', 'complete')  # doctest: +SKIP
    <StateManager: draft=0 review=0 complete=0>
    >>> mgr = StateManager('off', 'on')
    >>> mgr['foo'] = 'on'
    >>> mgr['bar'] = 'off'
    >>> mgr['quux'] = 'on'
    >>> mgr  # doctest: +SKIP
    <StateManager: off=1 on=2>
    >>> mgr.contains_all('on')
    False
    >>> mgr['bar'] = 'on'
    >>> mgr.contains_all('on')
    True
    >>> mgr.contains_none('off')
    True

    Internal class used by `ADLTransferClient`.
    """
    def __init__(self, *states):
        self._states = {state: set() for state in states}
        self._objects = {}

    @property
    def states(self):
        return list(self._states)

    @property
    def objects(self):
        return list(self._objects)

    def __iter__(self):
        return iter(self._objects.items())

    def __getitem__(self, obj):
        return self._objects[obj]

    def __setitem__(self, obj, state):
        if obj in self._objects:
            self._states[self._objects[obj]].discard(obj)
        self._states[state].add(obj)
        self._objects[obj] = state

    def contains_all(self, state):
        """ Return whether all managed objects are in the given state """
        objs = self._states[state]
        return len(objs) > 0 and len(self.objects) - len(objs) == 0

    def contains_none(self, *states):
        """ Return whether no managed objects are in the given states """
        return all([len(self._states[state]) == 0 for state in states])

    def __str__(self):
        status = " ".join(
            ["%s=%d" % (s, len(self._states[s])) for s in self._states])
        return "<StateManager: " + status + ">"

    __repr__ = __str__


# Named tuples used to serialize client progress
File = namedtuple('File', 'src dst state length chunks exception')
Chunk = namedtuple('Chunk', 'name state offset expected actual exception')


class ADLTransferClient(object):
    """
    Client for transferring data from/to Azure DataLake Store

    This is intended as the underlying class for `ADLDownloader` and
    `ADLUploader`. If necessary, it can be used directly for additional
    control.

    Parameters
    ----------
    adlfs: ADL filesystem instance
    name: str
        Unique ID used for persistence.
    transfer: callable
        Function or callable object invoked when transferring chunks. See
        ``Function Signatures``.
    merge: callable [None]
        Function or callable object invoked when merging chunks. For each file
        containing only one chunk, no merge function will be called, even if
        provided. If None, then merging is skipped. See
        ``Function Signatures``.
    nthreads: int [None]
        Number of threads to use (minimum is 1). If None, uses the number of
        cores.
    chunksize: int [2**28]
        Number of bytes for a chunk. Large files are split into chunks. Files
        smaller than this number will always be transferred in a single thread.
    buffersize: int [2**25]
        Number of bytes for internal buffer. This block cannot be bigger than
        a chunk and cannot be smaller than a block.
    blocksize: int [2**25]
        Number of bytes for a block. Within each chunk, we write a smaller
        block for each API call. This block cannot be bigger than a chunk.
    chunked: bool [True]
        If set, each transferred chunk is stored in a separate file until
        chunks are gathered into a single file. Otherwise, each chunk will be
        written into the same destination file.
    unique_temporary: bool [True]
        If set, transferred chunks are written into a unique temporary
        directory.
    persist_path: str [None]
        Path used for persisting a client's state. If None, then `save()`
        and `load()` will be empty operations.
    delimiter: byte(s) or None
        If set, will transfer blocks using delimiters, as well as split
        files for transferring on that delimiter.
    parent: ADLDownloader, ADLUploader or None
        In typical usage, the transfer client is created in the context of an
        upload or download, which can be persisted between sessions.        
    progress_callback: callable [None]
        Callback for progress with signature function(current, total) where
        current is the number of bytes transferred so far, and total is the
        size of the blob, or None if the total size is unknown.
    timeout: int (0)
        Default value 0 means infinite timeout. Otherwise time in seconds before the
        process will stop and raise an exception if  transfer is still in progress

    Temporary Files
    ---------------

    When a merge step is available, the client will write chunks to temporary
    files before merging. The exact temporary file looks like this in
    pseudo-BNF:

    >>> # {dirname}/{basename}.segments[.{unique_str}]/{basename}_{offset}

    Function Signatures
    -------------------

    To perform the actual work needed by the client, the user must pass in two
    callables, `transfer` and `merge`. If merge is not provided, then the
    merge step will be skipped.

    The `transfer` callable has the function signature,
    `fn(adlfs, src, dst, offset, size, buffersize, blocksize, shutdown_event)`.
    `adlfs` is the ADL filesystem instance. `src` and `dst` refer to the source
    and destination of the respective file transfer. `offset` is the location
    in `src` to read `size` bytes from. `buffersize` is the number of bytes
    used for internal buffering before transfer. `blocksize` is the number of
    bytes in a chunk to write at one time. The callable should return an
    integer representing the number of bytes written.

    The `merge` callable has the function signature,
    `fn(adlfs, outfile, files, shutdown_event)`. `adlfs` is the ADL filesystem
    instance. `outfile` is the result of merging `files`.

    For both transfer callables, `shutdown_event` is optional. In particular,
    `shutdown_event` is a `threading.Event` that is passed to the callable.
    The event will be set when a shutdown is requested. It is good practice
    to listen for this.

    Internal State
    --------------

    self._fstates: StateManager
        This captures the current state of each transferred file.
    self._files: dict
        Using a tuple of the file source/destination as the key, this
        dictionary stores the file metadata and all chunk states. The
        dictionary key is `(src, dst)` and the value is
        `dict(length, cstates, exception)`.
    self._chunks: dict
        Using a tuple of the chunk name/offset as the key, this dictionary
        stores the chunk metadata and has a reference to the chunk's parent
        file. The dictionary key is `(name, offset)` and the value is
        `dict(parent=(src, dst), expected, actual, exception)`.
    self._ffutures: dict
        Using a Future object as the key, this dictionary provides a reverse
        lookup for the file associated with the given future. The returned
        value is the file's primary key, `(src, dst)`.
    self._cfutures: dict
        Using a Future object as the key, this dictionary provides a reverse
        lookup for the chunk associated with the given future. The returned
        value is the chunk's primary key, `(name, offset)`.

    See Also
    --------
    azure.datalake.store.multithread.ADLDownloader
    azure.datalake.store.multithread.ADLUploader
    """

    def __init__(self, adlfs, transfer, merge=None, nthreads=None,
                 chunksize=2**28, blocksize=2**25, chunked=True,
                 unique_temporary=True, delimiter=None,
                 parent=None, verbose=False, buffersize=2**25,
                 progress_callback=None, timeout=0):
        self._adlfs = adlfs
        self._parent = parent
        self._transfer = transfer
        self._merge = merge
        self._nthreads = max(1, nthreads or multiprocessing.cpu_count())
        self._chunksize = chunksize
        self._buffersize = buffersize
        self._blocksize = blocksize
        self._chunked = chunked
        self._unique_temporary = unique_temporary
        self._unique_str = uuid.uuid4().hex
        self._progress_callback=progress_callback
        self._progress_lock = threading.Lock()
        self._timeout = timeout
        self.verbose = verbose

        # Internal state tracking files/chunks/futures
        self._progress_total_bytes = 0
        self._transfer_total_bytes = 0

        self._files = {}
        self._chunks = {}
        self._ffutures = {}
        self._cfutures = {}
        self._fstates = StateManager(
            'pending', 'transferring', 'merging', 'finished', 'cancelled',
            'errored')

    def submit(self, src, dst, length):
        """
        Split a given file into chunks.

        All submitted files/chunks start in the `pending` state until `run()`
        is called.
        """
        cstates = StateManager(
            'pending', 'running', 'finished', 'cancelled', 'errored')

        # Create unique temporary directory for each file
        if self._chunked:
            if self._unique_temporary:
                filename = "{}.segments.{}".format(dst.name, self._unique_str)
            else:
                filename = "{}.segments".format(dst.name)
            tmpdir = dst.parent/filename
        else:
            tmpdir = None

        # TODO: might need xrange support for py2
        offsets = range(0, length, self._chunksize)

        # in the case of empty files, ensure that the initial offset of 0 is properly added.
        if not offsets:
            if not length:
                offsets = [0]
            else:
                raise DatalakeIncompleteTransferException('Could not compute offsets for source: {}, with destination: {} and expected length: {}.'.format(src, dst, length))

        tmpdir_and_offsets = tmpdir and len(offsets) > 1
        for offset in offsets:
            if tmpdir_and_offsets:
                name = tmpdir / "{}_{}".format(dst.name, offset)
            else:
                name = dst
            cstates[(name, offset)] = 'pending'
            self._chunks[(name, offset)] = {
                "parent": (src, dst),
                "expected": min(length - offset, self._chunksize),
                "actual": 0,
                "exception": None}
            logger.debug("Submitted %s, byte offset %d", name, offset)

        self._fstates[(src, dst)] = 'pending'
        self._files[(src, dst)] = {
            "length": length,
            "cstates": cstates,
            "exception": None}
        self._transfer_total_bytes += length

    def _start(self, src, dst):
        key = (src, dst)
        self._fstates[key] = 'transferring'
        for obj in self._files[key]['cstates'].objects:
            name, offset = obj
            cs = self._files[key]['cstates']
            if obj in cs.objects and cs[obj] == 'finished':
                continue
            cs[obj] = 'running'
            future = self._pool.submit(
                self._transfer, self._adlfs, src, name, offset,
                self._chunks[obj]['expected'], self._buffersize,
                self._blocksize, shutdown_event=self._shutdown_event)
            self._cfutures[future] = obj
            future.add_done_callback(self._update)

    @property
    def active(self):
        """ Return whether the transfer is active """
        return not self._fstates.contains_none('pending', 'transferring', 'merging')

    @property
    def successful(self):
        """
        Return whether the transfer completed successfully.

        It will raise AssertionError if the transfer is active.
        """
        assert not self.active
        return self._fstates.contains_all('finished')

    @property
    def progress(self):
        """ Return a summary of all transferred file/chunks """
        files = []
        for key in self._files:
            src, dst = key
            chunks = []
            for obj in self._files[key]['cstates'].objects:
                name, offset = obj
                chunks.append(Chunk(
                    name=name,
                    offset=offset,
                    state=self._files[key]['cstates'][obj],
                    expected=self._chunks[obj]['expected'],
                    actual=self._chunks[obj]['actual'],
                    exception=self._chunks[obj]['exception']))
            files.append(File(
                src=src,
                dst=dst,
                state=self._fstates[key],
                length=self._files[key]['length'],
                chunks=chunks,
                exception=self._files[key]['exception']))
        return files
    
    def _rename_file(self, src, dst, overwrite=False):
        """ Rename a file from file_name.inprogress to just file_name. Invoked once download completes on a file.

        Internal function used by `download`.
        """
        try:
            # we do a final check to make sure someone didn't create the destination file while download was occuring
            # if the user did not specify overwrite.
            if os.path.isfile(dst):
                if not overwrite:
                    raise FileExistsError(dst)
                os.remove(dst)
            os.rename(src, dst)
        except Exception as e:
            logger.error('Rename failed for source file: %r; %r', src, e)
            raise e
    
        logger.debug('Renamed %r to %r', src, dst)

    def _update_progress(self, length):
        if self._progress_callback is not None:
            with self._progress_lock:
                self._progress_total_bytes += length
            self._progress_callback(self._progress_total_bytes, self._transfer_total_bytes)

    def _update(self, future):

        if future in self._cfutures:
            obj = self._cfutures[future]
            parent = self._chunks[obj]['parent']
            cstates = self._files[parent]['cstates']
            src, dst = parent

            if future.cancelled():
                cstates[obj] = 'cancelled'
            elif future.exception():
                self._chunks[obj]['exception'] = repr(future.exception())
                cstates[obj] = 'errored'
            else:
                nbytes, exception = future.result()
                self._chunks[obj]['actual'] = nbytes
                self._chunks[obj]['exception'] = exception
                if exception:
                    cstates[obj] = 'errored'
                elif self._chunks[obj]['expected'] != nbytes:
                    name, offset = obj
                    cstates[obj] = 'errored'
                    exception = DatalakeIncompleteTransferException(
                        'chunk {}, offset {}: expected {} bytes, transferred {} bytes'.format(
                            name, offset, self._chunks[obj]['expected'],
                            self._chunks[obj]['actual']))
                    self._chunks[obj]['exception'] = exception
                    logger.error("Incomplete transfer: %s -> %s, %s",
                                 src, dst, repr(exception))
                else:
                    cstates[obj] = 'finished'
                    self._update_progress(nbytes)

            if cstates.contains_all('finished'):
                logger.debug("Chunks transferred")
                if self._merge and len(cstates.objects) > 1:
                    logger.debug("Merging file: %s", self._fstates[parent])
                    self._fstates[parent] = 'merging'
                    merge_future = self._pool.submit(
                        self._merge, self._adlfs, dst,
                        [chunk for chunk, _ in sorted(cstates.objects,
                                                      key=operator.itemgetter(1))], 
                        overwrite=self._parent._overwrite,
                        shutdown_event=self._shutdown_event)
                    self._ffutures[merge_future] = parent
                    merge_future.add_done_callback(self._update)
                else:
                    if not self._chunked and str(dst).endswith('.inprogress'):
                        logger.debug("Renaming file to remove .inprogress: %s", self._fstates[parent])
                        self._fstates[parent] = 'merging'    
                        self._rename_file(dst, dst.replace('.inprogress',''), overwrite=self._parent._overwrite)
                        dst = dst.replace('.inprogress', '')

                    self._fstates[parent] = 'finished'
                    logger.info("Transferred %s -> %s", src, dst)
            elif cstates.contains_none('running', 'pending'):
                logger.error("Transfer failed: %s -> %s", src, dst)
                self._fstates[parent] = 'errored'
        elif future in self._ffutures:
            src, dst = self._ffutures[future]

            if future.cancelled():
                self._fstates[(src, dst)] = 'cancelled'
            elif future.exception():
                self._files[(src, dst)]['exception'] = repr(future.exception())
                self._fstates[(src, dst)] = 'errored'
            else:
                exception = future.result()
                self._files[(src, dst)]['exception'] = exception
                if exception:
                    self._fstates[(src, dst)] = 'errored'
                else:
                    self._fstates[(src, dst)] = 'finished'
                    logger.info("Transferred %s -> %s", src, dst)
        # TODO: Re-enable progress saving when a less IO intensive solution is available.
        # See issue: https://github.com/Azure/azure-data-lake-store-python/issues/117
        #self.save()
        else:
            raise ValueError("Illegal state future {} not found in either file futures {} nor chunk futures {}"
                             .format(future, self._ffutures, self._cfutures))
        if self.verbose:
            print('\b' * 200, self.status, end='')
            sys.stdout.flush()

    @property
    def status(self):
        c = sum([Counter([c.state for c in f.chunks]) for f in
                 self.progress], Counter())
        return dict(c)

    def run(self, nthreads=None, monitor=True, before_start=None):
        self._pool = ThreadPoolExecutor(self._nthreads)
        self._shutdown_event = threading.Event()
        self._nthreads = nthreads or self._nthreads
        self._ffutures = {}
        self._cfutures = {}

        for src, dst in self._files:
            if before_start:
                before_start(self._adlfs, src, dst)
            self._start(src, dst)

        if monitor:
            self.monitor(timeout=self._timeout)
            has_errors = False
            error_list = []
            for f in self.progress:
                for chunk in f.chunks:
                    if chunk.state == 'finished':
                        continue
                    if chunk.exception:
                        error_string = '{} -> {}, chunk {} {}: {}, {}'.format(
                            f.src, f.dst, chunk.name, chunk.offset,
                            chunk.state, repr(chunk.exception))
                        logger.error(error_string)
                        has_errors = True
                        error_list.append(error_string)
                    else:
                        error_string = '{} -> {}, chunk {} {}: {}'.format(
                            f.src, f.dst, chunk.name, chunk.offset,
                            chunk.state)
                        logger.error(error_string)
                        error_list.append(error_string)
                        has_errors = True
            if has_errors:
                raise DatalakeIncompleteTransferException('One more more exceptions occured during transfer, resulting in an incomplete transfer. \n\n List of exceptions and errors:\n {}'.format('\n'.join(error_list)))

    def _wait(self, poll=0.1, timeout=0):
        start = time.time()
        while self.active:
            if timeout > 0 and time.time() - start > timeout:
                break
            time.sleep(poll)

    def _clear(self):
        self._cfutures = {}
        self._ffutures = {}
        self._pool = None

    def shutdown(self):
        """
        Shutdown task threads in an orderly fashion.

        Within the context of this method, we disable Ctrl+C keystroke events
        until all threads have exited. We re-enable Ctrl+C keystroke events
        before leaving.
        """
        handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            logger.debug("Shutting down worker threads")
            self._shutdown_event.set()
            self._pool.shutdown(wait=True)
        except Exception as e:
            logger.error("Unexpected exception occurred during shutdown: %s", repr(e))
        else:
            logger.debug("Shutdown complete")
        finally:
            signal.signal(signal.SIGINT, handler)

    def monitor(self, poll=0.1, timeout=0):
        """ Wait for download to happen """
        try:
            self._wait(poll, timeout)
        except KeyboardInterrupt:
            logger.warning("%s suspended and persisted", self)
            self.shutdown()
        self._clear()
        
        # TODO: Re-enable progress saving when a less IO intensive solution is available.
        # See issue: https://github.com/Azure/azure-data-lake-store-python/issues/117
        #self.save()

    def __getstate__(self):
        dic2 = self.__dict__.copy()
        dic2.pop('_cfutures', None)
        dic2.pop('_ffutures', None)
        dic2.pop('_pool', None)
        dic2.pop('_shutdown_event', None)
        dic2.pop('_progress_lock', None)

        dic2['_files'] = dic2.get('_files', {}).copy()
        dic2['_chunks'] = dic2.get('_chunks', {}).copy()

        return dic2

    def save(self, keep=True):
        if self._parent is not None:
            self._parent.save(keep=keep)
