# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
The main file-system class and functionality.

Provides an pythonic interface to the Azure Data-lake Store, including
file-system commands with typical names and options, and a File object
which is compatible with the built-in File.
"""

# standard imports
import io
import logging
import sys
import uuid
import json

# local imports
from .exceptions import DatalakeBadOffsetException, DatalakeIncompleteTransferException
from .exceptions import FileNotFoundError, PermissionError
from .lib import DatalakeRESTInterface
from .utils import ensure_writable, read_block
from .enums import ExpiryOptionType
from .retry import ExponentialRetryPolicy, NoRetryPolicy
from .multiprocessor import multi_processor_change_acl
import pathlib


logger = logging.getLogger(__name__)
valid_expire_types = [x.value for x in ExpiryOptionType]


class AzureDLFileSystem(object):
    """
    Access Azure DataLake Store as if it were a file-system

    Parameters
    ----------
    store_name: str ("")
        Store name to connect to. If not supplied, we use environment variable azure_data_lake_store_name
    token_credential: credentials object
        When setting up a new connection, this contains the authorization
        credentials. Use Azure Identity to get this or define an implementation of azure.core.credentials.TokenCredential
    scopes: str(None)
        which is a list of scopes to use for the token.
    url_suffix: str (None)
        Domain to send REST requests to. The end-point URL is constructed
        using this and the store_name. If None, use default.
    api_version: str (2018-09-01)
        The API version to target with requests. Changing this value will change the behavior of the requests, and can cause unexpected behavior or breaking changes. Changes to this value should be undergone with caution.
    per_call_timeout_seconds: float(60)
        This is the timeout for each requests library call.
    kwargs: optional key/values
        Other arguments forwarded to the DatalakeRESTInterface constructor.
    """
    _singleton = [None]

    def __init__(self, token_credential=None, **kwargs):
        self.token_credential = token_credential
        self.kwargs = kwargs
        self.connect()
        self.dirs = {}
        self._emptyDirs = []
        AzureDLFileSystem._singleton[0] = self

    @classmethod
    def current(cls):
        """ Return the most recently created AzureDLFileSystem
        """
        if not cls._singleton[0]:
            return cls()
        else:
            return cls._singleton[0]

    def connect(self):
        """
        Establish connection object.
        """
        self.azure = DatalakeRESTInterface(token_credential=self.token_credential, **self.kwargs)
        self.token_credential = self.azure.token_credential

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.connect()

    def open(self, path, mode='rb', blocksize=2 ** 25, delimiter=None):
        """ Open a file for reading or writing

        Parameters
        ----------
        path: string
            Path of file on ADL
        mode: string
            One of 'rb', 'ab' or 'wb'
        blocksize: int
            Size of data-node blocks if reading
        delimiter: byte(s) or None
            For writing delimiter-ended blocks
        """
        if 'b' not in mode:
            raise NotImplementedError("Text mode not supported, use mode='%s'"
                                      " and manage bytes" % (mode[0] + 'b'))
        return AzureDLFile(self, AzureDLPath(path), mode, blocksize=blocksize,
                           delimiter=delimiter)

    def _ls_batched(self, path, batch_size=4000):
        """Batched ListStatus calls. Internal Method"""
        if batch_size <= 1:
            raise ValueError("Batch size must be strictly greater than 1")
        parms = {'listSize': batch_size}
        ret = []
        continuation_token = "NonEmptyStringSentinel"

        while continuation_token != "":
            ls_call_result = self.azure.call('LISTSTATUS', path, **parms)

            data = ls_call_result['FileStatuses']['FileStatus']
            ret.extend(data)

            continuation_token = ls_call_result['FileStatuses']['continuationToken']
            parms['listAfter'] = continuation_token  # continuationToken to be used as ListAfter

        return ret

    def _ls(self, path, invalidate_cache=True, batch_size=4000):
        """ List files at given path """
        path = AzureDLPath(path).trim()
        key = path.as_posix()

        if invalidate_cache:
            self.invalidate_cache(key)

        if key not in self.dirs:
            self.dirs[key] = self._ls_batched(key, batch_size=batch_size)
            for f in self.dirs[key]:
                f['name'] = (path / f['pathSuffix']).as_posix()
        return self.dirs[key]

    def ls(self, path="", detail=False, invalidate_cache=True):
        """
        List all elements under directory specified with path

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        detail: bool
            Detailed info or not.
        invalidate_cache: bool
            Whether to invalidate cache or not

        Returns
        -------
        List of elements under directory specified with path
        """
        path = AzureDLPath(path)
        files = self._ls(path, invalidate_cache)
        if not files:
            # in this case we just invalidated the cache (if it was true), so no need to do it again
            inf = self.info(path, invalidate_cache=False)
            if inf['type'] == 'DIRECTORY':
                # always return an empty array in this case, because there are no entries underneath the folder
                return []

            raise FileNotFoundError(path)
        if detail:
            return files
        else:
            return [f['name'] for f in files]

    def info(self, path, invalidate_cache=True, expected_error_code=None):
        """
        File information for path

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        invalidate_cache: bool
            Whether to invalidate cache or not
        expected_error_code:  int
            Optionally indicates a specific, expected error code, if any.

        Returns
        -------
        File information
        """
        path = AzureDLPath(path).trim()
        path_as_posix = path.as_posix()
        root = path.parent
        root_as_posix = root.as_posix()

        # in the case of getting info about the root itself or if the cache won't be hit
        # simply return the result of a GETFILESTATUS from the service
        if invalidate_cache or path_as_posix in {'/', '.'}:
            to_return = self.azure.call('GETFILESTATUS', path_as_posix, expected_error_code=expected_error_code)[
                'FileStatus']
            to_return['name'] = path_as_posix

            # add the key/value pair back to the cache so long as it isn't the root
            if path_as_posix not in {'/', '.'}:
                if root_as_posix not in self.dirs:
                    self.dirs[root_as_posix] = [to_return]
                else:
                    found = False
                    for f in self.dirs[root_as_posix]:
                        if f['name'] == path_as_posix:
                            found = True
                            break
                    if not found:
                        self.dirs[root_as_posix].append(to_return)
            return to_return

        for f in self._ls(root, invalidate_cache):
            if f['name'] == path_as_posix:
                return f

        raise FileNotFoundError(path)

    def _walk(self, path, invalidate_cache=True, include_dirs=False):
        """
        Walk a path recursively and returns list of files and dirs(if parameter set)

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        invalidate_cache: bool
            Whether to invalidate cache
        include_dirs: bool
            Whether to include dirs in return value

        Returns
        -------
        List of files and (optionally) dirs
        """
        ret = list(self._ls(path, invalidate_cache))
        self._emptyDirs = []
        current_subdirs = [f for f in ret if f['type'] != 'FILE']
        while current_subdirs:
            dirs_below_current_level = []
            for apath in current_subdirs:
                try:
                    sub_elements = self._ls(apath['name'], invalidate_cache)
                except FileNotFoundError:
                    # Folder may have been deleted while walk is going on. Infrequent so we can take the linear hit
                    ret.remove(apath)
                    continue
                if not sub_elements:
                    self._emptyDirs.append(apath)
                else:
                    ret.extend(sub_elements)
                    dirs_below_current_level.extend([f for f in sub_elements if f['type'] != 'FILE'])
            current_subdirs = dirs_below_current_level

        if include_dirs:
            return ret
        else:
            return [f for f in ret if f['type'] == 'FILE']

    def _empty_dirs_to_add(self):
        """ Returns directories found empty during walk. Only for internal use"""
        return self._emptyDirs

    def walk(self, path='', details=False, invalidate_cache=True):
        """
        Get all files below given path

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        details: bool
            Whether to include file details
        invalidate_cache: bool
            Whether to invalidate cache

        Returns
        -------
        List of files
        """
        return [f if details else f['name'] for f in self._walk(path, invalidate_cache)]

    def glob(self, path, details=False, invalidate_cache=True):
        """
        Find files (not directories) by glob-matching.

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        details: bool
            Whether to include file details
        invalidate_cache: bool
            Whether to invalidate cache

        Returns
        -------
        List of files
        """

        path = AzureDLPath(path).trim()
        path_as_posix = path.as_posix()
        prefix = path.globless_prefix
        allfiles = self.walk(prefix, details, invalidate_cache)
        if prefix == path:
            return allfiles
        return [f for f in allfiles if AzureDLPath(f['name'] if details else f).match(path_as_posix)]

    def du(self, path, total=False, deep=False, invalidate_cache=True):
        """
        Bytes in keys at path

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        total: bool
            Return the sum on list
        deep: bool
            Recursively enumerate or just use files under current dir
        invalidate_cache: bool
            Whether to invalidate cache

        Returns
        -------
        List of dict of name:size pairs or total size.
        """

        if deep:
            files = self._walk(path, invalidate_cache)
        else:
            files = self.ls(path, detail=True, invalidate_cache=invalidate_cache)
        if total:
            return sum(f.get('length', 0) for f in files)
        else:
            return {p['name']: p['length'] for p in files}

    def df(self, path):
        """ Resource summary of path

        Parameters
        ----------
        path: str
            Path to query
        """
        path = AzureDLPath(path).trim()
        current_path_info = self.info(path, invalidate_cache=False)
        if current_path_info['type'] == 'FILE':
            return {'directoryCount': 0, 'fileCount': 1, 'length': current_path_info['length'], 'quota': -1,
                    'spaceConsumed': current_path_info['length'], 'spaceQuota': -1}
        else:
            all_files_and_dirs = self._walk(path, include_dirs=True)
            dir_count = 1  # 1 as walk doesn't return current directory
            length = file_count = 0
            for item in all_files_and_dirs:
                length += item['length']
                if item['type'] == 'FILE':
                    file_count += 1
                else:
                    dir_count += 1

            return {'directoryCount': dir_count, 'fileCount': file_count, 'length': length, 'quota': -1,
                    'spaceConsumed': length, 'spaceQuota': -1}

    def chmod(self, path, mod):
        """  Change access mode of path

        Note this is not recursive.

        Parameters
        ----------
        path: str
            Location to change
        mod: str
            Octal representation of access, e.g., "0777" for public read/write.
            See [docs](http://hadoop.apache.org/docs/r2.4.1/hadoop-project-dist/hadoop-hdfs/WebHDFS.html#Permission)
        """
        path = AzureDLPath(path).trim()
        self.azure.call('SETPERMISSION', path.as_posix(), permission=mod)
        self.invalidate_cache(path.as_posix())

    def set_expiry(self, path, expiry_option, expire_time=None):
        """
        Set or remove the expiration time on the specified file.
        This operation can only be executed against files.

        Note: Folders are not supported.

        Parameters
        ----------
        path: str
            File path to set or remove expiration time
        expire_time: int
            The time that the file will expire, corresponding to the expiry_option that was set
        expiry_option: str
            Indicates the type of expiration to use for the file:
                1. NeverExpire: ExpireTime is ignored.
                2. RelativeToNow: ExpireTime is an integer in milliseconds representing the expiration date relative to when file expiration is updated.
                3. RelativeToCreationDate: ExpireTime is an integer in milliseconds representing the expiration date relative to file creation.
                4. Absolute: ExpireTime is an integer in milliseconds, as a Unix timestamp relative to 1/1/1970 00:00:00.
        """
        parms = {}
        value_to_use = [x for x in valid_expire_types if x.lower() == expiry_option.lower()]
        if len(value_to_use) != 1:
            raise ValueError(
                'expiry_option must be one of: {}. Value given: {}'.format(valid_expire_types, expiry_option))

        if value_to_use[0] != ExpiryOptionType.never_expire.value and not expire_time:
            raise ValueError(
                'expire_time must be specified if the expiry_option is not NeverExpire. Value of expiry_option: {}'.format(
                    expiry_option))

        path = AzureDLPath(path).trim()
        parms['expiryOption'] = value_to_use[0]

        if expire_time:
            parms['expireTime'] = int(expire_time)

        self.azure.call('SETEXPIRY', path.as_posix(), is_extended=True, **parms)
        self.invalidate_cache(path.as_posix())

    def _acl_call(self, action, path, acl_spec=None, invalidate_cache=False):
        """
        Helper method for ACL calls to reduce code repetition

        Parameters
        ----------
        action: str
            The ACL action being executed. For example SETACL
        path: str
            The path the action is being executed on (file or folder)
        acl_spec: str
            The optional ACL specification to set on the path in the format
            '[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,...'

            Note that for remove acl entries the permission (rwx) portion is not required.
        invalidate_cache: bool
            optionally indicates that the cache of files should be invalidated after this operation
            This should always be done for set and remove operations, since the state of the file or folder has changed.
        """
        parms = {}
        path = AzureDLPath(path).trim()
        posix_path = path.as_posix()
        if acl_spec:
            parms['aclSpec'] = acl_spec

        to_return = self.azure.call(action, posix_path, **parms)
        if invalidate_cache:
            self.invalidate_cache(posix_path)

        return to_return

    def set_acl(self, path, acl_spec, recursive=False, number_of_sub_process=None):
        """
        Set the Access Control List (ACL) for a file or folder.

        Note: this is by default not recursive, and applies only to the file or folder specified.

        Parameters
        ----------
        path: str
            Location to set the ACL on.
        acl_spec: str
            The ACL specification to set on the path in the format
            '[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,...'
        recursive: bool
            Specifies whether to set ACLs recursively or not
        """
        if recursive:
            multi_processor_change_acl(adl=self, path=path, method_name="set_acl", acl_spec=acl_spec,
                                       number_of_sub_process=number_of_sub_process)
        else:
            self._acl_call('SETACL', path, acl_spec, invalidate_cache=True)

    def modify_acl_entries(self, path, acl_spec, recursive=False, number_of_sub_process=None):
        """
        Modify existing Access Control List (ACL) entries on a file or folder.
        If the entry does not exist it is added, otherwise it is updated based on the spec passed in.
        No entries are removed by this process (unlike set_acl).

        Note: this is by default not recursive, and applies only to the file or folder specified.

        Parameters
        ----------
        path: str
            Location to set the ACL entries on.
        acl_spec: str
            The ACL specification to use in modifying the ACL at the path in the format
            '[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,...'
        recursive: bool
            Specifies whether to modify ACLs recursively or not
        """
        if recursive:
            multi_processor_change_acl(adl=self, path=path, method_name="mod_acl", acl_spec=acl_spec,
                                       number_of_sub_process=number_of_sub_process)
        else:
            self._acl_call('MODIFYACLENTRIES', path, acl_spec, invalidate_cache=True)

    def remove_acl_entries(self, path, acl_spec, recursive=False, number_of_sub_process=None):
        """
        Remove existing, named, Access Control List (ACL) entries on a file or folder.
        If the entry does not exist already it is ignored.
        Default entries cannot be removed this way, please use remove_default_acl for that.
        Unnamed entries cannot be removed in this way, please use remove_acl for that.

        Note: this is by default not recursive, and applies only to the file or folder specified.

        Parameters
        ----------
        path: str
            Location to remove the ACL entries.
        acl_spec: str
            The ACL specification to remove from the ACL at the path in the format (note that the permission portion is missing)
            '[default:]user|group|other:[entity id or UPN],[default:]user|group|other:[entity id or UPN],...'
        recursive: bool
            Specifies whether to remove ACLs recursively or not
        """
        if recursive:
            multi_processor_change_acl(adl=self, path=path, method_name="rem_acl", acl_spec=acl_spec,
                                       number_of_sub_process=number_of_sub_process)
        else:
            self._acl_call('REMOVEACLENTRIES', path, acl_spec, invalidate_cache=True)

    def get_acl_status(self, path):
        """
        Gets Access Control List (ACL) entries for the specified file or directory.

        Parameters
        ----------
        path: str
            Location to get the ACL.
        """
        return self._acl_call('MSGETACLSTATUS', path)['AclStatus']

    def remove_acl(self, path):
        """
        Remove the entire, non default, ACL from the file or folder, including unnamed entries.
        Default entries cannot be removed this way, please use remove_default_acl for that.

        Note: this is not recursive, and applies only to the file or folder specified.

        Parameters
        ----------
        path: str
            Location to remove the ACL.
        """
        self._acl_call('REMOVEACL', path, invalidate_cache=True)

    def remove_default_acl(self, path):
        """
        Remove the entire default ACL from the folder.
        Default entries do not exist on files, if a file
        is specified, this operation does nothing.

        Note: this is not recursive, and applies only to the folder specified.

        Parameters
        ----------
        path: str
            Location to set the ACL on.
        """
        self._acl_call('REMOVEDEFAULTACL', path, invalidate_cache=True)

    def chown(self, path, owner=None, group=None):
        """
        Change owner and/or owning group

        Note this is not recursive.

        Parameters
        ----------
        path: str
            Location to change
        owner: str
            UUID of owning entity
        group: str
            UUID of group
        """
        parms = {}
        if owner is None and group is None:
            raise ValueError('Must supply owner and/or group')
        if owner:
            parms['owner'] = owner
        if group:
            parms['group'] = group
        path = AzureDLPath(path).trim()
        self.azure.call('SETOWNER', path.as_posix(), **parms)
        self.invalidate_cache(path.as_posix())

    def exists(self, path, invalidate_cache=True):
        """
        Does such a file/directory exist?

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        invalidate_cache: bool
            Whether to invalidate cache

        Returns
        -------
        True or false depending on whether the path exists.
        """
        try:
            self.info(path, invalidate_cache, expected_error_code=404)
            return True
        except FileNotFoundError:
            return False

    def cat(self, path):
        """
        Return contents of file

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query

        Returns
        -------
        Contents of file
        """
        with self.open(path, 'rb') as f:
            return f.read()

    def tail(self, path, size=1024):
        """
        Return last bytes of file

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        size: int
            How many bytes to return

        Returns
        -------
        Last(size) bytes of file
        """
        length = self.info(path)['length']
        if size > length:
            return self.cat(path)
        with self.open(path, 'rb') as f:
            f.seek(length - size)
            return f.read(size)

    def head(self, path, size=1024):
        """
        Return first bytes of file

        Parameters
        ----------
        path: str or AzureDLPath
            Path to query
        size: int
            How many bytes to return

        Returns
        -------
        First(size) bytes of file
        """
        with self.open(path, 'rb', blocksize=size) as f:
            return f.read(size)

    def get(self, path, filename):
        """
        Stream data from file at path to local filename

        Parameters
        ----------
        path: str or AzureDLPath
            ADL Path to read
        filename: str or Path
            Local file path to write to

        Returns
        -------
        None
        """
        with self.open(path, 'rb') as f:
            with open(filename, 'wb') as f2:
                while True:
                    data = f.read(f.blocksize)
                    if len(data) == 0:
                        break
                    f2.write(data)

    def put(self, filename, path, delimiter=None):
        """
        Stream data from local filename to file at path

        Parameters
        ----------
        filename: str or Path
            Local file path to read from
        path: str or AzureDLPath
            ADL Path to write to
        delimiter:
            Optional delimeter for delimiter-ended blocks

        Returns
        -------
        None
        """
        with open(filename, 'rb') as f:
            with self.open(path, 'wb', delimiter=delimiter) as f2:
                while True:
                    data = f.read(f2.blocksize)
                    if len(data) == 0:
                        break
                    f2.write(data)

    def mkdir(self, path):
        """
        Make new directory

        Parameters
        ----------
        path: str or AzureDLPath
            Path to create directory

        Returns
        -------
        None
        """
        """  """
        path = AzureDLPath(path).trim()
        self.azure.call('MKDIRS', path.as_posix())
        self.invalidate_cache(path)

    def rmdir(self, path):
        """
        Remove empty directory

        Parameters
        ----------
        path: str or AzureDLPath
            Directory  path to remove

        Returns
        -------
        None
        """
        if self.info(path)['type'] != "DIRECTORY":
            raise ValueError('Can only rmdir on directories')
        # should always invalidate the cache when checking to see if the directory is empty
        if self.ls(path, invalidate_cache=True):
            raise ValueError('Directory not empty: %s' % path)
        self.rm(path, False)

    def mv(self, path1, path2):
        """
        Move file between locations on ADL

        Parameters
        ----------
        path1:
            Source Path
        path2:
            Destination path

        Returns
        -------
        None
        """
        path1 = AzureDLPath(path1).trim()
        path2 = AzureDLPath(path2).trim()
        self.azure.call('RENAME', path1.as_posix(),
                        destination=path2.as_posix())
        self.invalidate_cache(path1)
        self.invalidate_cache(path2)

    def concat(self, outfile, filelist, delete_source=False):
        """ Concatenate a list of files into one new file

        Parameters
        ----------

        outfile: path
            The file which will be concatenated to. If it already exists,
            the extra pieces will be appended.
        filelist: list of paths
            Existing adl files to concatenate, in order
        delete_source: bool (False)
            If True, assume that the paths to concatenate exist alone in a
            directory, and delete that whole directory when done.

        Returns
        -------
        None
        """
        outfile = AzureDLPath(outfile).trim()
        delete = 'true' if delete_source else 'false'
        sourceList = [AzureDLPath(f).as_posix() for f in filelist]
        sources = {}
        sources["sources"] = sourceList

        self.azure.call('MSCONCAT', outfile.as_posix(),
                        data=bytearray(json.dumps(sources, separators=(',', ':')), encoding="utf-8"),
                        deleteSourceDirectory=delete,
                        headers={'Content-Type': "application/json"},
                        retry_policy=NoRetryPolicy())
        self.invalidate_cache(outfile)

    merge = concat

    def cp(self, path1, path2):
        """ Not implemented. Copy file between locations on ADL """
        # TODO: any implementation for this without download?
        raise NotImplementedError

    def rm(self, path, recursive=False):
        """
        Remove a file or directory

        Parameters
        ----------
        path: str or AzureDLPath
            The location to remove.
        recursive: bool (True)
            Whether to remove also all entries below, i.e., which are returned
            by `walk()`.

        Returns
        -------
        None
        """
        path = AzureDLPath(path).trim()
        # Always invalidate the cache when attempting to check existence of something to delete
        if not self.exists(path, invalidate_cache=True):
            raise FileNotFoundError(path)
        self.azure.call('DELETE', path.as_posix(), recursive=recursive)
        self.invalidate_cache(path)
        if recursive:
            matches = [p for p in self.dirs if p.startswith(path.as_posix())]
            [self.invalidate_cache(m) for m in matches]

    def invalidate_cache(self, path=None):
        """
        Remove entry from object file-cache

        Parameters
        ----------
        path: str or AzureDLPath
            Remove the path from object file-cache

        Returns
        -------
        None
        """
        if path is None:
            self.dirs.clear()
        else:
            path = AzureDLPath(path).trim()
            self.dirs.pop(path.as_posix(), None)
            parent = AzureDLPath(path.parent).trim()
            self.dirs.pop(parent.as_posix(), None)

    def touch(self, path):
        """
        Create empty file

        Parameters
        ----------
        path: str or AzureDLPath
            Path of file to create

        Returns
        -------
        None
        """
        with self.open(path, 'wb'):
            pass

    def read_block(self, fn, offset, length, delimiter=None):
        """ Read a block of bytes from an ADL file

        Starting at ``offset`` of the file, read ``length`` bytes.  If
        ``delimiter`` is set then we ensure that the read starts and stops at
        delimiter boundaries that follow the locations ``offset`` and ``offset
        + length``.  If ``offset`` is zero then we start at zero.  The
        bytestring returned WILL include the end delimiter string.

        If offset+length is beyond the eof, reads to eof.

        Parameters
        ----------
        fn: string
            Path to filename on ADL
        offset: int
            Byte offset to start read
        length: int
            Number of bytes to read
        delimiter: bytes (optional)
            Ensure reading starts and stops at delimiter bytestring

        Examples
        --------
        >>> adl.read_block('data/file.csv', 0, 13)  # doctest: +SKIP
        b'Alice, 100\\nBo'
        >>> adl.read_block('data/file.csv', 0, 13, delimiter=b'\\n')  # doctest: +SKIP
        b'Alice, 100\\nBob, 200\\n'

        Use ``length=None`` to read to the end of the file.
        >>> adl.read_block('data/file.csv', 0, None, delimiter=b'\\n')  # doctest: +SKIP
        b'Alice, 100\\nBob, 200\\nCharlie, 300'

        See Also
        --------
        distributed.utils.read_block
        """
        with self.open(fn, 'rb') as f:
            size = f.info()['length']
            if offset >= size:
                return b''
            if length is None:
                length = size
            if offset + length > size:
                length = size - offset
            bytes = read_block(f, offset, length, delimiter)
        return bytes

    # ALIASES
    listdir = ls
    access = exists
    rename = mv
    stat = info
    unlink = remove = rm


class AzureDLFile(object):
    """
    Open ADL key as a file. Data is only loaded and cached on demand.

    Parameters
    ----------
    azure: azure connection
    path: AzureDLPath
        location of file
    mode: str {'wb', 'rb', 'ab'}
    blocksize: int
        Size of the write or read-ahead buffer. For writing(and appending, will be
        truncated to 4MB (2**22).
    delimiter: bytes or None
        If specified and in write mode, each flush will send data terminating
        on this bytestring, potentially leaving some data in the buffer.

    Examples
    --------
    >>> adl = AzureDLFileSystem()  # doctest: +SKIP
    >>> with adl.open('my-dir/my-file.txt', mode='rb') as f:  # doctest: +SKIP
    ...     f.read(10)  # doctest: +SKIP

    See Also
    --------
    AzureDLFileSystem.open: used to create AzureDLFile objects
    """

    def __init__(self, azure, path, mode='rb', blocksize=2 ** 25,
                 delimiter=None):
        self.mode = mode
        if mode not in {'rb', 'wb', 'ab'}:
            raise NotImplementedError("File mode must be {'rb', 'wb', 'ab'}, not %s" % mode)
        self.path = path
        self.azure = azure
        self.cache = b""
        self.loc = 0
        self.delimiter = delimiter
        self.start = 0
        self.end = 0
        self.closed = False
        self.trim = True
        self.buffer = io.BytesIO()
        self.blocksize = blocksize
        uniqueid = str(uuid.uuid4())
        self.filesessionid = uniqueid
        self.leaseid = uniqueid

        # always invalidate the cache when checking for existence of a file
        # that may be created or written to (for the first time).
        try:
            file_data = self.azure.info(path, invalidate_cache=True, expected_error_code=404)
            exists = True
        except FileNotFoundError:
            exists = False

        # cannot create a new file object out of a directory
        if exists and file_data['type'] == 'DIRECTORY':
            raise IOError(
                'path: {} is a directory, not a file, and cannot be opened for reading or writing'.format(path))

        if mode == 'ab' or mode == 'wb':
            self.blocksize = min(2 ** 22, blocksize)

        if mode == 'ab' and exists:
            self.loc = file_data['length']
        elif (mode == 'ab' and not exists) or (mode == 'wb'):
            # Create the file
            _put_data_with_retry(
                rest=self.azure.azure,
                op='CREATE',
                path=self.path.as_posix(),
                data=None,
                overwrite='true',
                write='true',
                syncFlag='DATA',
                leaseid=self.leaseid,
                filesessionid=self.filesessionid)
            logger.debug('Created file %s ' % self.path)
        else:  # mode == 'rb':
            if not exists:
                raise FileNotFoundError(path.as_posix())
            self.size = file_data['length']

    def info(self):
        """ File information about this path """
        return self.azure.info(self.path)

    def tell(self):
        """ Current file location """
        return self.loc

    def seek(self, loc, whence=0):
        """ Set current file location

        Parameters
        ----------
        loc: int
            byte location
        whence: {0, 1, 2}
            from start of file, current location or end of file, resp.
        """
        if not self.mode == 'rb':
            raise ValueError('Seek only available in read mode')
        if whence == 0:
            nloc = loc
        elif whence == 1:
            nloc = self.loc + loc
        elif whence == 2:
            nloc = self.size + loc
        else:
            raise ValueError(
                "invalid whence (%s, should be 0, 1 or 2)" % whence)
        if nloc < 0:
            raise ValueError('Seek before start of file')
        if nloc > self.size:
            raise ValueError('ADLFS does not support seeking beyond file')
        self.loc = nloc
        return self.loc

    def readline(self, length=-1):
        """
        Read and return a line from the stream.

        If length is specified, at most size bytes will be read.
        """
        if length < 0:
            length = self.size

        line = b""
        while True:

            # if cache has last bytes of file and its read, return line and exit loop
            if self.end >= self.size and self.loc >= self.end:
                return line

            self._read_blocksize()

            found = self.cache[self.loc - self.start:].find(b'\n') + 1
            if found:
                partialLine = self.cache[
                              self.loc - self.start: min(self.loc - self.start + found, self.loc - self.start + length)]
            else:
                partialLine = self.cache[self.loc - self.start:]

            self.loc += len(partialLine)
            line += partialLine

            if found:
                return line

    def __next__(self):
        out = self.readline()
        if not out:
            raise StopIteration
        return out

    next = __next__

    def __iter__(self):
        return self

    def readlines(self):
        """ Return all lines in a file as a list """
        return list(self)

    def _fetch(self, start, end):
        self.start = start
        self.end = min(end, self.size)
        response = _fetch_range_with_retry(
            self.azure.azure, self.path.as_posix(), self.start, self.end, filesessionid=self.filesessionid)
        self.cache = getattr(response, 'content', response)

    def _read_blocksize(self, offset=-1):
        """
        Reads next blocksize of data and updates the cache if read offset is not within cache otherwise nop

        Parameters
        ----------
        offset: int (-1)
            offset from where to read; if <0, last read location or beginning of file.

        Returns
        -------
        None
        """
        if offset < 0:
            offset = self.loc
        if offset >= self.size:
            self.start = self.size
            self.end = self.size
            self.cache = b""
            return
        if self.start <= offset < self.end:
            logger.debug("Read offset {offset} is within cache {start}-{end}. "
                        "Not going to server.".format(offset=offset, start=self.start, end=self.end))
            return
        if offset > self.size:
            raise ValueError('Read offset is outside the File')
        self._fetch(offset, offset + self.blocksize)

    def read(self, length=-1):
        """
        Return data from cache, or fetch pieces as necessary

        Parameters
        ----------
        length: int (-1)
            Number of bytes to read; if <0, all remaining bytes.
        """
        if self.mode != 'rb':
            raise ValueError('File not in read mode')
        if length < 0:
            length = self.size
        if self.closed:
            raise ValueError('I/O operation on closed file.')
        flag = 0
        out = b""
        while length > 0:
            self._read_blocksize()
            data_read = self.cache[self.loc - self.start:
                                   min(self.loc - self.start + length, self.end - self.start)]
            if not data_read:  # Check to catch possible server errors. Ideally shouldn't happen.
                flag += 1
                if flag >= 5:
                    exception_string = "Current Location:{loc}, " \
                                       "File Size:{size}, Cache Start:{start}, " \
                                       "Cache End:{end}".format(loc=self.loc, size=self.size,
                                                                start=self.start, end=self.end)
                    raise DatalakeIncompleteTransferException('Could not read data: {path}. '
                                                              'Repeated zero byte reads. Possible file corruption. File Details'
                                                              '{details}'.format(path=self.path, details=exception_string))
            out += data_read
            self.loc += len(data_read)
            length -= len(data_read)
            if self.loc >= self.size:
                length = 0

        return out

    read1 = read

    def readinto(self, b):
        """
        Reads data into buffer b


        Parameters
        ----------
        b: bytearray
            Buffer to which bytes are read into

        Returns
        -------
        Returns number of bytes read.
        """
        temp = self.read(len(b))
        b[:len(temp)] = temp
        return len(temp)

    def write(self, data):
        """
        Write data to buffer.

        Buffer only sent to ADL on flush() or if buffer is bigger than
        blocksize.

        Parameters
        ----------
        data: bytes
            Set of bytes to be written.
        """
        if self.mode not in {'wb', 'ab'}:
            raise ValueError('File not in write mode')
        if self.closed:
            raise ValueError('I/O operation on closed file.')

        # TODO Flush may be simplified
        # Buffered writes so a very large buffer is not copied leading to very large memory consumption
        bytes_written = 0
        for i in range(0, len(data), self.blocksize):
            out = self.buffer.write(ensure_writable(data[i:i + self.blocksize]))
            self.loc += out
            bytes_written += out
            self.flush(syncFlag='DATA')
        return bytes_written

    def flush(self, syncFlag='METADATA', force=False):
        """
        Write buffered data to ADL.

        Without delimiter: Uploads the current buffer.

        With delimiter: writes an amount of data less than or equal to the
        block-size, which ends on the delimiter, until buffer is smaller than
        the blocksize. If there is no delimiter in a block uploads whole block.

        If force=True, flushes all data in the buffer, even if it doesn't end
        with a delimiter; appropriate when closing the file.
        """
        if not self.writable() or self.closed:
            return

        if not (syncFlag == 'METADATA' or syncFlag == 'DATA' or syncFlag == 'CLOSE'):
            raise ValueError('syncFlag must be one of these: METADATA, DATA or CLOSE')

        common_args_append = {
            'rest': self.azure.azure,
            'op': 'APPEND',
            'path': self.path.as_posix(),
            'append': 'true',
            'leaseid': self.leaseid,
            'filesessionid': self.filesessionid
        }
        self.buffer.seek(0)  # Go to start of buffer
        data = self.buffer.read()

        while len(data) > self.blocksize:
            data_to_write_limit = self.blocksize
            if self.delimiter:
                delimiter_index = data.rfind(self.delimiter, 0, self.blocksize)
                if delimiter_index != -1:  # delimiter found
                    data_to_write_limit = delimiter_index + len(self.delimiter)

            offset = self.tell() - len(data)
            _put_data_with_retry(syncFlag='DATA', data=data[:data_to_write_limit], offset=offset, **common_args_append)
            logger.debug('Wrote %d bytes to %s' % (data_to_write_limit, self))
            data = data[data_to_write_limit:]

        if force:
            offset = self.tell() - len(data)
            _put_data_with_retry(syncFlag=syncFlag, data=data, offset=offset, **common_args_append)
            logger.debug('Wrote %d bytes to %s' % (len(data), self))
            data = b''

        self.buffer = io.BytesIO(data)
        self.buffer.seek(0, 2)  # seek to end for other writes to buffer

    def close(self):
        """ Close file

        If in write mode, causes flush of any unwritten data.
        """
        logger.debug("closing stream")
        if self.closed:
            return
        if self.writable():
            self.flush(syncFlag='CLOSE', force=True)
            self.azure.invalidate_cache(self.path.as_posix())
        self.closed = True

    def readable(self):
        """Return whether the AzureDLFile was opened for reading"""
        return self.mode == 'rb'

    def seekable(self):
        """Return whether the AzureDLFile is seekable (only in read mode)"""
        return self.readable()

    def writable(self):
        """Return whether the AzureDLFile was opened for writing"""
        return self.mode in {'wb', 'ab'}

    def __str__(self):
        return "<ADL file: %s>" % (self.path.as_posix())

    __repr__ = __str__

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _fetch_range(rest, path, start, end, stream=False, retry_policy=ExponentialRetryPolicy(), **kwargs):
    logger.debug('Fetch: %s, %s-%s', path, start, end)
    # if the caller gives a bad start/end combination, OPEN will throw and
    # this call will bubble it up
    return rest.call(
        'OPEN', path, offset=start, length=end - start, read='true', stream=stream, retry_policy=retry_policy, **kwargs)


def _fetch_range_with_retry(rest, path, start, end, stream=False, retries=10,
                            delay=0.01, backoff=3, **kwargs):
    err = None
    retry_policy = ExponentialRetryPolicy(max_retries=retries, exponential_retry_interval=delay,
                                          exponential_factor=backoff)
    try:
        return _fetch_range(rest, path, start, end, stream=False, retry_policy=retry_policy, **kwargs)
    except Exception as e:
        err = e
        exception = RuntimeError('Max number of ADL retries exceeded: exception ' + repr(err))
        rest.log_response_and_raise(None, exception)


def _put_data(rest, op, path, data, retry_policy=ExponentialRetryPolicy(), **kwargs):
    logger.debug('Put: %s %s, %s', op, path, kwargs)
    return rest.call(op, path=path, data=data, retry_policy=retry_policy, **kwargs)


def _put_data_with_retry(rest, op, path, data, retries=10, delay=0.01, backoff=3,
                         **kwargs):
    err = None
    retry_policy = ExponentialRetryPolicy(max_retries=retries, exponential_retry_interval=delay,
                                          exponential_factor=backoff)
    try:
        return _put_data(rest, op, path, data, retry_policy=retry_policy, **kwargs)
    except (PermissionError, FileNotFoundError) as e:
        rest.log_response_and_raise(None, e)
    except DatalakeBadOffsetException as e:
        try:
            # There is a possibility that a call in previous retry succeeded in the backend
            # but didn't generate a response. In that case, any other retry will fail as the
            # data is already written. We can try a zero byte append at len(data) + offset
            # and see if it succeeds. If it does, we assume that data is written and carry on.
            current_offset = kwargs.pop('offset', None)
            if current_offset is None:
                raise e
            return _put_data(rest, op, path, [], retry_policy=retry_policy, offset=current_offset + len(data), **kwargs)
        except:
            rest.log_response_and_raise(None, e)
    except Exception as e:
        err = e
        logger.debug('Exception %s on ADL upload',
                     repr(err))
        exception = RuntimeError('Max number of ADL retries exceeded: exception ' + repr(err))
        rest.log_response_and_raise(None, exception)


class AzureDLPath(type(pathlib.PurePath())):
    """
    Subclass of native object-oriented filesystem path.

    This is used as a convenience class for reducing boilerplate and
    eliminating differences between system-dependent paths.

    We subclass the system's concrete pathlib class due to this issue:

    http://stackoverflow.com/questions/29850801/subclass-pathlib-path-fails

    Parameters
    ----------
    path: AzureDLPath or string
        location of file or directory

    Examples
    --------
    >>> p1 = AzureDLPath('/Users/foo')  # doctest: +SKIP
    >>> p2 = AzureDLPath(p1.name)  # doctest: +SKIP
    """

    def __contains__(self, s):
        """ Return whether string is contained in path. """
        return s in self.as_posix()

    def __getstate__(self):
        return self.as_posix()

    def __setstate__(self, state):
        self.__init__(state)

    @property
    def globless_prefix(self):
        """ Return shortest path prefix without glob quantifiers. """
        parts = []
        for part in self.parts:
            if any(q in part for q in ['*', '?']):
                break
            parts.append(part)
        return pathlib.PurePath(*parts)

    def startswith(self, prefix, *args, **kwargs):
        """ Return whether string starts with the prefix.

        This is equivalent to `str.startswith`.
        """
        return self.as_posix().startswith(prefix.as_posix(), *args, **kwargs)

    def trim(self):
        """ Return path without anchor (concatenation of drive and root). """
        return self.relative_to(self.anchor)
