# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
High performance multi-threaded module to up/download

Calls method in `core` with thread pool executor to ensure the network
is used to its maximum throughput.

Only implements upload and download of (massive) files and directory trees.
"""
from contextlib import closing
import glob
import logging
import os
import pickle
import time
import errno
import uuid

from io import open
from .core import AzureDLPath, _fetch_range
from .exceptions import FileExistsError, FileNotFoundError
from .transfer import ADLTransferClient
from .utils import datadir, read_block, tokenize
from .retry import ExponentialRetryPolicy

logger = logging.getLogger(__name__)


def save(instance, filename, keep=True):
    if os.path.exists(filename):
        all_downloads = load(filename)
    else:
        all_downloads = {}
    if not instance.client._fstates.contains_all('finished') and keep:
        all_downloads[instance._name] = instance
    else:
        all_downloads.pop(instance._name, None)
    try:
        # persist failure should not halt things
        with open(filename, 'wb') as f:
            pickle.dump(all_downloads, f)
    except IOError:
        logger.debug("Persist failed: %s" % filename)


def load(filename):
    try:
        return pickle.load(open(filename, 'rb'))
    except:
        return {}


class ADLDownloader(object):
    """ Download remote file(s) using chunks and threads

    Launches multiple threads for efficient downloading, with `chunksize`
    assigned to each. The remote path can be a single file, a directory
    of files or a glob pattern.

    Parameters
    ----------
    adlfs: ADL filesystem instance
    rpath: str
        remote path/globstring to use to find remote files. Recursive glob
        patterns using `**` are not supported.
    lpath: str
        local path. If downloading a single file, will write to this specific
        file, unless it is an existing directory, in which case a file is
        created within it. If downloading multiple files, this is the root
        directory to write within. Will create directories as required.
    nthreads: int [None]
        Number of threads to use. If None, uses the number of cores.
    chunksize: int [2**28]
        Number of bytes for a chunk. Large files are split into chunks. Files
        smaller than this number will always be transferred in a single thread.
    buffersize: int [2**22]
        Ignored in curret implementation.
        Number of bytes for internal buffer. This block cannot be bigger than
        a chunk and cannot be smaller than a block.
    blocksize: int [2**22]
        Number of bytes for a block. Within each chunk, we write a smaller
        block for each API call. This block cannot be bigger than a chunk.
    client: ADLTransferClient [None]
        Set an instance of ADLTransferClient when finer-grained control over
        transfer parameters is needed. Ignores `nthreads` and `chunksize` set
        by constructor.
    run: bool [True]
        Whether to begin executing immediately.
    overwrite: bool [False]
        Whether to forcibly overwrite existing files/directories. If False and
        local path is a directory, will quit regardless if any files would be
        overwritten or not. If True, only matching filenames are actually
        overwritten.
    progress_callback: callable [None]
        Callback for progress with signature function(current, total) where
        current is the number of bytes transfered so far, and total is the
        size of the blob, or None if the total size is unknown.
    timeout: int (0)
        Default value 0 means infinite timeout. Otherwise time in seconds before the
        process will stop and raise an exception if  transfer is still in progress

    See Also
    --------
    azure.datalake.store.transfer.ADLTransferClient
    """
    def __init__(self, adlfs, rpath, lpath, nthreads=None, chunksize=2**28,
                 buffersize=2**22, blocksize=2**22, client=None, run=True,
                 overwrite=False, verbose=False, progress_callback=None, timeout=0):
        
        # validate that the src exists and the current user has access to it
        # this only validates access to the top level folder. If there are files
        # or folders underneath it that the user does not have access to the download
        # will fail on those files. We clean the path in case there are wildcards.
        # In this case, we will always invalidate the cache for this check to 
        # do our best to ensure that the path exists as close to run time of the transfer as possible.
        # Due to the nature of a distributed filesystem, the path could be deleted later during execution,
        # at which point the transfer's behavior may be non-deterministic, but it will indicate an error.
        if not adlfs.exists(AzureDLPath(rpath).globless_prefix, invalidate_cache=True):
            raise FileNotFoundError('Data Lake item at path: {} either does not exist or the current user does not have permission to access it.'.format(rpath))
        if client:
            self.client = client
        else:
            self.client = ADLTransferClient(
                adlfs,
                transfer=get_chunk,
                nthreads=nthreads,
                chunksize=chunksize,
                buffersize=buffersize,
                blocksize=blocksize,
                chunked=False,
                verbose=verbose,
                parent=self,
                progress_callback=progress_callback,
                timeout=timeout)
        self._name = tokenize(adlfs, rpath, lpath, chunksize, blocksize)
        self.rpath = rpath
        self.lpath = lpath
        self._overwrite = overwrite
        existing_files = self._setup()
        if existing_files:
            raise FileExistsError('Overwrite was not specified and the following files exist, blocking the transfer operation. Please specify overwrite to overwrite these files during transfer: {}'.format(','.join(existing_files)))
        
        if run:
            self.run()

    def save(self, keep=True):
        """ Persist this download

        Saves a copy of this transfer process in its current state to disk.
        This is done automatically for a running transfer, so that as a chunk
        is completed, this is reflected. Thus, if a transfer is interrupted,
        e.g., by user action, the transfer can be restarted at another time.
        All chunks that were not already completed will be restarted at that
        time.

        See methods ``load`` to retrieved saved transfers and ``run`` to
        resume a stopped transfer.

        Parameters
        ----------
        keep: bool (True)
            If True, transfer will be saved if some chunks remain to be
            completed; the transfer will be sure to be removed otherwise.
        """
        save(self, os.path.join(datadir, 'downloads'), keep)

    @staticmethod
    def load():
        """ Load list of persisted transfers from disk, for possible resumption.

        Returns
        -------
            A dictionary of download instances. The hashes are auto-
            generated unique. The state of the chunks completed, errored, etc.,
            can be seen in the status attribute. Instances can be resumed with
            ``run()``.
        """
        return load(os.path.join(datadir, 'downloads'))

    @staticmethod
    def clear_saved():
        """ Remove references to all persisted downloads.
        """
        if os.path.exists(os.path.join(datadir, 'downloads')):
            os.remove(os.path.join(datadir, 'downloads'))

    @property
    def hash(self):
        return self._name



    def _setup(self):
        """ Create set of parameters to loop over
        """

        def is_glob_path(path):
            path = AzureDLPath(path).trim()
            prefix = path.globless_prefix
            return not path == prefix
        is_rpath_glob = is_glob_path(self.rpath)

        if is_rpath_glob:
            rfiles = self.client._adlfs.glob(self.rpath, details=True, invalidate_cache=True)
        else:
            rfiles = self.client._adlfs.walk(self.rpath, details=True, invalidate_cache=True)

        if not rfiles:
            raise ValueError('No files to download')

        # If only one file is returned we are not sure whether user specified a dir or a file to download,
        # since walk gives the same result for both i.e walk("DirWithsingleFile") == walk("DirWithSingleFile\SingleFile)
        # If user specified a file in rpath,
        # then we want to download the file into lpath directly and not create another subdir for that.
        # If user specified a dir that happens to contain only one file, we want to create the dir as well under lpath.
        if len(rfiles) == 1 and not is_rpath_glob and self.client._adlfs.info(self.rpath)['type'] == 'FILE':
            if os.path.exists(self.lpath) and os.path.isdir(self.lpath):
                file_pairs = [(os.path.join(self.lpath, os.path.basename(rfiles[0]['name'] + '.inprogress')),
                               rfiles[0])]
            else:
                file_pairs = [(self.lpath, rfiles[0])]
        else:
            local_rel_rpath = str(AzureDLPath(self.rpath).trim().globless_prefix)
            file_pairs = [(os.path.join(self.lpath, os.path.relpath(f['name'] +'.inprogress', local_rel_rpath)), f)
                          for f in rfiles]


        # this property is used for internal validation
        # and should not be referenced directly by public callers
        self._file_pairs = file_pairs

        existing_files = []
        for lfile, rfile in file_pairs:
            # only interested in the final destination file name for existence, 
            # not the initial inprogress target
            destination_file = lfile.replace('.inprogress', '')
            if not self._overwrite and os.path.exists(destination_file):
                existing_files.append(destination_file)
            else:
                self.client.submit(rfile['name'], lfile, rfile['length'])
        
        return existing_files

    def run(self, nthreads=None, monitor=True):
        """ Populate transfer queue and execute downloads

        Parameters
        ----------
        nthreads: int [None]
            Override default nthreads, if given
        monitor: bool [True]
            To watch and wait (block) until completion.
        """
        def touch(self, src, dst):
            root = os.path.dirname(dst)
            if not os.path.exists(root) and root:
                # don't attempt to create current directory
                logger.debug('Creating directory %s', root)
                try:
                    os.makedirs(root)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
            logger.debug('Creating empty file %s', dst)
            with open(dst, 'wb'):
                pass

        for empty_directory in self.client._adlfs._empty_dirs_to_add():
            local_rel_rpath = str(AzureDLPath(self.rpath).trim().globless_prefix)
            path = os.path.join(self.lpath, os.path.relpath(empty_directory['name'], local_rel_rpath))
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        self.client.run(nthreads, monitor, before_start=touch)

    def active(self):
        """ Return whether the downloader is active """
        return self.client.active

    def successful(self):
        """
        Return whether the downloader completed successfully.

        It will raise AssertionError if the downloader is active.
        """
        return self.client.successful

    def __str__(self):
        return "<ADL Download: %s -> %s (%s)>" % (self.rpath, self.lpath,
                                                  self.client.status)

    __repr__ = __str__

def get_chunk(adlfs, src, dst, offset, size, buffersize, blocksize,
              shutdown_event=None, retries=10, delay=0.01, backoff=3):
    """ Download a piece of a remote file and write locally

    Internal function used by `download`.
    """
    err = None
    total_bytes_downloaded = 0
    retry_policy = ExponentialRetryPolicy(max_retries=retries, exponential_retry_interval=delay,
                                          exponential_factor=backoff)
    filesessionid = str(uuid.uuid4())
    try:
        nbytes = 0
        start = offset

        with open(dst, 'rb+') as fout:
            fout.seek(start)
            while start < offset+size:
                with closing(_fetch_range(adlfs.azure, src, start=start,
                                          end=min(start+blocksize, offset+size), stream=True,
                                          retry_policy=retry_policy, filesessionid=filesessionid)) as response:
                    chunk = response.content
                    if shutdown_event and shutdown_event.is_set():
                        return total_bytes_downloaded, None
                    if chunk:
                        nwritten = fout.write(chunk)
                        if nwritten:
                            nbytes += nwritten
                            start += nwritten
                        else:
                            raise IOError("Failed to write to disk for {0} at location {1} with blocksize {2}".format(dst, start, blocksize))
        logger.debug('Downloaded %s bytes to %s, byte offset %s', nbytes, dst, offset)

        # There are certain cases where we will be throttled and recieve less than the expected amount of data.
        # In these cases, instead of failing right away, instead indicate a retry is occuring and update offset and
        # size to attempt another read to get the rest of the data. We will only do this if the amount of bytes read
        # is less than size, because if somehow we recieved too much data we are not clear on how to proceed.
        if nbytes < size:
            errMsg = 'Did not recieve total bytes requested from server. This can be due to server side throttling and will be retried. Data Expected: {}. Data Received: {}.'.format(size, nbytes)
            size -= nbytes
            offset += nbytes
            total_bytes_downloaded += nbytes
            raise IOError(errMsg)
        elif nbytes > size:
            raise IOError('Received more bytes than expected from the server. Expected: {}. Received: {}.'.format(size, nbytes))
        else:
            total_bytes_downloaded += nbytes

        return total_bytes_downloaded, None
    except Exception as e:
        err = e
        logger.debug('Exception %s on ADL download on attempt', repr(err))
        exception = RuntimeError('Max number of ADL retries exceeded: exception ' + repr(err))
        logger.error('Download failed %s; %s', dst, repr(exception))
        return total_bytes_downloaded, exception


class ADLUploader(object):
    """ Upload local file(s) using chunks and threads

    Launches multiple threads for efficient uploading, with `chunksize`
    assigned to each. The path can be a single file, a directory
    of files or a glob pattern.

    Parameters
    ----------
    adlfs: ADL filesystem instance
    rpath: str
        remote path to upload to; if multiple files, this is the dircetory
        root to write within
    lpath: str
        local path. Can be single file, directory (in which case, upload
        recursively) or glob pattern. Recursive glob patterns using `**` are
        not supported.
    nthreads: int [None]
        Number of threads to use. If None, uses the number of cores.
    chunksize: int [2**28]
        Number of bytes for a chunk. Large files are split into chunks. Files
        smaller than this number will always be transferred in a single thread.
    buffersize: int [2**22]
        Number of bytes for internal buffer. This block cannot be bigger than
        a chunk and cannot be smaller than a block.
    blocksize: int [2**22]
        Number of bytes for a block. Within each chunk, we write a smaller
        block for each API call. This block cannot be bigger than a chunk.
    client: ADLTransferClient [None]
        Set an instance of ADLTransferClient when finer-grained control over
        transfer parameters is needed. Ignores `nthreads` and `chunksize`
        set by constructor.
    run: bool [True]
        Whether to begin executing immediately.
    overwrite: bool [False]
        Whether to forcibly overwrite existing files/directories. If False and
        remote path is a directory, will quit regardless if any files would be
        overwritten or not. If True, only matching filenames are actually
        overwritten.
    progress_callback: callable [None]
        Callback for progress with signature function(current, total) where
        current is the number of bytes transfered so far, and total is the
        size of the blob, or None if the total size is unknown.
    timeout: int (0)
        Default value 0 means infinite timeout. Otherwise time in seconds before the
        process will stop and raise an exception if  transfer is still in progress

    See Also
    --------
    azure.datalake.store.transfer.ADLTransferClient
    """
    def __init__(self, adlfs, rpath, lpath, nthreads=None, chunksize=2**28,
                 buffersize=2**22, blocksize=2**22, client=None, run=True,
                 overwrite=False, verbose=False, progress_callback=None, timeout=0):

        if client:
            self.client = client
        else:
            self.client = ADLTransferClient(
                adlfs,
                transfer=put_chunk,
                merge=merge_chunks,
                nthreads=nthreads,
                chunksize=chunksize,
                buffersize=buffersize,
                blocksize=blocksize,
                delimiter=None, # TODO: see utils.cs for what is required to support delimiters.
                parent=self,
                verbose=verbose,
                unique_temporary=True,
                progress_callback=progress_callback,
                timeout=timeout)
        self._name = tokenize(adlfs, rpath, lpath, chunksize, blocksize)
        self.rpath = AzureDLPath(rpath)
        self.lpath = lpath
        self._overwrite = overwrite
        existing_files = self._setup()
        
        if existing_files:
            raise FileExistsError('Overwrite was not specified and the following files exist, blocking the transfer operation. Please specify overwrite to overwrite these files during transfer: {}'.format(','.join(existing_files)))

        if run:
            self.run()

    def save(self, keep=True):
        """ Persist this upload

        Saves a copy of this transfer process in its current state to disk.
        This is done automatically for a running transfer, so that as a chunk
        is completed, this is reflected. Thus, if a transfer is interrupted,
        e.g., by user action, the transfer can be restarted at another time.
        All chunks that were not already completed will be restarted at that
        time.

        See methods ``load`` to retrieved saved transfers and ``run`` to
        resume a stopped transfer.

        Parameters
        ----------
        keep: bool (True)
            If True, transfer will be saved if some chunks remain to be
            completed; the transfer will be sure to be removed otherwise.
        """
        save(self, os.path.join(datadir, 'uploads'), keep)

    @staticmethod
    def load():
        """ Load list of persisted transfers from disk, for possible resumption.

        Returns
        -------
            A dictionary of upload instances. The hashes are auto
            generated unique. The state of the chunks completed, errored, etc.,
            can be seen in the status attribute. Instances can be resumed with
            ``run()``.
        """
        return load(os.path.join(datadir, 'uploads'))

    @staticmethod
    def clear_saved():
        """ Remove references to all persisted uploads.
        """
        if os.path.exists(os.path.join(datadir, 'uploads')):
            os.remove(os.path.join(datadir, 'uploads'))

    @property
    def hash(self):
        return self._name

    def _setup(self):
        """ Create set of parameters to loop over
        """
        is_path_walk_empty = False
        if "*" not in self.lpath:
            lfiles = []
            for directory, subdir, fnames in os.walk(self.lpath):
                lfiles.extend([os.path.join(directory, f) for f in fnames])
                if not subdir and not fnames: # Empty Directory
                    self.client._adlfs._emptyDirs.append(directory)

            if (not lfiles and os.path.exists(self.lpath) and
                    not os.path.isdir(self.lpath)):
                lfiles = [self.lpath]
                is_path_walk_empty = True
        else:
            lfiles = glob.glob(self.lpath)
        
        if len(lfiles) > 0 and not is_path_walk_empty:
            local_rel_lpath = str(AzureDLPath(self.lpath).globless_prefix)
            file_pairs = [(f, self.rpath / AzureDLPath(f).relative_to(local_rel_lpath)) for f in lfiles]
        elif lfiles:
            if self.client._adlfs.exists(self.rpath, invalidate_cache=True) and \
               self.client._adlfs.info(self.rpath, invalidate_cache=False)['type'] == "DIRECTORY":
                file_pairs = [(lfiles[0], self.rpath / AzureDLPath(lfiles[0]).name)]
            else:
                file_pairs = [(lfiles[0], self.rpath)]
        else:
            raise ValueError('No files to upload')

        # this property is used for internal validation
        # and should not be referenced directly by public callers
        self._file_pairs = file_pairs

        existing_files = []
        for lfile, rfile in file_pairs:
            if not self._overwrite and self.client._adlfs.exists(rfile, invalidate_cache=False):
                existing_files.append(rfile.as_posix())
            else:
                fsize = os.stat(lfile).st_size
                self.client.submit(lfile, rfile, fsize)

        return existing_files

    def run(self, nthreads=None, monitor=True):
        """ Populate transfer queue and execute downloads

        Parameters
        ----------
        nthreads: int [None]
            Override default nthreads, if given
        monitor: bool [True]
            To watch and wait (block) until completion.
        """
        for empty_directory in self.client._adlfs._empty_dirs_to_add():
            local_rel_path = os.path.relpath(empty_directory, self.lpath)
            rel_rpath = str(AzureDLPath(self.rpath).trim().globless_prefix / local_rel_path)
            self.client._adlfs.mkdir(rel_rpath)

        self.client.run(nthreads, monitor)

    def active(self):
        """ Return whether the uploader is active """
        return self.client.active

    def successful(self):
        """
        Return whether the uploader completed successfully.

        It will raise AssertionError if the uploader is active.
        """
        return self.client.successful

    def __str__(self):
        return "<ADL Upload: %s -> %s (%s)>" % (self.lpath, self.rpath,
                                                self.client.status)

    __repr__ = __str__


def put_chunk(adlfs, src, dst, offset, size, buffersize, blocksize, delimiter=None,
              shutdown_event=None):
    """ Upload a piece of a local file

    Internal function used by `upload`.
    """
    nbytes = 0
    try:
        with adlfs.open(dst, 'wb', blocksize=buffersize, delimiter=delimiter) as fout:
            end = offset + size
            miniblock = min(size, blocksize)
            # For empty files there is no need to take the IO hit.
            if size != 0:
                with open(src, 'rb') as fin:
                    for o in range(offset, end, miniblock):
                        if shutdown_event and shutdown_event.is_set():
                            return nbytes, None
                        data = read_block(fin, o, miniblock, delimiter)
                        nbytes += fout.write(data)
                
    except Exception as e:
        exception = repr(e)
        logger.error('Upload failed %s; %s', src, exception)
        return nbytes, exception
    logger.debug('Uploaded from %s, byte offset %s', src, offset)
    return nbytes, None


def merge_chunks(adlfs, outfile, files, shutdown_event=None, overwrite=False):
    try:
        # note that it is assumed that only temp files from this run are in the segment folder created.
        # so this call is optimized to instantly delete the temp folder on concat.
        # if somehow the target file was created between the beginning of upload
        # and concat, we will remove it if the user specified overwrite.
        # here we must get the most up to date information from the service,
        # instead of relying on the local cache to ensure that we know if
        # the merge target already exists.
        if adlfs.exists(outfile, invalidate_cache=True):
            if overwrite:
                adlfs.remove(outfile, True)
            else:
                raise FileExistsError(outfile)

        adlfs.concat(outfile, files, delete_source=True)
    except Exception as e:
        exception = repr(e)
        logger.error('Merged failed %s; %s', outfile, exception)
        return exception
    logger.debug('Merged %s', outfile)
    adlfs.invalidate_cache(outfile)
    return None
