# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from azure.cli.core.profiles import ResourceType

from ..util import get_datetime_from_string


def exists(cmd, client, timeout=None):
    from azure.core.exceptions import HttpResponseError
    try:
        client.get_file_system_properties(timeout=timeout)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        _dont_fail_on_exist(ex, StorageErrorCode.container_not_found)
        return False


def generate_sas_fs_uri(client, cmd, file_system, permission=None,
                        expiry=None, start=None, id=None, ip=None,  # pylint: disable=redefined-builtin
                        protocol=None, cache_control=None, content_disposition=None,
                        content_encoding=None, content_language=None,
                        content_type=None, full_uri=False, as_user=False):
    generate_file_system_sas = cmd.get_models('_shared_access_signature#generate_file_system_sas')

    sas_kwargs = {}
    if as_user:
        user_delegation_key = client.get_user_delegation_key(
            get_datetime_from_string(start) if start else datetime.utcnow(),
            get_datetime_from_string(expiry))

    sas_token = generate_file_system_sas(account_name=client.account_name, file_system_name=file_system,
                                         credential=user_delegation_key if as_user else client.credential.account_key,
                                         permission=permission, expiry=expiry, start=start, policy_id=id,
                                         ip=ip, protocol=protocol,
                                         cache_control=cache_control, content_disposition=content_disposition,
                                         content_encoding=content_encoding, content_language=content_language,
                                         content_type=content_type, **sas_kwargs)

    if full_uri:
        t_file_system_client = cmd.get_models('_file_system_client#FileSystemClient')
        file_system_client = t_file_system_client(account_url=client.url, file_system_name=file_system,
                                                  credential=sas_token)
        return file_system_client.url

    return sas_token
