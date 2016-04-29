from __future__ import print_function
import os
from sys import stderr

from azure.storage.blob import PublicAccess, BlockBlobService, AppendBlobService, PageBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType
from azure.mgmt.storage.operations import StorageAccountsOperations

from azure.cli.commands import (CommandTable,
                                LongRunningOperation,
                                RESOURCE_GROUP_ARG_NAME)
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli.commands._validators import validate_key_value_pairs
from azure.cli._locale import L

from ._params import PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS

command_table = CommandTable()

# FACTORIES

def _storage_client_factory(_):
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

def _file_data_service_factory(args):
    return get_data_service_client(
        FileService,
        args.pop('account_name', None),
        args.pop('account_key', None),
        connection_string=args.pop('connection_string', None),
        sas_token=args.pop('sas_token', None))

def _blob_data_service_factory(args):
    blob_type = args.get('type')
    blob_service = blob_types.get(blob_type, BlockBlobService)
    return get_data_service_client(
        blob_service,
        args.pop('account_name', None),
        args.pop('account_key', None),
        connection_string=args.pop('connection_string', None),
        sas_token=args.pop('sas_token', None))

def _cloud_storage_account_service_factory(args):
    account_name = args.pop('account_name', None)
    account_key = args.pop('account_key', None)
    sas_token = args.pop('sas_token', None)
    connection_string = args.pop('connection_string', None)
    if connection_string:
        # CloudStorageAccount doesn't accept connection string directly, so we must parse
        # out the account name and key manually
        conn_dict = validate_key_value_pairs(connection_string)
        account_name = conn_dict['AccountName']
        account_key = conn_dict['AccountKey']
    return CloudStorageAccount(account_name, account_key, sas_token)

def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        percent_done = current * 100 / total
        message += '{: >5.1f}'.format(percent_done)
        print('\b' * len(message) + message, end='', file=stderr)
        stderr.flush()

#### ACCOUNT COMMANDS #############################################################################

build_operation(
    'storage account', 'storage_accounts', _storage_client_factory,
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
                              'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage account list', description=L('List storage accounts.'))
@command_table.option(**PARAMETER_ALIASES['optional_resource_group_name'])
def list_accounts(args):
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    smc = _storage_client_factory({})
    group = args.get(RESOURCE_GROUP_ARG_NAME)
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()
    return list(accounts)

build_operation(
    'storage account keys', 'storage_accounts', _storage_client_factory,
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
            resource_group_name=args.get(RESOURCE_GROUP_ARG_NAME),
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
    keys = smc.storage_accounts.list_keys(args.get(RESOURCE_GROUP_ARG_NAME),
                                          storage_account)

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

    resource_group = args.get(RESOURCE_GROUP_ARG_NAME)
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

    resource_group = args.get(RESOURCE_GROUP_ARG_NAME)
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
        AutoCommandDefinition(BlockBlobService.delete_container, 'Bool', 'delete'),
        AutoCommandDefinition(BlockBlobService.get_container_properties,
                              'ContainerProperties', 'show'),
        AutoCommandDefinition(BlockBlobService.create_container, 'Bool', 'create'),
        AutoCommandDefinition(BlockBlobService.generate_container_shared_access_signature,
                              'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container acl', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_acl, 'StoredAccessPolicy', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_acl, '[StoredAccessPolicy]', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container metadata', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_metadata, 'Properties', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_metadata, 'Metadata', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}

@command_table.command('storage container exists')
@command_table.description(L('Check if a storage container exists.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
@command_table.option('--snapshot', help=L('UTC datetime value which specifies a snapshot'))
@command_table.option(**PARAMETER_ALIASES['timeout'])
def exists_container(args):
    bbs = _blob_data_service_factory(args)
    return bbs.exists(
        container_name=args.get('container_name'),
        snapshot=args.get('snapshot'),
        timeout=args.get('timeout'))

lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
    lease_duration_values['min'],
    lease_duration_values['max'],
    lease_duration_values['infinite'])

build_operation(
    'storage container lease', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_container_lease, 'LeaseID', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_container_lease, 'LeaseID', 'renew'),
        AutoCommandDefinition(BlockBlobService.release_container_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_container_lease, None, 'change'),
        AutoCommandDefinition(BlockBlobService.break_container_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# BLOB COMMANDS

build_operation(
    'storage blob', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_blobs, '[Blob]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_blob, None, 'delete'),
        AutoCommandDefinition(BlockBlobService.generate_blob_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(BlockBlobService.make_blob_url, 'URL', 'url'),
        AutoCommandDefinition(BlockBlobService.snapshot_blob, 'SnapshotProperties', 'snapshot'),
        AutoCommandDefinition(BlockBlobService.get_blob_properties, 'Properties', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_properties, 'Propeties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob service-properties', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_service_properties,
                              '[ServiceProperties]', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_service_properties,
                              'ServiceProperties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob metadata', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

blob_types = {
    'block': BlockBlobService,
    'page': PageBlobService,
    'append': AppendBlobService
}
blob_types_str = ' '.join(blob_types.keys())

@command_table.command('storage blob upload')
@command_table.description(L('Upload a blob to a container.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option(**PARAMETER_ALIASES['blob_name'])
@command_table.option('--type', required=True, choices=blob_types.keys(),
                      help=L('type of blob to upload ({})'.format(blob_types_str)))
@command_table.option('--upload-from', required=True,
                      help=L('local path to upload from'))
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
@command_table.option('--container.public-access', default=None,
                      choices=public_access_types.keys(),
                      type=lambda x: public_access_types.get(x, ValueError))
@command_table.option('--content.type')
@command_table.option('--content.disposition')
@command_table.option('--content.encoding')
@command_table.option('--content.language')
@command_table.option('--content.md5')
@command_table.option('--content.cache-control')
def upload_blob(args):
    from azure.storage.blob import ContentSettings
    bds = _blob_data_service_factory(args)
    blob_type = args.get('type')
    container_name = args.get('container_name')
    blob_name = args.get('blob_name')
    file_path = args.get('upload_from')
    content_settings = ContentSettings(
        content_type=args.get('content.type'),
        content_disposition=args.get('content.disposition'),
        content_encoding=args.get('content.encoding'),
        content_language=args.get('content.language'),
        content_md5=args.get('content.md5'),
        cache_control=args.get('content.cache-control')
    )

    def upload_append_blob():
        if not bds.exists(container_name, blob_name):
            bds.create_blob(
                container_name=container_name,
                blob_name=blob_name,
                content_settings=content_settings)
        return bds.append_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=_update_progress
        )

    def upload_block_blob():
        return bds.create_blob_from_path(
            container_name=container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=_update_progress,
            content_settings=content_settings
        )

    type_func = {
        'append': upload_append_blob,
        'block': upload_block_blob,
        'page': upload_block_blob  # same implementation
    }
    return type_func[blob_type]()

@command_table.command('storage blob download')
@command_table.description(L('Download the specified blob.'))
@command_table.option(**PARAMETER_ALIASES['container_name'])
@command_table.option(**PARAMETER_ALIASES['blob_name'])
@command_table.option('--download-to', help=L('the file path to download to'), required=True)
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
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
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
@command_table.option('--snapshot', help=L('UTC datetime value which specifies a snapshot'))
@command_table.option(**PARAMETER_ALIASES['timeout'])
def exists_blob(args):
    bbs = _blob_data_service_factory(args)
    return bbs.exists(
        blob_name=args.get('blob_name'),
        container_name=args.get('container_name'),
        snapshot=args.get('snapshot'),
        timeout=args.get('timeout'))

build_operation(
    'storage blob lease', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_blob_lease, 'LeaseID', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_blob_lease, 'LeaseID', 'renew'),
        AutoCommandDefinition(BlockBlobService.release_blob_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_blob_lease, None, 'change'),
        AutoCommandDefinition(BlockBlobService.break_blob_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob copy', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.copy_blob, 'CopyOperationProperties', 'start'),
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
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(FileService.get_share_stats, 'ShareStats', 'stats'),
        AutoCommandDefinition(FileService.get_share_properties, 'Properties', 'show'),
        AutoCommandDefinition(FileService.set_share_properties, 'Properties', 'set')

    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_share_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_share_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share acl', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.set_share_acl, '[StoredAccessPolicy]', 'set'),
        AutoCommandDefinition(FileService.get_share_acl, 'StoredAccessPolicy', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage share exists')
@command_table.description(L('Check if a file share exists.'))
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
def exist_share(args):
    fsc = _file_data_service_factory(args)
    return fsc.exists(share_name=args.get('share_name'))

# DIRECTORY COMMANDS

build_operation(
    'storage directory', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.create_directory, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_directory, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.get_directory_properties, 'Properties', 'show')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_directory_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_directory_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage directory exists')
@command_table.description(L('Check if a directory exists.'))
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--directory-name -d', help=L('the directory name'), required=True)
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
def exist_directory(args):
    fsc = _file_data_service_factory(args)
    return fsc.exists(share_name=args.get('share_name'),
                      directory_name=args.get('directory_name'))

# FILE COMMANDS

FILE_PARAM_ALIASES = PARAMETER_ALIASES.copy()
FILE_PARAM_ALIASES.update({
    'directory_name': {
        'name': '--directory-name -d',
        'required': False
    }
})

build_operation(
    'storage file', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.delete_file, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.resize_file, 'Result', 'resize'),
        AutoCommandDefinition(FileService.make_file_url, 'URL', 'url'),
        AutoCommandDefinition(FileService.generate_file_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(FileService.get_file_properties, 'Properties', 'show'),
        AutoCommandDefinition(FileService.set_file_properties, 'Properties', 'set')
    ], command_table, FILE_PARAM_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_file_metadata, 'Metadata', 'set')
    ], command_table, FILE_PARAM_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file service-properties', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_service_properties, 'ServiceProperties', 'show'),
        AutoCommandDefinition(FileService.set_file_service_properties, 'ServiceProperties', 'set')
    ], command_table, FILE_PARAM_ALIASES, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage file download')
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--file-name -f', help=L('the file name'), required=True)
@command_table.option('--local-file-name', help=L('the path to the local file'), required=True)
@command_table.option('--directory-name -d', help=L('the directory name'))
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
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
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
def exist_file(args):
    fsc = _file_data_service_factory(args)
    return fsc.exists(share_name=args.get('share_name'),
                      directory_name=args.get('directory_name'),
                      file_name=args.get('file_name'))

@command_table.command('storage file upload')
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--file-name -f', help=L('the destination file name'), required=True)
@command_table.option('--local-file-name', help=L('the file name to upload'), required=True)
@command_table.option('--directory-name -d', help=L('the destination directory to upload to'))
@command_table.option_set(STORAGE_DATA_CLIENT_ARGS)
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
        AutoCommandDefinition(FileService.copy_file, 'CopyOperationPropeties', 'start'),
        AutoCommandDefinition(FileService.abort_copy_file, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)
