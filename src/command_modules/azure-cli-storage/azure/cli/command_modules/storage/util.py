# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path
from fnmatch import fnmatch

from azure.cli.core.profiles import get_sdk, ResourceType


def collect_blobs(blob_service, container, pattern=None):
    """
    List the blobs in the given blob container, filter the blob by comparing their path to the given
    pattern.
    """
    # TODO: deal with container which contains more that 5000 files.
    #       In that case, the listing operation will page the results.

    if not blob_service:
        raise ValueError('missing parameter blob_service')

    if not container:
        raise ValueError('missing parameter container')

    if not _pattern_has_wildcards(pattern):
        return [pattern]

    return (blob.name for blob in blob_service.list_blobs(container) if _match_path(pattern, blob.name))


def collect_files(file_service, share, pattern=None):
    """
    Search files in the the given file share recursively. Filter the files by matching their path
    to the given pattern. Returns a iterable of tuple (dir, name).
    """
    if not file_service:
        raise ValueError('missing parameter file_service')

    if not share:
        raise ValueError('missing parameter share')

    if not _pattern_has_wildcards(pattern):
        return [pattern]

    return glob_files_remotely(file_service, share, pattern)


def create_blob_service_from_storage_client(client):
    BlockBlobService = get_sdk(ResourceType.DATA_STORAGE, 'blob.blockblobservice#BlockBlobService')
    return BlockBlobService(account_name=client.account_name,
                            account_key=client.account_key,
                            sas_token=client.sas_token)


def create_file_share_from_storage_client(client):
    FileService = get_sdk(ResourceType.DATA_STORAGE, 'file.fileservice#FileService')
    return FileService(account_name=client.account_name,
                       account_key=client.account_key,
                       sas_token=client.sas_token)


def filter_none(iterable):
    return (x for x in iterable if x is not None)


def glob_files_locally(folder_path, pattern):
    """glob files in local folder based on the given pattern"""
    pattern = os.path.join(folder_path, pattern.lstrip('/')) if pattern else None

    from os import walk
    len_folder_path = len(folder_path) + 1
    for root, _, files in walk(folder_path):
        for f in files:
            full_path = os.path.join(root, f)
            if pattern and fnmatch(full_path, pattern):
                yield (full_path, full_path[len_folder_path:])
            elif not pattern:
                yield (full_path, full_path[len_folder_path:])


def glob_files_remotely(client, share_name, pattern):
    """glob the files in remote file share based on the given pattern"""
    from collections import deque
    Directory, File = get_sdk(ResourceType.DATA_STORAGE,
                              'file.models#Directory',
                              'file.models#File')

    queue = deque([""])
    while queue:
        current_dir = queue.pop()
        for f in client.list_directories_and_files(share_name, current_dir):
            if isinstance(f, File):
                if (pattern and fnmatch(os.path.join(current_dir, f.name), pattern)) or \
                   (not pattern):
                    yield current_dir, f.name
            elif isinstance(f, Directory):
                queue.appendleft(os.path.join(current_dir, f.name))


def create_short_lived_container_sas(account_name, account_key, container):
    from datetime import datetime, timedelta
    SharedAccessSignature, BlobPermissions = \
        get_sdk(ResourceType.DATA_STORAGE,
                'sharedaccesssignature#SharedAccessSignature',
                'blob.models#BlobPermissions')

    expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sas = SharedAccessSignature(account_name, account_key)
    return sas.generate_container(container, permission=BlobPermissions(read=True), expiry=expiry,
                                  protocol='https')


def create_short_lived_share_sas(account_name, account_key, share):
    from datetime import datetime, timedelta
    SharedAccessSignature, BlobPermissions = \
        get_sdk(ResourceType.DATA_STORAGE,
                'sharedaccesssignature#SharedAccessSignature',
                'blob.models#BlobPermissions')

    expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sas = SharedAccessSignature(account_name, account_key)
    return sas.generate_share(share, permission=BlobPermissions(read=True), expiry=expiry,
                              protocol='https')


def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python <= 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def _pattern_has_wildcards(p):
    return not p or p.find('*') != -1 or p.find('?') != -1 or p.find('[') != -1


def _match_path(pattern, *args):
    return fnmatch(os.path.join(*args), pattern) if pattern else True
