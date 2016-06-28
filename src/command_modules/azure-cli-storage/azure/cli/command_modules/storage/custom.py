 # pylint: disable=no-self-use,too-many-arguments

from __future__ import print_function
from sys import stderr

from azure.cli.command_modules.storage._factory import storage_client_factory
from azure.cli._util import CLIError
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService

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

def renew_storage_account_keys(resource_group_name, account_name, key=None):
    ''' Regenerate one or both keys for a storage account.
    :param str key:Key to renew.'''
    from azure.cli.command_modules.storage._params import storage_account_key_options
    scf = storage_client_factory()
    for k in [storage_account_key_options[key]] if key \
        else storage_account_key_options.values():
        result = scf.storage_accounts.regenerate_key(
            resource_group_name=resource_group_name,
            account_name=account_name,
            key_name=k)
    return result

def show_storage_account_usage():
    ''' Show the current count and limit of the storage accounts under the subscription. '''
    scf = storage_client_factory()
    return next((x for x in scf.usage.list().value if x.name.value == 'StorageAccounts'), None) #pylint: disable=no-member

def show_storage_account_connection_string(resource_group_name, account_name, use_http='https'):
    ''' Show the connection string for a storage account.
    :param str use_http:use http as the default endpoint protocol '''
    scf = storage_client_factory()
    keys = scf.storage_accounts.list_keys(resource_group_name, account_name).keys #pylint: disable=no-member
    connection_string = 'DefaultEndpointsProtocol={};AccountName={};AccountKey={}'.format(
        use_http,
        account_name,
        keys[0].value) #pylint: disable=no-member
    return {'ConnectionString':connection_string}

def create_storage_account(resource_group_name, account_name, location, account_type, tags=None):
    ''' Create a storage account. '''
    from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku
    scf = storage_client_factory()
    # TODO Add the other new params from rc5
    # https://github.com/Azure/azure-sdk-for-python/blob/v2.0.0rc5/
    # azure-mgmt-storage/azure/mgmt/storage/models/storage_account_create_parameters.py
    # accountType is now called sku.name also.
    params = StorageAccountCreateParameters(Sku(account_type), 'Storage', location, tags)
    return scf.storage_accounts.create(resource_group_name, account_name, params)

def set_storage_account_properties(
        resource_group_name, account_name, account_type=None, tags='', custom_domain=None):
    ''' Update storage account property (only one at a time).
    :param str custom_domain:the custom domain name
    '''
    from azure.mgmt.storage.models import StorageAccountUpdateParameters, CustomDomain, Sku
    scf = storage_client_factory()
    # TODO Add the new params encryption and access_tier after rc5 update
    sku = Sku(account_type) if account_type else None
    params = StorageAccountUpdateParameters(sku=sku, tags=tags, custom_domain=custom_domain)
    return scf.storage_accounts.update(resource_group_name, account_name, params)

def container_exists(client, container_name, snapshot=None, timeout=None):
    '''Check if a storage container exists.
    :param str snapshot:UTC datetime value which specifies a snapshot
    '''
    return client.exists(
        container_name=container_name,
        snapshot=snapshot,
        timeout=timeout)

def upload_blob(
        client, container_name, blob_name, blob_type, upload_from,
        content_type=None, content_disposition=None,
        content_encoding=None, content_language=None, content_md5=None,
        content_cache_control=None):
    '''Upload a blob to a container.
    :param str blob_type:type of blob to upload
    :param str upload_from:local path to upload from
    '''
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
                content_settings=content_settings)
        return client.append_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=upload_from,
            progress_callback=_update_progress
        )

    def upload_block_blob():
        return client.create_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=upload_from,
            progress_callback=_update_progress,
            content_settings=content_settings
        )

    type_func = {
        'append': upload_append_blob,
        'block': upload_block_blob,
        'page': upload_block_blob  # same implementation
    }
    return type_func[blob_type]()

def download_blob(client, container_name, blob_name, download_to):
    ''' Download the specified blob.
    :param str download_to:the file path to download to
    '''
    client.get_blob_to_path(container_name, blob_name, download_to,
                            progress_callback=_update_progress)

def blob_exists(client, container_name, blob_name, snapshot=None, timeout=None):
    ''' Check if a storage blob exists. '''
    return client.exists(
        blob_name=blob_name,
        container_name=container_name,
        snapshot=snapshot,
        timeout=timeout)

def share_exists(client, share_name):
    ''' Check if a file share exists.'''
    return client.exists(share_name=share_name)

def dir_exists(client, share_name, directory_name):
    ''' Check if a share directory exists.'''
    return client.exists(share_name=share_name, directory_name=directory_name)

def download_file(client, share_name, file_name, local_file_name, directory_name=None):
    ''' Download a file from a file share.
    :param str file_name:the file name
    :param str local_file_name:the path to the local file to download to'''
    client.get_file_to_path(share_name, directory_name, file_name, local_file_name,
                            progress_callback=_update_progress)

def file_exists(client, share_name, file_name, directory_name=None):
    ''' Check if a file exists at a specified path.
    :param str file_name:the file name to check
    :param str directory_name:subdirectory path to the file
    '''
    return client.exists(share_name=share_name, directory_name=directory_name, file_name=file_name)

def upload_file(client, share_name, file_name, local_file_name, directory_name=None):
    ''' Upload a file to a file share path.
    :param str file_name:the destination file name
    :param str local_file_name:the path and file name to upload
    :param str directory_name:the destination directory to upload to'''
    client.create_file_from_path(share_name, directory_name, file_name, local_file_name,
                                 progress_callback=_update_progress)

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
    return list(_get_acl(client, container_name))

def set_acl_policy(client, container_name, policy_name, start=None, expiry=None, permission=None):
    ''' Set a stored access policy on a containing object '''
    from azure.storage.models import AccessPolicy
    if not (start or expiry or permission):
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(client, container_name)
    try:
        acl[policy_name] = AccessPolicy(permission, expiry, start)
    except KeyError:
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(client, container_name, acl)

def delete_acl_policy(client, container_name, policy_name):
    ''' Delete a stored access policy on a containing object '''
    acl = _get_acl(client, container_name)
    del acl[policy_name]
    return _set_acl(client, container_name, acl)
