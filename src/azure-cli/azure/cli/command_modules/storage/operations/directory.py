# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.profiles import ResourceType

def create_directory(client, metadata=None, fail_on_exist=False, **kwargs):
    from azure.core.exceptions import ResourceExistsError
    try:
        client.create_directory(metadata=metadata, **kwargs)
        return True
    except ResourceExistsError as ex:
        if not fail_on_exist:
            return False
        raise ex


def delete_directory(client, fail_not_exist=False, **kwargs):
    from azure.core.exceptions import ResourceNotFoundError
    try:
        client.delete_directory(**kwargs)
        return True
    except ResourceNotFoundError as ex:
        if not fail_not_exist:
            return False
        raise ex


def list_share_directories(cmd, client, exclude_extended_info=False, **kwargs):
    from ..track2_util import list_generator
    kwargs['include'] = [] if exclude_extended_info else ["timestamps", "Etag", "Attributes", "PermissionKey"]
    generator = client.list_directories_and_files(**kwargs)
    results = list_generator(pages=generator.by_page(), num_results=None)
    t_dir_properties = cmd.get_models('_models#DirectoryProperties', resource_type=ResourceType.DATA_STORAGE_FILESHARE)
    return list(f for f in results if isinstance(f, t_dir_properties))
