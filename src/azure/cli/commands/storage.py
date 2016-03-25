from __future__ import print_function
from os import environ
from sys import stderr
from six.moves import input #pylint: disable=redefined-builtin

from azure.storage.blob import PublicAccess
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.operations import StorageAccountsOperations

from ..parser import IncorrectUsageError
from ..commands import CommandTable, COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from ._command_creation import get_mgmt_service_client, get_data_service_client
from ..commands._auto_command import build_operation
from .._locale import L

command_table = CommandTable()

def extend_parameter(parameter_metadata, **kwargs):
    modified_parameter_metadata = parameter_metadata.copy()
    modified_parameter_metadata.update(kwargs)
    return modified_parameter_metadata

COMMON_PARAMETERS = GLOBAL_COMMON_PARAMETERS.copy()
COMMON_PARAMETERS.update({
    'account-name': {
       'name': '--account-name -n', 
       'help': L('the storage account name'), 
       'required': not environ.get('AZURE_STORAGE_ACCOUNT'),
       'default': environ.get('AZURE_STORAGE_ACCOUNT')
    },
    'optional_resource_group_name': extend_parameter(GLOBAL_COMMON_PARAMETERS['resource_group_name'], required=False),
    'account_key': {
       'name': '--account-key -k', 
       'help': L('the storage account key'),
       'required': not environ.get('AZURE_STORAGE_ACCESS_KEY'),
       'default': environ.get('AZURE_STORAGE_ACCESS_KEY')
    },
    'blob-name': {
        'name': '--blob-name -bn',
        'help': L('the name of the blob'), 
        'required': True
    },
    'container-name': {
        'name': '--container-name -c',
        'required': True
    }, 
    'connection-string': {
        'name': '--connection-string -t',
        'help': L('the storage connection string'),
        'required': not environ.get('AZURE_STORAGE_CONNECTION_STRING'),
        'default': environ.get('AZURE_STORAGE_CONNECTION_STRING')
    }
})

def get_command_table():
    return command_table

def _storage_client_factory():
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

# ACCOUNT COMMANDS

build_operation(command_table,
                'storage account',
                'storage_accounts',
                _storage_client_factory,
                [
                    (StorageAccountsOperations.check_name_availability, 'Result'),
                    (StorageAccountsOperations.delete, None),
                    (StorageAccountsOperations.get_properties, 'StorageAccount'),
                    (StorageAccountsOperations.list_keys, '[StorageAccountKeys]')
                ])

@command_table.command('storage account list', description=L('List storage accounts.'))
@command_table.option(**COMMON_PARAMETERS['optional_resource_group_name'])
def list_accounts(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    smc = _storage_client_factory()
    group = args.get('resource_group_name')
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()
    return list(accounts)

@command_table.command('storage account renew-keys')
@command_table.description(L('Regenerate one or both keys for a storage account.'))
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option('--key -y', default=['key1', 'key2'], 
                      choices=['key1', 'key2'], help=L('Key to renew'))
def renew_account_keys(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()
    for key in args.get('key'):
        result = smc.storage_accounts.regenerate_key(
            resource_group_name=args.get('resource_group_name'),
            account_name=args.get('account-name'),
            key_name=key)

    return result

@command_table.command('storage account usage')
@command_table.description(
    L('Show the current count and limit of the storage accounts under the subscription.'))
def show_account_usage(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()
    return next((x for x in smc.usage.list() if x.name.value == 'StorageAccounts'), None)

@command_table.command('storage account connection-string')
@command_table.description(L('Show the connection string for a storage account.'))
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option('--use-http', action='store_const', const='http', default='https',
                      help=L('use http as the default endpoint protocol'))
def show_storage_connection_string(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()

    endpoint_protocol = args.get('use-http') 
    storage_account = args.get('account-name')
    keys = smc.storage_accounts.list_keys(args.get('resource_group_name'), storage_account)

    connection_string = 'DefaultEndpointsProtocol={};AccountName={};AccountKey={}'.format(
        endpoint_protocol,
        storage_account,
        keys.key1) #pylint: disable=no-member

    return {'ConnectionString':connection_string}

# CONTAINER COMMANDS

public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}
@command_table.command('storage container create')
@command_table.description(L('Create a storage container.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection-string'])
@command_table.option('--public-access -p', default=None, choices=public_access_types.keys(), 
                      type=lambda x: public_access_types[x])
def create_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    public_access = args.get('public-access')

    if not bbs.create_container(args.get('container-name'), public_access=public_access):
        raise RuntimeError(L('Container creation failed.'))

@command_table.command('storage container delete')
@command_table.description(L('Delete a storage container.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection-string'])
@command_table.option('--force -f', help=L('supress delete confirmation prompt'))
def delete_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    container_name = args.get('container-name')
    prompt_for_delete = args.get('force') is None

    if prompt_for_delete:
        ans = input('Really delete {}? [Y/n] '.format(container_name))
        if not ans or ans[0].lower() != 'y':
            return 0

    if not bbs.delete_container(container_name):
        raise RuntimeError(L('Container deletion failed.'))

@command_table.command('storage container list')
@command_table.description(L('List storage containers.'))
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection-string'])
@command_table.option('--prefix -p', help=L('container name prefix to filter by'))
def list_containers(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    results = bbs.list_containers(args.get('prefix'))
    return results

@command_table.command('storage container show')
@command_table.description(L('Show details of a storage container'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection-string'])
def show_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    result = bbs.get_container_properties(args.get('container-name'))
    return result

# BLOB COMMANDS
# TODO: Evaluate for removing hand-authored commands in favor of auto-commands (task ##115068835)

@command_table.command('storage blob upload-block-blob')
@command_table.description(L('Upload a block blob to a container.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['blob-name'])
@command_table.option('--upload-from -uf', required=True)
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection-string'])
@command_table.option('--container.public-access -cpa', default=None, choices=public_access_types.keys(), 
                      type=lambda x: public_access_types[x])
@command_table.option('--content.type -cst')
@command_table.option('--content.disposition -csd')
@command_table.option('--content.encoding -cse')
@command_table.option('--content.language -csl')
@command_table.option('--content.md5 -csm')
@command_table.option('--content.cache-control -cscc')
def create_block_blob(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import ContentSettings
    bbs = _get_blob_service_client(args)
    public_access = args.get('container.public-access')
    bbs.create_container(args.get('container-name'), public_access=public_access)

    return bbs.create_blob_from_path(
        args.get('container-name'),
        args.get('blob-name'),
        args.get('upload-from'),
        progress_callback=_update_progress,
        content_settings=ContentSettings(content_type=args.get('content.type'),
                                         content_disposition=args.get('content.disposition'),
                                         content_encoding=args.get('content.encoding'),
                                         content_language=args.get('content.language'),
                                         content_md5=args.get('content.md5'),
                                         cache_control=args.get('content.cache-control'))
        )

@command_table.command('storage blob list')
@command_table.description(L('List all blobs in a container.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection-string'])
@command_table.option('--prefix -p', help=L('blob name prefix to filter by'))
def list_blobs(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    blobs = bbs.list_blobs(args.get('container-name'),
                           prefix=args.get('prefix'))
    return list(blobs.items)

@command_table.command('storage blob delete')
@command_table.description(L('Delete a blob from a container.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['blob-name'])
def delete_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.delete_blob(args.get('container-name'), args.get('blob-name'))

@command_table.command('storage blob show')
@command_table.description(L('Show properties of the specified blob.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['blob-name'])
def show_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.get_blob_properties(args.get('container-name'), args.get('blob-name'))

@command_table.command('storage blob download')
@command_table.description(L('Download the specified blob.'))
@command_table.option(**COMMON_PARAMETERS['container-name'])
@command_table.option(**COMMON_PARAMETERS['blob-name'])
@command_table.option('--download-to -dt', help=L('the file path to download to'), required=True)
def download_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)

    # show dot indicator of download progress (one for every 10%)
    bbs.get_blob_to_path(args.get('container-name'),
                         args.get('blob-name'),
                         args.get('download-to'),
                         progress_callback=_update_progress)

# FILE COMMANDS

@command_table.command('storage file create')
@command_table.option('--share-name -sn', required=True)
@command_table.option('--file-name -fn', required=True)
@command_table.option('--local-file-name -lfn', required=True)
@command_table.option('--directory-name -dn')
@command_table.option(**COMMON_PARAMETERS['account-name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['container-name'])
def storage_file_create(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    fsc.create_file_from_path(args.get('share-name'),
                              args.get('directory-name'),
                              args.get('file-name'),
                              args.get('local-file-name'))

# HELPER METHODS

def _get_blob_service_client(args):
    from azure.storage.blob import BlockBlobService
    return get_data_service_client(BlockBlobService,
                                   args['storage-account'],
                                   args['storage-account-key'],
                                   args['connection-string'])

def _get_file_service_client(args):
    from azure.storage.file import FileService
    return get_data_service_client(FileService,
                                   args['storage-account'],
                                   args['storage-account-key'],
                                   args['connection-string'])

def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        num_format = 'xxx.x'
        num_decimals = len(num_format.split('.', maxsplit=1)[1]) if '.' in num_format else 0
        format_string = '{:.%sf}' % num_decimals
        percent_done = format_string.format(current * 100 / total)
        padding = len(num_format) - len(percent_done)
        message += (' ' * padding) + percent_done
        print('\b' * len(message) + message, end='', file=stderr, flush=True)
