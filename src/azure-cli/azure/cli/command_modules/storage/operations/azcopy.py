# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..azcopy.util import AzCopy, blob_client_auth_for_azcopy, file_client_auth_for_azcopy, login_auth_for_azcopy
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.storage._client_factory import (blob_data_service_factory,
                                                               page_blob_service_factory, file_data_service_factory,
                                                               queue_data_service_factory, table_data_service_factory)
from azure.cli.command_modules.storage._validators import _query_account_key
from azure.cli.command_modules.storage.azcopy.util import _generate_sas_token

def storage_copy(cmd, client=None, source=None, destination=None, 
                    blob_type=None, block_blob_tier=None, block_size_mb=None, cache_control=None,
                    check_md5=None, content_disposition=None, cotent_encoding=None, cotent_language=None, content_type=None,
                    exclude=None, exclude_blob_type=None, follow_symlinks=None, log_level=None, no_guess_minme_type=None,
                    overwrite=None, page_blob_tier=None, preserve_last_modified_time=None, put_md5=None, recursive=None, 
                    s2s_detect_source_changed=None, s2s_handle_invalid_metadata=None, s2s_preserve_access_tier=None, s2s_preserve_properties=None,
                    cap_mbp=None, output_type=None,
                    container_name=None, blob_name=None, destination_lease_id=None,
                    metadata=None, timeout=None,
                    source_if_modified_since=None, source_if_unmodified_since=None, source_if_match=None, source_if_none_match=None, 
                    destination_if_modified_since=None, destination_if_unmodified_since=None, destination_if_match=None, destination_if_none_match=None, 
                    copy_source=None, source_lease_id=None):
    def get_url_with_sas(source):
        import re
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
    if source is not None:
        full_source = get_url_with_sas(source)
    if destination is not None:
        full_destination = get_url_with_sas(destination)
    azcopy = AzCopy()
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    azcopy.copy(full_source, full_destination, flags=flags)

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
