# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..azcopy.util import AzCopy, blob_client_auth_for_azcopy, file_client_auth_for_azcopy, login_auth_for_azcopy
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.storage._client_factory import (blob_data_service_factory,file_data_service_factory)


def storage_copy(cmd, client=None, source=None, destination=None, 
                    check_md5="FailIfDifferent", put_md5=None, recursive=None, 
                    metadata=None, timeout=None,
                    source_if_modified_since=None, source_if_unmodified_since=None, source_if_match=None, source_if_none_match=None, 
                    destination_if_modified_since=None, destination_if_unmodified_since=None, destination_if_match=None, destination_if_none_match=None,
                    source_account_name=None, source_container_name=None, source_blob_name=None, source_share_name=None, source_file_path=None,
                    destination_account_name=None, destination_container_name=None, destination_blob_name=None, destination_share_name=None, destination_file_path=None):
    def get_url_with_sas(url=None, account_name=None, container_name=None, blob_name=None, share_name=None, file_path=None):
        import re
        import os
        from azure.cli.command_modules.storage._validators import _query_account_key
        from azure.cli.command_modules.storage.azcopy.util import _generate_sas_token
        if url is not None:
            source = url
        elif account_name:
            if container_name:
                client = blob_data_service_factory(cmd.cli_ctx, {'account_name': account_name})
                if blob_name is None:
                    blob_name = ''
                source = client.make_blob_url(container_name, blob_name)
            elif share_name:
                account_key = _query_account_key(cmd.cli_ctx, account_name)
                client = file_data_service_factory(cmd.cli_ctx, {'account_name': account_name, 'account_key': account_key})
                dir_name, file_name = os.path.split(file_path) if file_path else (None, '')
                dir_name = None if dir_name in ('', '.') else dir_name
                source = client.make_file_url(share_name, dir_name, file_name)
        else:
            raise ValueError('Not valid file')

        storage_pattern = re.compile(r'https://(.*?)\.(blob|dfs|file).core.windows.net')
        result = re.findall(storage_pattern, source)
        if result: # Azure storage account
            storage_info = result[0]
            account_name = storage_info[0]
            service = storage_info[1]
            if "?" in source: # sas token exists
                return source
            else: # no sas token
                account_key = _query_account_key(cmd.cli_ctx, account_name)
                if service in ['blob', 'dfs']:
                    service = 'blob'
                if service not in ['blob', 'file']:
                    # error
                    usage_string = \
                        'Invalid usage: {}. Supply only one of the following argument sets to specify source:' \
                        '\n\t   --container-name  --name' \
                        '\n\tOR --share-name --path'
                    raise ValueError(usage_string.format('Neither a valid blob or file source is specified'))
                else:
                    sas_token = _generate_sas_token(cmd, account_name, account_key, service)
                    return _add_url_sas(source, sas_token)
        else:
            return source
    # Figure out source and destination type
    full_source = get_url_with_sas(source, source_account_name, source_container_name, source_blob_name, source_share_name, source_file_path)
    full_destination = get_url_with_sas(destination, destination_account_name, destination_container_name, destination_blob_name, destination_share_name, destination_file_path)

    azcopy = AzCopy()
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    if put_md5 is not None:
        flags.append('--put-md5')

    azcopy.copy(full_source, full_destination, flags=flags)

def storage_blob_remove(cmd, client, target, recursive=None):
    azcopy = _azcopy_blob_client(cmd, client)
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    azcopy.remove(_add_url_sas(target, azcopy.creds.sas_token), flags=flags)


def storage_blob_sync(cmd, client, source, destination):
    azcopy = _azcopy_blob_client(cmd, client)
    azcopy.sync(source, _add_url_sas(destination, azcopy.creds.sas_token), flags=['--delete-destination', 'true'])


def storage_run_command(cmd, command_args):
    if command_args.startswith('azcopy'):
        command_args = command_args[len('azcopy'):]
    azcopy = _azcopy_login_client(cmd)
    azcopy.run_command([command_args])


def _add_url_sas(url, sas):
    if not sas:
        return url
    return '{}?{}'.format(url, sas)


def _azcopy_blob_client(cmd, client):
    return AzCopy(creds=blob_client_auth_for_azcopy(cmd, client))


def _azcopy_login_client(cmd):
    return AzCopy(creds=login_auth_for_azcopy(cmd))
