# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Custom operations for storage file datalake"""

from datetime import datetime
from azure.cli.core.profiles import ResourceType

from knack.util import todict

from ..util import get_datetime_from_string


def exists(cmd, client, timeout=None):
    from azure.core.exceptions import HttpResponseError
    try:
        client.get_directory_properties(timeout=timeout)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        _dont_fail_on_exist(ex, StorageErrorCode.blob_not_found)
        return False


def list_fs_directories(client, path=None, recursive=True, num_results=None, timeout=None):
    generator = client.get_paths(path=path, recursive=recursive, timeout=timeout, max_results=num_results)

    return list(f for f in generator if f.is_directory)


def get_directory_properties(client, timeout=None):
    from .._transformers import transform_fs_access_output
    prop = todict(client.get_directory_properties(timeout=timeout))
    acl = transform_fs_access_output(client.get_access_control(timeout=timeout))
    result = dict(prop, **acl)
    return result


def remove_access_control_recursive(client, acl, **kwargs):
    failed_entries = []

    # the progress callback is invoked each time a batch is completed
    def progress_callback(acl_changes):
        # keep track of failed entries if there are any
        if acl_changes.batch_failures:
            failed_entries.extend(acl_changes.batch_failures)

    result = client.remove_access_control_recursive(acl=acl, progress_hook=progress_callback, **kwargs)
    result = todict(result)
    result['failedEntries'] = failed_entries
    return result


def set_access_control_recursive(client, acl, **kwargs):
    failed_entries = []

    # the progress callback is invoked each time a batch is completed
    def progress_callback(acl_changes):
        # keep track of failed entries if there are any
        if acl_changes.batch_failures:
            failed_entries.extend(acl_changes.batch_failures)

    result = client.set_access_control_recursive(acl=acl, progress_hook=progress_callback, **kwargs)
    result = todict(result)
    result['failedEntries'] = failed_entries
    return result


def update_access_control_recursive(client, acl, **kwargs):
    failed_entries = []

    # the progress callback is invoked each time a batch is completed
    def progress_callback(acl_changes):
        # keep track of failed entries if there are any
        if acl_changes.batch_failures:
            failed_entries.extend(acl_changes.batch_failures)

    result = client.update_access_control_recursive(acl=acl, progress_hook=progress_callback, **kwargs)
    result = todict(result)
    result['failedEntries'] = failed_entries
    return result


def fix_url_path(url):
    # Change https://xx.dfs.core.windows.net/test/dir1%2Fdir2 to https://xx.dfs.core.windows.net/test/dir1/dir2
    from urllib.parse import urlparse, urlunparse, unquote, quote
    url_parts = urlparse(url)
    fixed_path = quote(unquote(url_parts.path), '/()$=\',~')
    return urlunparse(url_parts[:2] + (fixed_path,) + url_parts[3:])


def generate_sas_directory_uri(client, cmd, file_system_name, directory_name, permission=None,
                               expiry=None, start=None, id=None, ip=None,  # pylint: disable=redefined-builtin
                               protocol=None, cache_control=None, content_disposition=None,
                               content_encoding=None, content_language=None,
                               content_type=None, full_uri=False, as_user=False, ):
    from urllib.parse import quote
    generate_directory_sas = cmd.get_models('_shared_access_signature#generate_directory_sas')

    sas_kwargs = {}
    if as_user:
        user_delegation_key = client.get_user_delegation_key(
            get_datetime_from_string(start) if start else datetime.utcnow(),
            get_datetime_from_string(expiry))

    sas_token = generate_directory_sas(account_name=client.account_name, file_system_name=file_system_name,
                                       directory_name=directory_name,
                                       credential=user_delegation_key if as_user else client.credential.account_key,
                                       permission=permission, expiry=expiry, start=start, policy_id=id,
                                       ip=ip, protocol=protocol,
                                       cache_control=cache_control, content_disposition=content_disposition,
                                       content_encoding=content_encoding, content_language=content_language,
                                       content_type=content_type, **sas_kwargs)
    sas_token = quote(sas_token, safe='&%()$=\',~')
    if full_uri:
        t_directory_client = cmd.get_models('_data_lake_directory_client#DataLakeDirectoryClient')
        directory_client = t_directory_client(account_url=client.url, file_system_name=file_system_name,
                                              directory_name=directory_name, credential=sas_token)
        return fix_url_path(directory_client.url)

    return sas_token
