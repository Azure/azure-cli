# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..azcopy.util import AzCopy, client_auth_for_azcopy, login_auth_for_azcopy


def storage_blob_copy(azcopy, source, destination, recursive=None):
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    azcopy.copy(source, destination, flags=flags)


def storage_remove(cmd, client, service, target, exclude=None, include=None, recursive=None):
    if service == 'file':
        azcopy = _azcopy_file_client(cmd, client)
    else:
        azcopy = _azcopy_blob_client(cmd, client)
    flags = []
    if recursive is not None:
        flags.append('--recursive')
    if include is not None:
        flags.append('--include=' + include)
    if exclude is not None:
        flags.append('--exclude=' + exclude)
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
    return AzCopy(creds=client_auth_for_azcopy(cmd, client))


def _azcopy_file_client(cmd, client):
    return AzCopy(creds=client_auth_for_azcopy(cmd, client, service='file'))


def _azcopy_login_client(cmd):
    return AzCopy(creds=login_auth_for_azcopy(cmd))
