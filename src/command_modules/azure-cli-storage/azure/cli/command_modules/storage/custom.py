#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments

from __future__ import print_function
from sys import stderr

from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.mgmt.storage.models import Kind

from azure.cli.command_modules.storage._factory import storage_client_factory
from azure.cli._util import CLIError

def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        percent_done = current * 100 / total
        message += '{: >5.1f}'.format(percent_done)
        print('\b' * len(message) + message, end='', file=stderr)
        stderr.flush()
        if current == total:
            print('', file=stderr)

# CUSTOM METHODS

def list_storage_accounts(resource_group_name=None):
    ''' List storage accounts. '''
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    scf = storage_client_factory()
    if resource_group_name:
        accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
    else:
        accounts = scf.storage_accounts.list()
    return list(accounts)

def renew_storage_account_keys(resource_group_name, account_name, key='both'):
    """ Regenerate one or both keys for a storage account. """
    from azure.cli.command_modules.storage._params import storage_account_key_options
    scf = storage_client_factory()
    for k in storage_account_key_options[key]:
        result = scf.storage_accounts.regenerate_key(
            resource_group_name=resource_group_name,
            account_name=account_name,
            key_name=k)
    return result

def show_storage_account_usage():
    ''' Show the current count and limit of the storage accounts under the subscription. '''
    scf = storage_client_factory()
    return next((x for x in scf.usage.list().value if x.name.value == 'StorageAccounts'), None) #pylint: disable=no-member

def show_storage_account_connection_string(resource_group_name, account_name, protocol='https'):
    """ Show the connection string for a storage account."""
    scf = storage_client_factory()
    keys = scf.storage_accounts.list_keys(resource_group_name, account_name).keys #pylint: disable=no-member
    connection_string = 'DefaultEndpointsProtocol={};AccountName={};AccountKey={}'.format(
        protocol,
        account_name,
        keys[0].value) #pylint: disable=no-member
    return {'ConnectionString':connection_string}

def create_storage_account(resource_group_name, account_name, sku, location,
                           kind=Kind.storage.value, tags=None, custom_domain=None,
                           encryption=None, access_tier=None):
    ''' Create a storage account. '''
    from azure.mgmt.storage.models import \
        (StorageAccountCreateParameters, Sku, CustomDomain, Encryption, AccessTier)
    scf = storage_client_factory()
    params = StorageAccountCreateParameters(
        sku=Sku(sku),
        kind=Kind(kind),
        location=location,
        tags=tags,
        custom_domain=CustomDomain(custom_domain) if custom_domain else None,
        encryption=Encryption(encryption) if encryption else None,
        access_tier=AccessTier(access_tier) if access_tier else None)
    return scf.storage_accounts.create(resource_group_name, account_name, params)

def set_storage_account_properties(
        resource_group_name, account_name, sku=None, tags=None, custom_domain=None,
        encryption=None, access_tier=None):
    ''' Update storage account property (only one at a time).'''
    from azure.mgmt.storage.models import \
        (StorageAccountUpdateParameters, Sku, CustomDomain, Encryption, AccessTier)
    scf = storage_client_factory()
    params = StorageAccountUpdateParameters(
        sku=Sku(sku) if sku else None,
        tags=tags,
        custom_domain=CustomDomain(custom_domain) if custom_domain else None,
        encryption=Encryption(encryption) if encryption else None,
        access_tier=AccessTier(access_tier) if access_tier else None)
    return scf.storage_accounts.update(resource_group_name, account_name, params)

def upload_blob( # pylint: disable=too-many-locals
        client, container_name, blob_name, blob_type, file_path,
        content_type=None, content_disposition=None,
        content_encoding=None, content_language=None, content_md5=None,
        content_cache_control=None, metadata=None, validate_content=False, maxsize_condition=None,
        max_connections=2, max_retries=5, retry_wait=1, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
    '''Upload a blob to a container.'''
    from azure.storage.blob import ContentSettings
    content_settings = ContentSettings(
        content_type=content_type,
        content_disposition=content_disposition,
        content_encoding=content_encoding,
        content_language=content_language,
        content_md5=content_md5,
        cache_control=content_cache_control
    )

    def upload_append_blob():
        if not client.exists(container_name, blob_name):
            client.create_blob(
                container_name=container_name,
                blob_name=blob_name,
                content_settings=content_settings,
                metadata=metadata,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_match=if_match,
                if_none_match=if_none_match,
                timeout=timeout)
        return client.append_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=_update_progress,
            validate_content=validate_content,
            maxsize_condition=maxsize_condition,
            lease_id=lease_id,
            max_retries=max_retries,
            retry_wait=retry_wait,
            timeout=timeout)

    def upload_block_blob():
        return client.create_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=_update_progress,
            content_settings=content_settings,
            metadata=metadata,
            validate_content=validate_content,
            max_connections=max_connections,
            max_retries=max_retries,
            retry_wait=retry_wait,
            lease_id=lease_id,
            if_modified_since=if_modified_since,
            if_unmodified_since=if_unmodified_since,
            if_match=if_match,
            if_none_match=if_none_match,
            timeout=timeout
        )

    type_func = {
        'append': upload_append_blob,
        'block': upload_block_blob,
        'page': upload_block_blob  # same implementation
    }
    return type_func[blob_type]()
upload_blob.__doc__ = BlockBlobService.create_blob_from_path.__doc__

def _get_service_container_type(client):
    if isinstance(client, BlockBlobService):
        return 'container'
    elif isinstance(client, FileService):
        return 'share'
    else:
        raise ValueError('Unsupported service {}'.format(type(client)))

def _get_acl(client, container_name):
    container = _get_service_container_type(client)
    return getattr(client, 'get_{}_acl'.format(container))(container_name)

def _set_acl(client, container_name, acl):
    container = _get_service_container_type(client)
    return getattr(client, 'set_{}_acl'.format(container))(container_name, acl)

def create_acl_policy(
        client, container_name, policy_name, start=None, expiry=None, permission=None):
    ''' Create a stored access policy on the containing object '''
    from azure.storage.models import AccessPolicy
    # TODO: Remove workaround once SDK issue fixed (Pivotal #120873795)
    if not (start or expiry or permission):
        raise CLIError('Must specify at least one property (permission, start or expiry) '
                       'when creating an access policy.')

    acl = _get_acl(client, container_name)
    acl[policy_name] = AccessPolicy(permission, expiry, start)
    return _set_acl(client, container_name, acl)

def get_acl_policy(client, container_name, policy_name):
    ''' Show a stored access policy on a containing object '''
    from azure.storage.models import AccessPolicy
    acl = _get_acl(client, container_name)
    return acl.get(policy_name)

def list_acl_policies(client, container_name):
    ''' List stored access policies on a containing object '''
    return _get_acl(client, container_name)

def set_acl_policy(client, container_name, policy_name, start=None, expiry=None, permission=None):
    ''' Set a stored access policy on a containing object '''
    from azure.storage.models import AccessPolicy
    if not (start or expiry or permission):
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(client, container_name)
    try:
        policy = acl[policy_name]
        policy.start = start or policy.start
        policy.expiry = expiry or policy.expiry
        policy.permission = permission or policy.permission
    except KeyError:
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(client, container_name, acl)

def delete_acl_policy(client, container_name, policy_name):
    ''' Delete a stored access policy on a containing object '''
    acl = _get_acl(client, container_name)
    del acl[policy_name]
    return _set_acl(client, container_name, acl)
