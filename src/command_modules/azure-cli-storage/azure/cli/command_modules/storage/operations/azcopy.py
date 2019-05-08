# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..azcopy.util import AzCopy, blob_client_auth_for_azcopy, login_auth_for_azcopy


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
    azcopy.sync(source, _add_url_sas(destination, azcopy.creds.sas_token), flags=['--delete-destination true'])


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
