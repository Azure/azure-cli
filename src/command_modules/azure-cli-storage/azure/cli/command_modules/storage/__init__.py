from __future__ import print_function
from os import environ
from sys import stderr

from azure.storage.blob import PublicAccess, BlockBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType
from azure.mgmt.storage.operations import StorageAccountsOperations

from azure.cli.commands import (CommandTable, LongRunningOperation)
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli._locale import L

from .params import PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS, _parse_datetime

command_table = CommandTable()

# FACTORIES

def _storage_client_factory(_):
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

def _file_data_service_factory(args):
    return get_data_service_client(
        FileService,
        args.pop('account_name', None),
        args.pop('account_key', None),
        args.pop('connection_string', None))

def _blob_data_service_factory(args):
    return get_data_service_client(
        BlockBlobService,
        args.pop('account_name', None),
        args.pop('account_key', None),
        args.pop('connection_string', None))

def _cloud_storage_account_service_factory(args):
    return CloudStorageAccount(
        args.pop('account_name', None),
        args.pop('account_key', None),
        args.pop('connection_string', None))

def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        percent_done = current * 100 / total
        message += '{: >5.1f}'.format(percent_done)
        print('\b' * len(message) + message, end='', file=stderr)
        stderr.flush()

#### ACCOUNT COMMANDS #############################################################################

build_operation(
    'storage account',
    'storage_accounts',
    _storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.check_name_availability,
                              'Result', 'check-name'),
        AutoCommandDefinition(StorageAccountsOperations.delete, None),
        AutoCommandDefinition(StorageAccountsOperations.get_properties, 'StorageAccount', 'show')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'storage account', None, _cloud_storage_account_service_factory,
    [
        AutoCommandDefinition(CloudStorageAccount.generate_shared_access_signature,
                              'String', 'generate-sas')
    ],
    command_table, None, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage account list', description=L('List storage accounts.'))
@command_table.option(**PARAMETER_ALIASES['optional_resource_group_name'])
def list_accounts(args):
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    smc = _storage_client_factory({})
    group = args.get('resourcegroup')
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()
    return list(accounts)

build_operation(
    'storage account keys',
    'storage_accounts',
    _storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.list_keys, '[StorageAccountKeys]', 'list')
    ], command_table, PARAMETER_ALIASES)

key_options = ['key1', 'key2']
@command_table.command('storage account keys renew')
@command_table.description(L('Regenerate one or both keys for a storage account.'))
@command_table.option(**PARAMETER_ALIASES['resource_group_name'])
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option('--key -y', default=key_options,
                      choices=key_options, help=L('Key to renew'))
def renew_account_keys(args):
    smc = _storage_client_factory({})
    keys_to_renew = args.get('key')
    for key in keys_to_renew if isinstance(keys_to_renew, list) else [keys_to_renew]:
        result = smc.storage_accounts.regenerate_key(
            resource_group_name=args.get('resourcegroup'),
            account_name=args.get('account_name'),
            key_name=key)
    return result

@command_table.command('storage account usage')
@command_table.description(
    L('Show the current count and limit of the storage accounts under the subscription.'))
def show_account_usage(_):
    smc = _storage_client_factory({})
    return next((x for x in smc.usage.list() if x.name.value == 'StorageAccounts'), None)

@command_table.command('storage account connection-string')
@command_table.description(L('Show the connection string for a storage account.'))
@command_table.option(**PARAMETER_ALIASES['resource_group_name'])
@command_table.option(**PARAMETER_ALIASES['account_name_required'])
@command_table.option('--use-http', action='store_const', const='http', default='https',
                      help=L('use http as the default endpoint protocol'))
def show_storage_connection_string(args):
    smc = _storage_client_factory({})
    endpoint_protocol = args.get('use_http')
    storage_account = args.get('account_name')
    keys = smc.storage_accounts.list_keys(args.get('resourcegroup'), storage_account)

    connection_string = 'DefaultEndpointsProtocol={};AccountName={};AccountKey={}'.format(
        endpoint_protocol,
        storage_account,
        keys.key1) #pylint: disable=no-member
    return {'ConnectionString':connection_string}

# TODO: update this once enums are supported in commands first-class (task #115175885)
storage_account_types = {'Standard_LRS': AccountType.standard_lrs,
                         'Standard_ZRS': AccountType.standard_zrs,
                         'Standard_GRS': AccountType.standard_grs,
                         'Standard_RAGRS': AccountType.standard_ragrs,
                         'Premium_LRS': AccountType.premium_lrs}

@command_table.command('storage account create')
@command_table.description(L('Create a storage account.'))
@command_table.option(**PARAMETER_ALIASES['resource_group_name'])
@command_table.option(**PARAMETER_ALIASES['account_name_required'])
@command_table.option(**PARAMETER_ALIASES['location'])
@command_table.option('--type', choices=storage_account_types.keys(), required=True)
@command_table.option(**PARAMETER_ALIASES['tags'])
def create_account(args):
    from azure.mgmt.storage.models import StorageAccountCreateParameters
    smc = _storage_client_factory({})

    resource_group = args.get('resourcegroup')
    account_name = args.get('account_name')
    account_type = storage_account_types[args.get('type')]
    params = StorageAccountCreateParameters(args.get('location'),
                                            account_type,
                                            args.get('tags'))

    op = LongRunningOperation('Creating storage account', 'Storage account created')
    poller = smc.storage_accounts.create(resource_group, account_name, params)
    return op(poller)

@command_table.command('storage account set')
@command_table.description(L('Update storage account property (only one at a time).'))
@command_table.option(**PARAMETER_ALIASES['resource_group_name'])
@command_table.option(**PARAMETER_ALIASES['account_name_required'])
@command_table.option('--type',
                      choices=storage_account_types.keys())
@command_table.option(**PARAMETER_ALIASES['tags'])
@command_table.option('--custom-domain', help=L('the custom domain name'))
@command_table.option('--subdomain', help=L('use indirect CNAME validation'))
def set_account(args):
    from azure.mgmt.storage.models import StorageAccountUpdateParameters, CustomDomain
    smc = _storage_client_factory({})

    resource_group = args.get('resourcegroup')
    account_name = args.get('account_name')
    domain = args.get('custom_domain')
    account_type = storage_account_types[args.get('type')] if args.get('type') else None

    params = StorageAccountUpdateParameters(args.get('tags'), account_type, domain)
    return smc.storage_accounts.update(resource_group, account_name, params)

#### BLOB COMMANDS ################################################################################

# CONTAINER COMMANDS

build_operation(
    'storage container', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_containers, '[Container]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_container, None, 'delete'),
        AutoCommandDefinition(BlockBlobService.get_container_properties,
                              '[ContainerProperties]', 'show'),
        AutoCommandDefinition(BlockBlobService.create_container, None, 'create'),
        AutoCommandDefinition(BlockBlobService.generate_container_shared_access_signature,
                              'String', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container acl', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_acl, 'Something?', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_acl, 'Something?', 'get'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container metadata', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_metadata, 'Something?', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_metadata, 'Something?', 'get'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}

@command_table.command('storage container exists')
@command_table.description(L('Check if a storage container exists.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
@command_table.option('--snapshot', type=_parse_datetime,
                      help=L('UTC datetime value which specifies a snapshot'))
@command_table.option(**PARAMETER_ALIASES['timeout'])
def exists_container(args):
    bbs = _blob_data_service_factory(args)
    return str(bbs.exists(
        container_name=args.get('container_name'),
        snapshot=args.get('snapshot'),
        timeout=args.get('timeout')))

lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
    lease_duration_values['min'],
    lease_duration_values['max'],
    lease_duration_values['infinite'])

build_operation(
    'storage container lease', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_container_lease, 'String', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_container_lease, None, 'renew'),
        AutoCommandDefinition(BlockBlobService.release_container_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_container_lease, 'LeaseId', 'change'),
        AutoCommandDefinition(BlockBlobService.break_container_lease, 'Something?', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# BLOB COMMANDS

build_operation(
    'storage blob', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_blobs, '[Blob]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_blob, None, 'delete'),
        AutoCommandDefinition(BlockBlobService.generate_blob_shared_access_signature,
                                'String', 'generate-sas'),
        AutoCommandDefinition(BlockBlobService.make_blob_url, 'URL', 'url'),
        AutoCommandDefinition(BlockBlobService.snapshot_blob, 'Something?', 'snapshot')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob service-properties', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_service_properties, '[Properties]', 'get'),
        AutoCommandDefinition(BlockBlobService.set_blob_service_properties, 'Something?', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob metadata', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_metadata, 'Metadata', 'get'),
        AutoCommandDefinition(BlockBlobService.set_blob_metadata, 'Something?', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob properties', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_properties, '[Properties]', 'get'),
        AutoCommandDefinition(BlockBlobService.set_blob_properties, 'Something?', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage blob upload-block-blob')
@command_table.description(L('Upload a block blob to a container.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option(**PARAMETER_ALIASES['blob_name'])
@command_table.option('--upload-from', required=True)
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
@command_table.option('--container.public-access', default=None,
                      choices=public_access_types.keys(),
                      type=lambda x: public_access_types.get(x, ValueError))
@command_table.option('--content.type')
@command_table.option('--content.disposition')
@command_table.option('--content.encoding')
@command_table.option('--content.language')
@command_table.option('--content.md5')
@command_table.option('--content.cache-control')
def create_block_blob(args):
    from azure.storage.blob import ContentSettings
    bbs = _blob_data_service_factory(args)
    bbs.create_container(args.get('container_name'),
                         public_access=args.get('public_access'))

    return bbs.create_blob_from_path(
        container_name=args.get('container_name'),
        blob_name=args.get('blob_name'),
        file_path=args.get('upload_from'),
        progress_callback=_update_progress,
        content_settings=ContentSettings(content_type=args.get('content.type'),
                                         content_disposition=args.get('content.disposition'),
                                         content_encoding=args.get('content.encoding'),
                                         content_language=args.get('content.language'),
                                         content_md5=args.get('content.md5'),
                                         cache_control=args.get('content.cache-control'))
        )

@command_table.command('storage blob download')
@command_table.description(L('Download the specified blob.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option(**PARAMETER_ALIASES['blob_name'])
@command_table.option('--download-to', help=L('the file path to download to'), required=True)
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
def download_blob(args):
    bbs = _blob_data_service_factory(args)

    # show dot indicator of download progress (one for every 10%)
    bbs.get_blob_to_path(args.get('container_name'),
                         args.get('blob_name'),
                         args.get('download_to'),
                         progress_callback=_update_progress)

@command_table.command('storage blob exists')
@command_table.description(L('Check if a storage blob exists.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option(**PARAMETER_ALIASES['blob_name'])
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
@command_table.option('--snapshot', type=_parse_datetime,
                      help=L('UTC datetime value which specifies a snapshot'))
@command_table.option(**PARAMETER_ALIASES['timeout'])
def exists_blob(args):
    bbs = _blob_data_service_factory(args)
    return str(bbs.exists(
        blob_name=args.get('blob_name'),
        container_name=args.get('container_name'),
        snapshot=args.get('snapshot'),
        timeout=args.get('timeout')))

build_operation(
    'storage blob lease', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_blob_lease, 'String', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_blob_lease, None, 'renew'),
        AutoCommandDefinition(BlockBlobService.release_blob_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_blob_lease, 'LeaseId', 'change'),
        AutoCommandDefinition(BlockBlobService.break_blob_lease, 'Something?', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob copy', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.copy_blob, 'Something?', 'start'),
        AutoCommandDefinition(BlockBlobService.abort_copy_blob, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

#### FILE COMMANDS ################################################################################

# SHARE COMMANDS

build_operation(
    'storage share', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.list_shares, '[Share]', 'list'),
        AutoCommandDefinition(FileService.list_directories_and_files,
                              '[ShareContents]', 'contents'),
        AutoCommandDefinition(FileService.create_share, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_share, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.generate_share_shared_access_signature,
                              'Sometihng?', 'generate-sas'),
        AutoCommandDefinition(FileService.get_share_stats, 'Something?', 'stats')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_share_metadata, 'Metadata', 'get'),
        AutoCommandDefinition(FileService.set_share_metadata, None, 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share properties', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_share_properties, '[Properties]', 'get'),
        AutoCommandDefinition(FileService.set_share_properties, 'Something?', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share acl', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.set_share_acl, 'Something?', 'set'),
        AutoCommandDefinition(FileService.get_share_acl, 'Something?', 'get'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage share exists')
@command_table.description(L('Check if a file share exists.'))
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
def exist_share(args):
    fsc = _file_data_service_factory(args)
    return str(fsc.exists(share_name=args.get('share_name')))

# DIRECTORY COMMANDS

build_operation(
    'storage directory', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.create_directory, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_directory, 'Boolean', 'delete'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_directory_metadata, 'Metadata', 'get'),
        AutoCommandDefinition(FileService.set_directory_metadata, None, 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage directory exists')
@command_table.description(L('Check if a directory exists.'))
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--directory-name -d', help=L('the directory name'), required=True)
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
def exist_directory(args):
    fsc = _file_data_service_factory(args)
    return str(fsc.exists(share_name=args.get('share_name'),
                          directory_name=args.get('directory_name')))

# FILE COMMANDS

build_operation(
    'storage file', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.delete_file, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.resize_file, 'Something?', 'resize'),
        AutoCommandDefinition(FileService.make_file_url, 'URL', 'url'),
        AutoCommandDefinition(FileService.generate_file_shared_access_signature,
                              'String', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_metadata, 'Metadata', 'get'),
        AutoCommandDefinition(FileService.set_file_metadata, None, 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file properties', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_properties, '[Properties]', 'get'),
        AutoCommandDefinition(FileService.set_file_properties, 'Something?', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file service-properties', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_service_properties, '[Properties]', 'get'),
        AutoCommandDefinition(FileService.set_file_service_properties, 'Something?', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage file download')
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--file-name -f', help=L('the file name'), required=True)
@command_table.option('--local-file-name', help=L('the path to the local file'), required=True)
@command_table.option('--directory-name -d', help=L('the directory name'))
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
def storage_file_download(args):
    fsc = _file_data_service_factory(args)
    fsc.get_file_to_path(args.get('share_name'),
                         args.get('directory_name'),
                         args.get('file_name'),
                         args.get('local_file_name'),
                         progress_callback=_update_progress)

@command_table.command('storage file exists')
@command_table.description(L('Check if a file exists.'))
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--file-name -f', help=L('the file name to check'), required=True)
@command_table.option('--directory-name -d', help=L('subdirectory path to the file'))
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
def exist_file(args):
    fsc = _file_data_service_factory(args)
    return str(fsc.exists(share_name=args.get('share_name'),
                          directory_name=args.get('directory_name'),
                          file_name=args.get('file_name')))

@command_table.command('storage file upload')
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--file-name -f', help=L('the destination file name'), required=True)
@command_table.option('--local-file-name', help=L('the file name to upload'), required=True)
@command_table.option('--directory-name -d', help=L('the destination directory to upload to'))
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
@command_table.option(**PARAMETER_ALIASES['connection_string'])
def storage_file_upload(args):
    fsc = _file_data_service_factory(args)
    fsc.create_file_from_path(args.get('share_name'),
                              args.get('directory_name'),
                              args.get('file_name'),
                              args.get('local_file_name'),
                              progress_callback=_update_progress)

build_operation(
    'storage file copy', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.copy_file, 'Something?', 'start'),
        AutoCommandDefinition(FileService.abort_copy_file, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)
