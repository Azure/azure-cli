# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def collect_blobs(blob_service, container, pattern=None):
    """
    List the blobs in the given blob container, filter the blob by comparing their path to the given pattern.
    """
    if not blob_service:
        raise ValueError('missing parameter blob_service')

    if not container:
        raise ValueError('missing parameter container')

    if not _pattern_has_wildcards(pattern):
        return [pattern] if blob_service.exists(container, pattern) else []

    results = []
    for blob in blob_service.list_blobs(container):
        try:
            blob_name = blob.name.encode('utf-8') if isinstance(blob.name, unicode) else blob.name
        except NameError:
            blob_name = blob.name

        if _match_path(pattern, blob_name):
            results.append(blob_name)

    return results


def collect_files(cmd, file_service, share, pattern=None):
    """
    Search files in the the given file share recursively. Filter the files by matching their path to the given pattern.
    Returns a iterable of tuple (dir, name).
    """
    if not file_service:
        raise ValueError('missing parameter file_service')

    if not share:
        raise ValueError('missing parameter share')

    if not _pattern_has_wildcards(pattern):
        return [pattern]

    return glob_files_remotely(cmd, file_service, share, pattern)


def create_blob_service_from_storage_client(cmd, client):
    t_block_blob_svc = cmd.get_models('blob#BlockBlobService')
    return t_block_blob_svc(account_name=client.account_name,
                            account_key=client.account_key,
                            sas_token=client.sas_token)


def create_file_share_from_storage_client(cmd, client):
    t_file_svc = cmd.get_models('file.fileservice#FileService')
    return t_file_svc(account_name=client.account_name,
                      account_key=client.account_key,
                      sas_token=client.sas_token)


def filter_none(iterable):
    return (x for x in iterable if x is not None)


def glob_files_locally(folder_path, pattern):
    """glob files in local folder based on the given pattern"""
    import os

    pattern = os.path.join(folder_path, pattern.lstrip('/')) if pattern else None

    from os import walk
    len_folder_path = len(folder_path) + 1
    for root, _, files in walk(folder_path):
        for f in files:
            from fnmatch import fnmatch
            full_path = os.path.join(root, f)
            if pattern and fnmatch(full_path, pattern):
                yield (full_path, full_path[len_folder_path:])
            elif not pattern:
                yield (full_path, full_path[len_folder_path:])


def glob_files_remotely(cmd, client, share_name, pattern):
    """glob the files in remote file share based on the given pattern"""
    import os
    from collections import deque
    t_dir, t_file = cmd.get_models('file.models#Directory', 'file.models#File')

    queue = deque([""])
    while queue:
        current_dir = queue.pop()
        for f in client.list_directories_and_files(share_name, current_dir):
            if isinstance(f, t_file):
                from fnmatch import fnmatch
                if (pattern and fnmatch(os.path.join(current_dir, f.name), pattern)) or (not pattern):
                    yield current_dir, f.name
            elif isinstance(f, t_dir):
                queue.appendleft(os.path.join(current_dir, f.name))


def create_short_lived_blob_sas(cmd, account_name, account_key, container, blob):
    from datetime import datetime, timedelta
    if cmd.supported_api_version(min_api='2017-04-17'):
        t_sas = cmd.get_models('blob.sharedaccesssignature#BlobSharedAccessSignature')
    else:
        t_sas = cmd.get_models('shareaccesssignature#SharedAccessSignature')

    t_blob_permissions = cmd.get_models('blob.models#BlobPermissions')
    expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sas = t_sas(account_name, account_key)
    return sas.generate_blob(container, blob, permission=t_blob_permissions(read=True), expiry=expiry, protocol='https')


def create_short_lived_file_sas(cmd, account_name, account_key, share, directory_name, file_name):
    from datetime import datetime, timedelta
    if cmd.supported_api_version(min_api='2017-04-17'):
        t_sas = cmd.get_models('file.sharedaccesssignature#FileSharedAccessSignature')
    else:
        t_sas = cmd.get_models('sharedaccesssignature#SharedAccessSignature')

    t_file_permissions = cmd.get_models('file.models#FilePermissions')
    # if dir is empty string change it to None
    directory_name = directory_name if directory_name else None
    expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sas = t_sas(account_name, account_key)
    return sas.generate_file(share, directory_name=directory_name, file_name=file_name,
                             permission=t_file_permissions(read=True), expiry=expiry, protocol='https')


def create_short_lived_container_sas(cmd, account_name, account_key, container):
    from datetime import datetime, timedelta
    if cmd.supported_api_version(min_api='2017-04-17'):
        t_sas = cmd.get_models('blob.sharedaccesssignature#BlobSharedAccessSignature')
    else:
        t_sas = cmd.get_models('sharedaccesssignature#SharedAccessSignature')
    t_blob_permissions = cmd.get_models('blob.models#BlobPermissions')

    expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sas = t_sas(account_name, account_key)
    return sas.generate_container(container, permission=t_blob_permissions(read=True), expiry=expiry, protocol='https')


def create_short_lived_share_sas(cmd, account_name, account_key, share):
    from datetime import datetime, timedelta
    if cmd.supported_api_version(min_api='2017-04-17'):
        t_sas = cmd.get_models('file.sharedaccesssignature#FileSharedAccessSignature')
    else:
        t_sas = cmd.get_models('sharedaccesssignature#SharedAccessSignature')

    t_file_permissions = cmd.get_models('file.models#FilePermissions')
    expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sas = t_sas(account_name, account_key)
    return sas.generate_share(share, permission=t_file_permissions(read=True), expiry=expiry, protocol='https')


def mkdir_p(path):
    import errno
    import os
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
    from fnmatch import fnmatch
    import os
    return fnmatch(os.path.join(*args), pattern) if pattern else True


def guess_content_type(file_path, original, settings_class):
    if original.content_encoding or original.content_type:
        return original

    import mimetypes

    content_type, _ = mimetypes.guess_type(file_path)
    return settings_class(
        content_type=content_type,
        content_encoding=original.content_encoding,
        content_disposition=original.content_disposition,
        content_language=original.content_language,
        content_md5=original.content_md5,
        cache_control=original.cache_control)


def get_storage_client(cli_ctx, service_type, namespace):
    from azure.cli.command_modules.storage._client_factory import get_storage_data_service_client

    az_config = cli_ctx.config

    name = getattr(namespace, 'account_name', az_config.get('storage', 'account', None))
    key = getattr(namespace, 'account_key', az_config.get('storage', 'key', None))
    connection_string = getattr(namespace, 'connection_string', az_config.get('storage', 'connection_string', None))
    sas_token = getattr(namespace, 'sas_token', az_config.get('storage', 'sas_token', None))

    return get_storage_data_service_client(cli_ctx, service_type, name, key, connection_string, sas_token)
