# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from .util import get_storage_client
from ._validators import validate_client_parameters


@Completer
def file_path_completer(cmd, prefix, namespace):
    from azure.common import AzureMissingResourceHttpError

    if not namespace.share_name:
        return []

    validate_client_parameters(cmd, namespace)

    t_file_service = cmd.get_models('file#FileService')
    client = get_storage_client(cmd.cli_ctx, t_file_service, namespace)

    share_name = namespace.share_name
    directory_name = prefix or ''

    try:
        items = list(client.list_directories_and_files(share_name, directory_name))
    except AzureMissingResourceHttpError:
        directory_name = directory_name.rsplit('/', 1)[0] if '/' in directory_name else ''
        items = list(client.list_directories_and_files(share_name, directory_name))

    path_format = '{}{}' if directory_name.endswith('/') or not directory_name else '{}/{}'
    names = []
    for i in items:
        name = path_format.format(directory_name, i.name)
        if not hasattr(i.properties, 'content_length'):
            name = '{}/'.format(name)
        names.append(name)

    return sorted(names)


@Completer
def dir_path_completer(cmd, prefix, namespace):
    from azure.common import AzureMissingResourceHttpError

    if not namespace.share_name:
        return []

    validate_client_parameters(cmd, namespace)

    t_file_service = cmd.get_models('file#FileService')
    client = get_storage_client(cmd.cli_ctx, t_file_service, namespace)

    share_name = namespace.share_name
    directory_name = prefix or ''

    try:
        items = list(client.list_directories_and_files(share_name, directory_name))
    except AzureMissingResourceHttpError:
        directory_name = directory_name.rsplit('/', 1)[0] if '/' in directory_name else ''
        items = list(client.list_directories_and_files(share_name, directory_name))

    dir_list = [x for x in items if not hasattr(x.properties, 'content_length')]
    path_format = '{}{}/' if directory_name.endswith('/') or not directory_name else '{}/{}/'
    names = []
    for d in dir_list:
        name = path_format.format(directory_name, d.name)
        names.append(name)

    return sorted(names)


def get_storage_name_completion_list(service, func, parent=None):
    @Completer
    def completer(cmd, _, namespace):
        validate_client_parameters(cmd, namespace)
        client = get_storage_client(cmd.cli_ctx, service, namespace)
        if parent:
            parent_name = getattr(namespace, parent)
            method = getattr(client, func)
            items = [x.name for x in method(**{parent: parent_name})]
        else:
            items = [x.name for x in getattr(client, func)()]
        return items

    return completer


def get_storage_acl_name_completion_list(service, container_param, func):
    @Completer
    def completer(cmd, _, namespace):
        validate_client_parameters(cmd, namespace)
        client = get_storage_client(cmd.cli_ctx, service, namespace)
        container_name = getattr(namespace, container_param)
        return list(getattr(client, func)(container_name))

    return completer
