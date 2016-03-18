from os import environ

from azure.storage.blob import PublicAccess
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.operations import StorageAccountsOperations

from .._argparse import IncorrectUsageError
from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client, get_data_service_client
from ..commands._auto_command import build_operation
from .._locale import L

def _storage_client_factory():
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

# ACCOUNT COMMANDS

build_operation('storage account',
                'storage_accounts',
                _storage_client_factory,
                [
                    (StorageAccountsOperations.check_name_availability, 'Result'),
                    (StorageAccountsOperations.delete, None),
                    (StorageAccountsOperations.get_properties, 'StorageAccount'),
                    (StorageAccountsOperations.list_keys, '[StorageAccountKeys]')
                ])

@command('storage account list')
@description(L('List storage accounts.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'))
def list_accounts(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    smc = _storage_client_factory()
    group = args.get('resource-group')
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()
    return list(accounts)

# TODO: update this once enums are supported in commands first-class (task #115175885)
key_values = ['key1', 'key2']
key_values_string = ' | '.join(key_values)

@command('storage account renew-keys')
@description(L('Regenerate one or both keys for a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'), required=True)
@option('--key -y <key>', L('renew a specific key. Values %s' % key_values_string))
def renew_account_keys(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()

    key_name = args.get('key')
    resource_group = args.get('resource-group')
    account_name = args.get('account-name')

    if not key_name:
        for key in key_values:
            result = smc.storage_accounts.regenerate_key(
                resource_group_name=resource_group,
                account_name=account_name,
                key_name=key)
    elif key_name in key_values:
        result = smc.storage_accounts.regenerate_key(
            resource_group_name=resource_group,
            account_name=account_name,
            key_name=key_name)
    else:
        raise ValueError(L('Unrecognized key value: %s' % key_name))
    return result

@command('storage account usage show')
@description(L('Show the current count and limit of the storage accounts under the subscription.'))
def show_account_usage(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()
    for item in smc.usage.list():
        if item.name.value == 'StorageAccounts':
            return item
    return None

@command('storage account connectionstring show')
@description(L('Show the connection string for a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--use-http', L('use http as the default endpoint protocol'))
def show_storage_connection_string(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()

    endpoint_protocol = 'http' if args.get('use-http') is not None else 'https'
    storage_account = _resolve_storage_account(args)
    keys = smc.storage_accounts.list_keys(args.get('resource-group'), storage_account)

    connection_string = 'DefaultEndpointsProtocol=%s;AccountName=%s;AccountKey=%s' % (
        endpoint_protocol,
        storage_account,
        keys.key1) #pylint: disable=no-member

    return {'ConnectionString':connection_string}

# CONTAINER COMMANDS

@command('storage container create')
@description(L('Create a storage container.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
# TODO: Add permission parameter
def create_container(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  _resolve_storage_account(args),
                                  _resolve_storage_account_key(args),
                                  _resolve_connection_string(args))
    if not bbs.create_container(args.get('container-name')):
        raise RuntimeError(L('Container creation failed.'))

@command('storage container delete')
@description(L('Delete a storage container.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--quiet', L('supress delete confirmation prompt'))
def delete_container(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  _resolve_storage_account(args),
                                  _resolve_storage_account_key(args),
                                  _resolve_connection_string(args))
    container_name = args.get('container-name')
    prompt_for_delete = args.get('quiet') is None

    if prompt_for_delete:
        ans = input('Really delete %s? [Y/n] ' % container_name)
        if not ans or ans[0].lower() != 'y':
            return 0

    if not bbs.delete_container(container_name):
        raise RuntimeError(L('Container deletion failed.'))

@command('storage container list')
@description(L('List storage containers.'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--prefix -p <prefix>', L('prefix of container names to return'))
def list_containers(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  _resolve_storage_account(args),
                                  _resolve_storage_account_key(args),
                                  _resolve_connection_string(args))
    results = bbs.list_containers(args.get('prefix'))
    return results

@command('storage container show')
@description(L('Show details of a storage container'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def show_container(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  _resolve_storage_account(args),
                                  _resolve_storage_account_key(args),
                                  _resolve_connection_string(args))
    result = bbs.get_container_properties(args.get('container-name'))
    return result

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}
public_access_string = ' | '.join(public_access_types)

@command('storage blob blockblob create')
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--blob-name -bn <name>', required=True)
@option('--upload-from -uf <file>', required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--container.public-access -cpa <accessType>', 'Values: {}'.format(public_access_string))
@option('--content.type -cst <type>')
@option('--content.disposition -csd <disposition>')
@option('--content.encoding -cse <encoding>')
@option('--content.language -csl <language>')
@option('--content.md5 -csm <md5>')
@option('--content.cache-control -cscc <cacheControl>')
def create_block_blob(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings

    block_blob_service = get_data_service_client(BlockBlobService,
                                                 _resolve_storage_account(args),
                                                 _resolve_storage_account_key(args),
                                                 _resolve_connection_string(args))

    try:
        public_access = public_access_types[args.get('container.public-access')] \
                                            if args.get('container.public-access') \
                                            else None
    except KeyError:
        raise IncorrectUsageError(L('container.public-access must be: {}'
                                    .format(public_access_string)))

    block_blob_service.create_container(args.get('container-name'), public_access=public_access)

    return block_blob_service.create_blob_from_path(
        args.get('container-name'),
        args.get('blob-name'),
        args.get('upload-from'),
        content_settings=ContentSettings(content_type=args.get('content.type'),
                                         content_disposition=args.get('content.disposition'),
                                         content_encoding=args.get('content.encoding'),
                                         content_language=args.get('content.language'),
                                         content_md5=args.get('content.md5'),
                                         cache_control=args.get('content.cache-control'))
        )

@command('storage blob list')
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def list_blobs(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings

    block_blob_service = get_data_service_client(BlockBlobService,
                                                 _resolve_storage_account(args),
                                                 _resolve_storage_account_key(args),
                                                 _resolve_connection_string(args))

    blobs = block_blob_service.list_blobs(args.get('container-name'))
    return blobs.items

@command('storage file create')
@option('--share-name -sn <setting>', required=True)
@option('--file-name -fn <setting>', required=True)
@option('--local-file-name -lfn <setting>', required=True)
@option('--directory-name -dn <setting>')
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
def storage_file_create(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.file import FileService

    file_service = get_data_service_client(FileService,
                                           _resolve_storage_account(args),
                                           _resolve_storage_account_key(args),
                                           _resolve_connection_string(args))

    file_service.create_file_from_path(args.get('share-name'),
                                       args.get('directory-name'),
                                       args.get('file-name'),
                                       args.get('local-file-name'))

# HELPER METHODS

def _resolve_storage_account(args):
    return args.get('account-name') or environ.get('AZURE_STORAGE_ACCOUNT')

def _resolve_storage_account_key(args):
    return args.get('account-key') or environ.get('AZURE_STORAGE_ACCESS_KEY')

def _resolve_connection_string(args):
    return args.get('connection-string') or environ.get('AZURE_STORAGE_CONNECTION_STRING')
