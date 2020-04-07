# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Custom operations for storage file datalake"""

import os

from azure.core.exceptions import HttpResponseError
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.command_modules.storage._client_factory import storage_client_factory, cf_sa_for_keys
from azure.cli.core.util import get_file_json, shell_safe_json_parse
from azure.cli.command_modules.storage.util import mkdir_p
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def append_file(client, content):
    file = client.get_file_properties()
    # START append data
    client.append_data(data=content, offset=file.size, length=len(content))
    # END append data
    return client.flush_data(offset=len(content))


def download_file(client, destination_path=None, overwrite=True):
    destination_folder = os.path.dirname(destination_path) if destination_path else ""
    if destination_folder and not os.path.exists(destination_folder):
        mkdir_p(destination_folder)

    if not destination_folder or os.path.isdir(destination_path):
        file = client.get_file_properties()
        file_name = file.name.split("/")[-1]
        destination_path = os.path.join(destination_path, file_name) \
            if destination_path else file_name

    if not overwrite:
        raise CLIError('The specified path already exists. Please change to a valid path. ')

    with open(destination_path, 'wb') as stream:
        download = client.download_file()
        download_content = download.readall()
        stream.write(download_content)
    return None


def exists(cmd, client):
    try:
        client.get_file_properties()
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.sdkutil import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        _dont_fail_on_exist(ex, StorageErrorCode.blob_not_found)
        return False


def list_fs_files(client, path=None, recursive=True, num_results=None, upn=None, timeout=None, exclude_dir=None):
    generator = client.get_paths(path=path, recursive=recursive, timeout=timeout, max_results=num_results)

    if exclude_dir:
        return list(f for f in generator if not f.is_directory)

    return generator


def upload_file(cmd, client, local_path, overwrite=False, metadata=None, unmask=None, permissions=None):
    if not exists(cmd, client):
        client.create_file()
    """
    local_file = open(local_path, 'r')
    data = local_file.read()
    """
    count = os.path.getsize(local_path)
    with open(local_path, 'rb') as stream:
        data = stream.read(count)

    return client.upload_data(data=data, length=count, overwrite=overwrite, metadata=metadata, umaskoverwrite=unmask,
                              permissions=permissions)
