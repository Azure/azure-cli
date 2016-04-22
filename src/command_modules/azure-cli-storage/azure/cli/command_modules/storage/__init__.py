from __future__ import print_function
from datetime import datetime
from os import environ
from sys import stderr

from azure.storage.blob import PublicAccess, BlockBlobService
from azure.storage.file import FileService
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType
from azure.mgmt.storage.operations import StorageAccountsOperations

from azure.cli.commands import (CommandTable, LongRunningOperation,
                                COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS)
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli._locale import L

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

# HELPER METHODS

def extend_parameter(parameter_metadata, **kwargs):
    modified_parameter_metadata = parameter_metadata.copy()
    modified_parameter_metadata.update(kwargs)
    return modified_parameter_metadata

def _parse_datetime(string):
    date_format = '%Y-%m-%d_%H:%M:%S'
    return datetime.strptime(string, date_format)

def _parse_key_value_pairs(string):
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=') for x in kv_list)
    return result

def _parse_tags(string):
    result = None
    if string:
        result = _parse_key_value_pairs(string)
        s_list = [x for x in string.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result

def _update_progress(current, total):
    if total:
        message = 'Percent complete: %'
        percent_done = current * 100 / total
        message += '{: >5.1f}'.format(percent_done)
        print('\b' * len(message) + message, end='', file=stderr)
        stderr.flush()
        if current == total:
            print('', file=stderr)

COMMON_PARAMETERS = GLOBAL_COMMON_PARAMETERS.copy()
COMMON_PARAMETERS.update({
    'account_key': {
        'name': '--account-key -k',
        'help': L('the storage account key'),
        # While account key *may* actually be required if the environment variable hasn't been
        # specified, it is only required unless the connection string has been specified
        'required': False,
        'default': environ.get('AZURE_STORAGE_ACCESS_KEY')
    },
    'account_name': {
        'name': '--account-name -n',
        'help': L('the storage account name'),
        # While account name *may* actually be required if the environment variable hasn't been
        # specified, it is only required unless the connection string has been specified
        'required': False,
        'default': environ.get('AZURE_STORAGE_ACCOUNT')
    },
    'account_name_required': {
        # this is used only to obtain the connection string. Thus, the env variable default
        # does not apply and this is a required parameter
        'name': '--account-name -n',
        'help': L('the storage account name'),
        'required': True
    },
    'blob_name': {
        'name': '--blob-name -b',
        'help': L('the name of the blob'),
        'required': True
    },
    'container_name': {
        'name': '--container-name -c',
        'required': True
    },
    'connection_string': {
        'name': '--connection-string',
        'help': L('the storage connection string'),
        # You can either specify connection string or name/key. There is no convenient way
        # to express this kind of relationship in argparse...
        # TODO: Move to exclusive group
        'required': False,
        'default': environ.get('AZURE_STORAGE_CONNECTION_STRING')
    },
    'if_modified_since': {
        'name': '--if-modified-since',
        'help': L('alter only if modified since supplied UTC datetime ("Y-m-d_H:M:S")'),
        'type': _parse_datetime,
        'required': False,
    },
    'if_unmodified_since': {
        'name': '--if-unmodified-since',
        'help': L('alter only if unmodified since supplied UTC datetime ("Y-m-d_H:M:S")'),
        'type': _parse_datetime,
        'required': False,
    },
    'metadata': {
        'name': '--metadata',
        'metavar': 'METADATA',
        'type': _parse_key_value_pairs,
        'help': L('metadata in "a=b;c=d" format')
    },
    'optional_resource_group_name':
        extend_parameter(GLOBAL_COMMON_PARAMETERS['resource_group_name'], required=False),
    'share_name': {
        'name': '--share-name',
        'help': L('the name of the file share'),
        'required': True,
    },
    'tags' : {
        'name': '--tags',
        'metavar': 'TAGS',
        'help': L('individual and/or key/value pair tags in "a=b;c" format'),
        'required': False,
        'type': _parse_tags
    },
    'timeout': {
        'name': '--timeout',
        'help': L('timeout in seconds'),
        'required': False,
        'type': int
    }
})

STORAGE_DATA_CLIENT_ARGS = {
    'account_name': COMMON_PARAMETERS['account_name'],
    'account_key': COMMON_PARAMETERS['account_key'],
    'connection_string': COMMON_PARAMETERS['connection_string'],
}

# ACCOUNT COMMANDS

build_operation(
    'storage account',
    'storage_accounts',
    _storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.check_name_availability,
                              'Result', 'check-name'),
        AutoCommandDefinition(StorageAccountsOperations.delete, None),
        AutoCommandDefinition(StorageAccountsOperations.get_properties, 'StorageAccount', 'show'),
        AutoCommandDefinition(StorageAccountsOperations.list_keys, '[StorageAccountKeys]')
    ],
    command_table)

@command_table.command('storage account list', description=L('List storage accounts.'))
@command_table.option(**COMMON_PARAMETERS['optional_resource_group_name'])
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

key_options = ['key1', 'key2']
@command_table.command('storage account renew-keys')
@command_table.description(L('Regenerate one or both keys for a storage account.'))
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option(**COMMON_PARAMETERS['account_name'])
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
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option(**COMMON_PARAMETERS['account_name_required'])
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
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option(**COMMON_PARAMETERS['account_name_required'])
@command_table.option(**COMMON_PARAMETERS['location'])
@command_table.option('--type', choices=storage_account_types.keys(), required=True)
@command_table.option(**COMMON_PARAMETERS['tags'])
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
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option(**COMMON_PARAMETERS['account_name_required'])
@command_table.option('--type',
                      choices=storage_account_types.keys())
@command_table.option(**COMMON_PARAMETERS['tags'])
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
        AutoCommandDefinition(BlockBlobService.create_container, None, 'create')
    ],
    command_table, None, STORAGE_DATA_CLIENT_ARGS)

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}

@command_table.command('storage container exists')
@command_table.description(L('Check if a storage container exists.'))
@command_table.option(**COMMON_PARAMETERS['container_name'])
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
@command_table.option('--snapshot', type=_parse_datetime,
                      help=L('UTC datetime value which specifies a snapshot'))
@command_table.option(**COMMON_PARAMETERS['timeout'])
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

build_operation('storage container lease', None, _blob_data_service_factory,
                [
                    AutoCommandDefinition(BlockBlobService.renew_container_lease, None, 'renew'),
                    AutoCommandDefinition(BlockBlobService.release_container_lease,
                                          None, 'release'),
                    AutoCommandDefinition(BlockBlobService.change_container_lease,
                                          'LeaseId', 'change')
                ],
                command_table, None, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage container lease acquire')
@command_table.description(L('Acquire a lock on a container for delete operations.'))
@command_table.option(**COMMON_PARAMETERS['container_name'])
@command_table.option('--lease-duration',
                      help=L('Values: {}'.format(lease_duration_values_string)),
                      type=int, required=True)
@command_table.option('--proposed-lease-id', help=L('proposed lease id in GUID format'))
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
@command_table.option(**COMMON_PARAMETERS['if_modified_since'])
@command_table.option(**COMMON_PARAMETERS['if_unmodified_since'])
@command_table.option(**COMMON_PARAMETERS['timeout'])
def acquire_container_lease(args):
    bbs = _blob_data_service_factory(args)
    return bbs.acquire_container_lease(
        container_name=args.get('container_name'),
        lease_duration=args.get('lease_duration'),
        proposed_lease_id=args.get('proposed_lease_id'),
        if_modified_since=args.get('if_modified_since'),
        if_unmodified_since=args.get('if_unmodified_since'),
        timeout=args.get('timeout'))

@command_table.command('storage container lease break')
@command_table.description(L('Break a lock on a container for delete operations.'))
@command_table.option(**COMMON_PARAMETERS['container_name'])
@command_table.option('--lease-break-period', type=int,
                      help=L('Values: {}'.format(lease_duration_values_string)), required=True)
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
@command_table.option(**COMMON_PARAMETERS['if_modified_since'])
@command_table.option(**COMMON_PARAMETERS['if_unmodified_since'])
@command_table.option(**COMMON_PARAMETERS['timeout'])
def break_container_lease(args):
    bbs = _blob_data_service_factory(args)
    bbs.break_container_lease(
        container_name=args.get('container_name'),
        lease_break_period=args.get('lease_break_period'),
        if_modified_since=args.get('if_modified_since'),
        if_unmodified_since=args.get('if_unmodified_since'),
        timeout=args.get('timeout'))

# BLOB COMMANDS

build_operation('storage blob', None, _blob_data_service_factory,
                [
                    AutoCommandDefinition(BlockBlobService.list_blobs, '[Blob]', 'list'),
                    AutoCommandDefinition(BlockBlobService.delete_blob, None, 'delete'),
                    AutoCommandDefinition(BlockBlobService.get_blob_properties,
                                          'BlobProperties', 'show')
                ],
                command_table, None, STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage blob upload-block-blob')
@command_table.description(L('Upload a block blob to a container.'))
@command_table.option(**COMMON_PARAMETERS['container_name'])
@command_table.option(**COMMON_PARAMETERS['blob_name'])
@command_table.option('--upload-from', required=True)
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
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
@command_table.option(**COMMON_PARAMETERS['container_name'])
@command_table.option(**COMMON_PARAMETERS['blob_name'])
@command_table.option('--download-to', help=L('the file path to download to'), required=True)
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
def download_blob(args):
    bbs = _blob_data_service_factory(args)

    # show dot indicator of download progress (one for every 10%)
    bbs.get_blob_to_path(args.get('container_name'),
                         args.get('blob_name'),
                         args.get('download_to'),
                         progress_callback=_update_progress)

@command_table.command('storage blob exists')
@command_table.description(L('Check if a storage blob exists.'))
@command_table.option(**COMMON_PARAMETERS['container_name'])
@command_table.option(**COMMON_PARAMETERS['blob_name'])
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
@command_table.option('--snapshot', type=_parse_datetime,
                      help=L('UTC datetime value which specifies a snapshot'))
@command_table.option(**COMMON_PARAMETERS['timeout'])
def exists_blob(args):
    bbs = _blob_data_service_factory(args)
    return str(bbs.exists(
        blob_name=args.get('blob_name'),
        container_name=args.get('container_name'),
        snapshot=args.get('snapshot'),
        timeout=args.get('timeout')))

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
        AutoCommandDefinition(FileService.get_share_metadata, 'Metadata', 'show-metadata'),
        AutoCommandDefinition(FileService.set_share_metadata, None, 'set-metadata')
    ],
    command_table,
    {
        'metadata': COMMON_PARAMETERS['metadata']
    },
    STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage share exists')
@command_table.description(L('Check if a file share exists.'))
@command_table.option(**COMMON_PARAMETERS['share_name'])
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
def exist_share(args):
    fsc = _file_data_service_factory(args)
    return str(fsc.exists(share_name=args.get('share_name')))

# DIRECTORY COMMANDS

build_operation(
    'storage directory', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.create_directory, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_directory, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.get_directory_metadata, 'Metadata', 'show-metadata'),
        AutoCommandDefinition(FileService.set_directory_metadata, None, 'set-metadata')
    ],
    command_table,
    {
        'metadata': COMMON_PARAMETERS['metadata']
    },
    STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage directory exists')
@command_table.description(L('Check if a directory exists.'))
@command_table.option(**COMMON_PARAMETERS['share_name'])
@command_table.option('--directory-name -d', help=L('the directory name'), required=True)
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
def exist_directory(args):
    fsc = _file_data_service_factory(args)
    return str(fsc.exists(share_name=args.get('share_name'),
                          directory_name=args.get('directory_name')))

# FILE COMMANDS

build_operation(
    'storage file', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.delete_file, 'Boolean', 'delete'),
    ],
    command_table,
    {
        'directory_name': {
            'name': '--directory-name -d',
            'help': L('the directory to delete'),
            'required': False
        }
    },
    STORAGE_DATA_CLIENT_ARGS)

@command_table.command('storage file download')
@command_table.option(**COMMON_PARAMETERS['share_name'])
@command_table.option('--file-name -f', help=L('the file name'), required=True)
@command_table.option('--local-file-name', help=L('the path to the local file'), required=True)
@command_table.option('--directory-name -d', help=L('the directory name'))
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
def storage_file_download(args):
    fsc = _file_data_service_factory(args)
    fsc.get_file_to_path(args.get('share_name'),
                         args.get('directory_name'),
                         args.get('file_name'),
                         args.get('local_file_name'),
                         progress_callback=_update_progress)

@command_table.command('storage file exists')
@command_table.description(L('Check if a file exists.'))
@command_table.option(**COMMON_PARAMETERS['share_name'])
@command_table.option('--file-name -f', help=L('the file name to check'), required=True)
@command_table.option('--directory-name -d', help=L('subdirectory path to the file'))
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
def exist_file(args):
    fsc = _file_data_service_factory(args)
    return str(fsc.exists(share_name=args.get('share_name'),
                          directory_name=args.get('directory_name'),
                          file_name=args.get('file_name')))

@command_table.command('storage file upload')
@command_table.option(**COMMON_PARAMETERS['share_name'])
@command_table.option('--file-name -f', help=L('the destination file name'), required=True)
@command_table.option('--local-file-name', help=L('the file name to upload'), required=True)
@command_table.option('--directory-name -d', help=L('the destination directory to upload to'))
@command_table.option(**COMMON_PARAMETERS['account_name'])
@command_table.option(**COMMON_PARAMETERS['account_key'])
@command_table.option(**COMMON_PARAMETERS['connection_string'])
def storage_file_upload(args):
    fsc = _file_data_service_factory(args)
    fsc.create_file_from_path(args.get('share_name'),
                              args.get('directory_name'),
                              args.get('file_name'),
                              args.get('local_file_name'),
                              progress_callback=_update_progress)
