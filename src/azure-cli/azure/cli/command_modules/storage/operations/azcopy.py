# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..azcopy.util import AzCopy, client_auth_for_azcopy, login_auth_for_azcopy
from azure.cli.command_modules.storage._client_factory import blob_data_service_factory, file_data_service_factory

# pylint: disable=too-many-statements, too-many-locals


def storage_copy(cmd, source=None,
                 destination=None,
                 put_md5=None,
                 recursive=None,
                 blob_type=None,
                 preserve_s2s_access_tier=None,
                 content_type=None,
                 source_account_name=None,
                 source_container=None,
                 source_blob=None,
                 source_share=None,
                 source_file_path=None,
                 source_local_path=None,
                 destination_account_name=None,
                 destination_container=None,
                 destination_blob=None,
                 destination_share=None,
                 destination_file_path=None,
                 destination_local_path=None,
                 exclude_pattern=None, include_pattern=None, exclude_path=None, include_path=None,
                 follow_symlinks=None):
    def get_url_with_sas(source, account_name, container, blob, share, file_path, local_path):
        import re
        import os
        from azure.cli.command_modules.storage._validators import _query_account_key
        from azure.cli.command_modules.storage.azcopy.util import _generate_sas_token
        storage_endpoint = cmd.cli_ctx.cloud.suffixes.storage_endpoint
        if source is not None:
            if "?" in source:  # sas token exists
                return source
            storage_pattern = re.compile(r'https://(.*?)\.(blob|dfs|file).%s' % storage_endpoint)
            result = re.findall(storage_pattern, source)
            if result:   # source is URL
                storage_info = result[0]
                account_name = storage_info[0]
                if storage_info[1] in ['blob', 'dfs']:
                    service = 'blob'
                elif storage_info[1] in ['file']:
                    service = 'file'
                else:
                    raise ValueError('Not supported service type')
                account_key = _query_account_key(cmd.cli_ctx, account_name)
            else:   # source is path
                return source
        elif account_name:
            account_key = _query_account_key(cmd.cli_ctx, account_name)
            if container:
                client = blob_data_service_factory(cmd.cli_ctx, {'account_name': account_name})
                if blob is None:
                    blob = ''
                source = client.make_blob_url(container, blob)
                service = 'blob'
            elif share:
                client = file_data_service_factory(cmd.cli_ctx,
                                                   {'account_name': account_name, 'account_key': account_key})
                dir_name, file_name = os.path.split(file_path) if file_path else (None, '')
                dir_name = None if dir_name in ('', '.') else dir_name
                source = client.make_file_url(share, dir_name, file_name)
                service = 'file'
            else:  # Only support account trandfer for blob
                source = 'https://{}.blob.core.windows.net'.format(account_name)
                service = 'blob'
        elif local_path is not None:
            return local_path
        else:
            raise ValueError('Not valid file')

        sas_token = _generate_sas_token(cmd, account_name, account_key, service)
        return _add_url_sas(source, sas_token)

    # Figure out source and destination type
    full_source = get_url_with_sas(source, source_account_name, source_container,
                                   source_blob, source_share, source_file_path, source_local_path)
    full_destination = get_url_with_sas(destination, destination_account_name, destination_container,
                                        destination_blob, destination_share, destination_file_path,
                                        destination_local_path)

    azcopy = AzCopy()
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    if put_md5 is not None:
        flags.append('--put-md5')
    if blob_type is not None:
        flags.append('--blob-type=' + blob_type)
    if preserve_s2s_access_tier is not None:
        flags.append('--s2s-preserve-access-tier=' + str(preserve_s2s_access_tier))
    if include_pattern is not None:
        flags.append('--include-pattern=' + include_pattern)
    if exclude_pattern is not None:
        flags.append('--exclude-pattern=' + exclude_pattern)
    if include_path is not None:
        flags.append('--include-path=' + include_path)
    if exclude_pattern is not None:
        flags.append('--exclude-path=' + exclude_path)
    if content_type is not None:
        flags.append('--content-type=' + content_type)
    if follow_symlinks is not None:
        flags.append('--follow-symlinks=true')
    azcopy.copy(full_source, full_destination, flags=flags)


def storage_remove(cmd, client, service, target, recursive=None, exclude_pattern=None, include_pattern=None,
                   exclude_path=None, include_path=None):
    if service == 'file':
        azcopy = _azcopy_file_client(cmd, client)
    else:
        azcopy = _azcopy_blob_client(cmd, client)
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    if include_pattern is not None:
        flags.append('--include-pattern=' + include_pattern)
    if exclude_pattern is not None:
        flags.append('--exclude-pattern=' + exclude_pattern)
    if include_path is not None:
        flags.append('--include-path=' + include_path)
    if exclude_path is not None:
        flags.append('--exclude-path=' + exclude_path)
    azcopy.remove(_add_url_sas(target, azcopy.creds.sas_token), flags=flags)


def storage_blob_sync(cmd, client, source, destination, exclude_pattern=None, include_pattern=None,
                      exclude_path=None):
    azcopy = _azcopy_blob_client(cmd, client)
    flags = ['--delete-destination=true']
    if include_pattern is not None:
        flags.append('--include-pattern=' + include_pattern)
    if exclude_pattern is not None:
        flags.append('--exclude-pattern=' + exclude_pattern)
    if exclude_path is not None:
        flags.append('--exclude-path=' + exclude_path)
    azcopy.sync(source, _add_url_sas(destination, azcopy.creds.sas_token), flags=flags)


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
    return AzCopy(creds=client_auth_for_azcopy(cmd, client))


def _azcopy_file_client(cmd, client):
    return AzCopy(creds=client_auth_for_azcopy(cmd, client, service='file'))


def _azcopy_login_client(cmd):
    return AzCopy(creds=login_auth_for_azcopy(cmd))
