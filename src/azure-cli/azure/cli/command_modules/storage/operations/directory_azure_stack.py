# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def list_share_directories(cmd, client, share_name, directory_name=None, timeout=None):
    t_dir_properties = cmd.get_models('file.models#DirectoryProperties')

    generator = client.list_directories_and_files(share_name, directory_name, timeout=timeout)
    return list(f for f in generator if isinstance(f.properties, t_dir_properties))
