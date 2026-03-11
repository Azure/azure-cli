# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from azure.cli.core.profiles import ResourceType

from ..util import get_datetime_from_string


def create_file_system(cmd, client, metadata=None, public_access=None,
                       default_encryption_scope=None, prevent_encryption_scope_override=None, **kwargs):
    encryption_scope = None
    if default_encryption_scope is not None or prevent_encryption_scope_override is not None:
        EncryptionScopeOptions = cmd.get_models('_models#EncryptionScopeOptions',
                                                resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        encryption_scope = EncryptionScopeOptions(default_encryption_scope=default_encryption_scope,
                                                  prevent_encryption_scope_override=prevent_encryption_scope_override)
    return client.create_file_system(metadata=metadata, public_access=public_access,
                                     encryption_scope_options=encryption_scope, **kwargs)


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
                        content_type=None, full_uri=False, as_user=False, encryption_scope=None,
                        user_delegation_oid=None):
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
                                         content_type=content_type, encryption_scope=encryption_scope,
                                         user_delegation_oid=user_delegation_oid, **sas_kwargs)

    if full_uri:
        t_file_system_client = cmd.get_models('_file_system_client#FileSystemClient')
        file_system_client = t_file_system_client(account_url=client.url, file_system_name=file_system,
                                                  credential=sas_token)
        return file_system_client.url

    return sas_token


def list_deleted_path(client, marker=None, num_results=None, path_prefix=None, timeout=None, **kwargs):
    from ..track2_util import list_generator

    generator = client.list_deleted_paths(path_prefix=path_prefix, timeout=timeout,
                                          results_per_page=num_results, **kwargs)

    pages = generator.by_page(continuation_token=marker)  # BlobPropertiesPaged
    result = list_generator(pages=pages, num_results=num_results)

    if pages.continuation_token:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)

    return result


def set_service_properties(cmd, client, delete_retention=None, delete_retention_period=None,
                           enable_static_website=False, index_document=None, error_document_404_path=None):
    parameters = client.get_service_properties()
    # update
    kwargs = {}
    delete_retention_policy = cmd.get_models('_models#RetentionPolicy',
                                             resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)()
    if parameters.get('delete_retention_policy', None):
        delete_retention_policy = parameters['delete_retention_policy']
    if delete_retention is not None:
        delete_retention_policy.enabled = delete_retention
    if delete_retention_period is not None:
        delete_retention_policy.days = delete_retention_period
    delete_retention_policy.allow_permanent_delete = False

    static_website = cmd.get_models('_models#StaticWebsite',
                                    resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)()
    if parameters.get('static_website', None):
        static_website = parameters['static_website']

    if static_website is not None:
        static_website.enabled = enable_static_website
    if index_document is not None:
        static_website.index_document = index_document
    if error_document_404_path is not None:
        static_website.error_document_404_path = error_document_404_path

    if parameters.get('hour_metrics', None):
        kwargs['hour_metrics'] = parameters['hour_metrics']
    if parameters.get('logging', None):
        kwargs['logging'] = parameters['logging']
    if parameters.get('minute_metrics', None):
        kwargs['minute_metrics'] = parameters['minute_metrics']
    if parameters.get('cors', None):
        kwargs['cors'] = parameters['cors']

    # checks
    if delete_retention_policy and delete_retention_policy.enabled and not delete_retention_policy.days:
        from azure.cli.core.azclierror import InvalidArgumentValueError
        raise InvalidArgumentValueError("must specify days-retained")

    client.set_service_properties(delete_retention_policy=delete_retention_policy, static_website=static_website,
                                  **kwargs)
    return client.get_service_properties()
