# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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


def list_share_directories(cmd, client, share_name, directory_name=None, timeout=None):
    t_dir_properties = cmd.get_models('file.models#DirectoryProperties')

    generator = client.list_directories_and_files(share_name, directory_name, timeout=timeout)
    return list(f for f in generator if isinstance(f.properties, t_dir_properties))
