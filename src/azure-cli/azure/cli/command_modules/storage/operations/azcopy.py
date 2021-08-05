# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..azcopy.util import AzCopy, client_auth_for_azcopy, login_auth_for_azcopy, _generate_sas_token


# pylint: disable=too-many-statements, too-many-locals, unused-argument
def storage_copy(source, destination, put_md5=None, recursive=None, blob_type=None,
                 preserve_s2s_access_tier=None, content_type=None, follow_symlinks=None,
                 exclude_pattern=None, include_pattern=None, exclude_path=None, include_path=None,
                 cap_mbps=None, **kwargs):

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
    if cap_mbps is not None:
        flags.append('--cap-mbps=' + cap_mbps)
    azcopy.copy(source, destination, flags=flags)


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

    sas_token = client.sas_token

    if not sas_token and client.account_key:
        sas_token = _generate_sas_token(cmd, client.account_name, client.account_key, service=service,
                                        resource_types='co',
                                        permissions='rdl')

    azcopy.remove(_add_url_sas(target, sas_token), flags=flags)


# pylint: disable=unused-argument
def storage_fs_directory_copy(cmd, source, destination, recursive=None, **kwargs):
    azcopy = AzCopy()
    if kwargs.get('token_credential'):
        azcopy = _azcopy_login_client(cmd)

    flags = []
    if recursive:
        flags.append('--recursive')
    azcopy.copy(source, destination, flags=flags)


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

    sas_token = client.sas_token

    if not sas_token and client.account_key:
        sas_token = _generate_sas_token(cmd, client.account_name, client.account_key, service='blob',
                                        resource_types='co',
                                        permissions='rwdlac')

    azcopy.sync(source, _add_url_sas(destination, sas_token), flags=flags)


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
