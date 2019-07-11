# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..azcopy.util import AzCopy, blob_client_auth_for_azcopy, file_client_auth_for_azcopy, login_auth_for_azcopy
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.storage._client_factory import file_data_service_factory

def storage_copy(cmd, client, source=None, destination=None, container_name=None, blob_name=None, copy_source=None,
                  metadata=None, source_if_modified_since=None,
                  source_if_unmodified_since=None, source_if_match=None,
                  source_if_none_match=None, destination_if_modified_since=None,
                  destination_if_unmodified_since=None, destination_if_match=None,
                  destination_if_none_match=None, destination_lease_id=None,
                  source_lease_id=None, timeout=None, requires_sync=None,recursive=None):
    
    # Figure out source and destination type
    if source is not None:
        full_source = get_url_with_sas(source)
    elif 
    if destination is not None:
        full_destination = get_url_with_sas(destination)
    azcopy = AzCopy()       
    azcopy.copy(full_source, full_destination, flags)

    def get_url_with_sas(source):
        import re
        storage_pattern = re.compile(r'https://(.*?)\.(blob|dfs|file).core.windows.net')
        result = re.findall(storage_pattern)
        sas_pattern = re.compile(r'?(.*?)')
        if result is not None: # Azure storage account
            storage_info = result[0]
            storage_account = storage_info[0]
            storage_service = storage_info[1]
            if "?" in source: # sas token exists
                return source
            else: # no sas token
                if storage_service in ['blob', 'dfs']:
                    creds=blob_client_auth_for_azcopy(cmd, client)
                elif storage_service == 'file':
                    file_client = CliCommandType(
                        operations_tmpl='azure.multiapi.storage.file.fileservice#FileService.{}',
                        client_factory=file_data_service_factory,
                        resource_type=ResourceType.DATA_STORAGE)
                    creds=file_client_auth_for_azcopy(cmd, file_client)
                return _add_url_sas(source, creds.sas_token)
        else:
            return source


def storage_blob_copy(azcopy, source, destination, recursive=None):
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    azcopy.copy(source, destination, flags=flags)


def storage_blob_upload(cmd, client, source, destination, recursive=None):
    azcopy = _azcopy_blob_client(cmd, client)
    storage_blob_copy(azcopy, source, _add_url_sas(destination, azcopy.creds.sas_token), recursive=recursive)


def storage_blob_download(cmd, client, source, destination, recursive=None):
    azcopy = _azcopy_blob_client(cmd, client)
    storage_blob_copy(azcopy, _add_url_sas(source, azcopy.creds.sas_token), destination, recursive=recursive)


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
