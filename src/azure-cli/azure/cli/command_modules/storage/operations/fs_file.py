# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Custom operations for storage file datalake"""

import os

from azure.core.exceptions import HttpResponseError
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.storage.util import mkdir_p
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def append_file(client, content, timeout=None):
    file = client.get_file_properties(timeout=timeout)
    # START append data
    client.append_data(data=content, offset=file.size, length=len(content), timeout=timeout)
    # END append data
    return client.flush_data(offset=file.size + len(content), timeout=timeout)


def download_file(client, destination_path=None, overwrite=True, timeout=None):
    destination_folder = os.path.dirname(destination_path) if destination_path else ""
    if destination_folder and not os.path.exists(destination_folder):
        mkdir_p(destination_folder)

    if not destination_folder or os.path.isdir(destination_path):
        file = client.get_file_properties(timeout=timeout)
        file_name = file.name.split("/")[-1]
        destination_path = os.path.join(destination_path, file_name) \
            if destination_path else file_name

    if not overwrite and os.path.exists(destination_path):
        raise CLIError('The specified path already exists. Please change to a valid path. ')

    with open(destination_path, 'wb') as stream:
        download = client.download_file(timeout=timeout)
        download_content = download.readall()
        stream.write(download_content)


def exists(cmd, client, timeout=None):
    try:
        client.get_file_properties(timeout=timeout)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        _dont_fail_on_exist(ex, StorageErrorCode.blob_not_found)
        return False


def get_file_properties(client, timeout=None):
    from .._transformers import transform_fs_access_output

    prop = client.get_file_properties(timeout=timeout)
    if prop.content_settings.content_md5 is not None:
        from msrest import Serializer
        prop.content_settings.content_md5 = Serializer.serialize_bytearray(prop.content_settings.content_md5)

    acl = transform_fs_access_output(client.get_access_control(timeout=timeout))
    result = dict(prop, **acl)
    return result


def list_fs_files(client, path=None, recursive=True, num_results=None, timeout=None, exclude_dir=None,
                  marker=None, show_next_marker=None):
    generator = client.get_paths(path=path, max_results=num_results, recursive=recursive, timeout=timeout)
    pages = generator.by_page(continuation_token=marker)

    result = list(next(pages))

    if exclude_dir:
        result = list(f for f in result if not f.is_directory)

    if show_next_marker:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)
    else:
        if pages.continuation_token:
            logger.warning('Next Marker:')
            logger.warning(pages.continuation_token)

    return result


def upload_file(cmd, client, local_path, overwrite=None, content_settings=None, metadata=None, timeout=None,
                if_match=None, if_none_match=None, if_modified_since=None, if_unmodified_since=None,
                umask=None, permissions=None):

    from azure.core import MatchConditions
    upload_file_args = {
        'content_settings': content_settings,
        'metadata': metadata,
        'timeout': timeout,
        'if_modified_since': if_modified_since,
        'if_unmodified_since': if_unmodified_since,
        'permissions': permissions,
        'umask': umask
    }

    # Precondition Check
    if if_match:
        if if_match == '*':
            upload_file_args['match_condition'] = MatchConditions.IfPresent
        else:
            upload_file_args['etag'] = if_match
            upload_file_args['match_condition'] = MatchConditions.IfNotModified

    if if_none_match:
        upload_file_args['etag'] = if_none_match
        upload_file_args['match_condition'] = MatchConditions.IfModified

    # Overwrite sets to true will overwrite existing data.
    # Overwrite sets to false will be able to upload to empty file and non-existing file,
    # but will raise exception when uploading to non-empty file with new data.
    if not overwrite:

        # For non-existing file path, create one
        if not exists(cmd, client):
            client.create_file(permissions=permissions, umask=umask)

        upload_file_args['match_condition'] = MatchConditions.IfPresent
        try:
            count = os.path.getsize(local_path)
            with open(local_path, 'rb') as stream:
                response = client.upload_data(data=stream, length=count, overwrite=overwrite, **upload_file_args)
            return response
        except HttpResponseError as ex:
            StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                              resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)

            if ex.error_code == StorageErrorCode.invalid_flush_position:  # pylint: disable=no-member
                raise CLIError("You cannot upload to an existing non-empty file with overwrite=false. "
                               "Please set --overwrite to overwrite the existing file.")
            raise ex
    count = os.path.getsize(local_path)
    with open(local_path, 'rb') as stream:
        response = client.upload_data(data=stream, length=count, overwrite=overwrite, **upload_file_args)
    return response
