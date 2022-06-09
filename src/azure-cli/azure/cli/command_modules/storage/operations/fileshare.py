# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import math

from knack.log import get_logger

from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)


def list_shares(client, prefix=None, marker=None, num_results=None,
                include_metadata=False, timeout=None, include_snapshots=False, **kwargs):
    from ..track2_util import list_generator
    generator = client.list_shares(name_starts_with=prefix, include_metadata=include_metadata, timeout=timeout,
                                   include_snapshots=include_snapshots, results_per_page=num_results, **kwargs)

    pages = generator.by_page(continuation_token=marker)  # SharePropertiesPaged
    result = list_generator(pages=pages, num_results=num_results)

    if pages.continuation_token:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)

    return result


def create_share(cmd, client, metadata=None, quota=None, fail_on_exist=False, timeout=None, **kwargs):
    from azure.core.exceptions import HttpResponseError
    try:
        client.create_share(metadata=metadata, quota=quota, timeout=timeout, **kwargs)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILESHARE)
        if not fail_on_exist:
            return _dont_fail_on_exist(ex, StorageErrorCode.share_already_exists)
        raise ex


def share_exists(cmd, client, **kwargs):
    from azure.core.exceptions import HttpResponseError
    try:
        client.get_share_properties(**kwargs)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILESHARE)
        return _dont_fail_on_exist(ex, StorageErrorCode.share_not_found)


def generate_share_sas(cmd, client, permission=None, expiry=None, start=None, policy_id=None, ip=None, protocol=None,
                       cache_control=None, content_disposition=None, content_encoding=None,
                       content_language=None, content_type=None):
    generate_share_sas_fn = cmd.get_models('_shared_access_signature#generate_share_sas')

    sas_kwargs = {'protocol': protocol}
    sas_token = generate_share_sas_fn(account_name=client.account_name, share_name=client.share_name,
                                      account_key=client.credential.account_key, permission=permission,
                                      expiry=expiry, start=start, ip=ip, cache_control=cache_control,
                                      policy_id=policy_id, content_disposition=content_disposition,
                                      content_type=content_type, content_encoding=content_encoding,
                                      content_language=content_language, **sas_kwargs)
    return sas_token


def delete_share(cmd, client, fail_not_exist=False, timeout=None, delete_snapshots=None, **kwargs):
    from azure.core.exceptions import HttpResponseError
    try:
        client.delete_share(timeout=timeout, delete_snapshots=delete_snapshots, **kwargs)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILESHARE)
        if not fail_not_exist:
            return _dont_fail_on_exist(ex, StorageErrorCode.share_not_found)
        raise ex


def get_share_stats(client, timeout=None, **kwargs):
    result = client.get_share_stats(timeout=timeout, **kwargs)
    datasize = round(int(result) / math.pow(1024, 3))
    if datasize == 0:
        return str(datasize + 1)
    return str(datasize)


def set_share_metadata(client, metadata=None, timeout=None, **kwargs):
    client.set_share_metadata(metadata=metadata, timeout=timeout, **kwargs)
    return True


def _get_client(client, kwargs):
    directory_path = kwargs.pop("directory_name", None)
    if directory_path and directory_path.startswith('./'):
        directory_path = directory_path.replace('./', '', 1)
    dir_client = client.get_directory_client(directory_path=directory_path)
    file_name = kwargs.pop("file_name", None)
    if file_name:
        total_path = directory_path + '/' + file_name if directory_path else file_name
        dir_client = client.get_directory_client(directory_path=total_path)
        exists = False
        from azure.core.exceptions import ClientAuthenticationError
        try:
            exists = dir_client.exists()
        except ClientAuthenticationError:
            exists = False
        if not exists:
            dir_client = client.get_directory_client(directory_path=directory_path)
            client = dir_client.get_file_client(file_name=file_name)
            if "recursive" in kwargs:
                kwargs.pop("recursive")
        else:
            client = dir_client
    else:
        client = dir_client
    return client


def list_handle(client, marker, num_results, **kwargs):
    from ..track2_util import list_generator
    client = _get_client(client, kwargs)

    generator = client.list_handles(results_per_page=num_results, **kwargs)
    pages = generator.by_page(continuation_token=marker)  # SharePropertiesPaged
    result = list_generator(pages=pages, num_results=num_results)

    return {"items": result, "nextMarker": pages.continuation_token}


def close_handle(client, **kwargs):
    client = _get_client(client, kwargs)

    handle = kwargs.pop("handle", None)
    if kwargs.pop("close_all", None) or handle == '*':
        return client.close_all_handles(**kwargs)
    return client.close_handle(handle=handle, **kwargs)
