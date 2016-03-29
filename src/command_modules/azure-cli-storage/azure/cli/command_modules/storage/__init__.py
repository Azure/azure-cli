from __future__ import print_function
from datetime import datetime
from os import environ
from sys import stderr
from six.moves import input #pylint: disable=redefined-builtin

from azure.storage.blob import PublicAccess
from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType
from azure.mgmt.storage.operations import StorageAccountsOperations

from azure.cli._argparse import IncorrectUsageError
from azure.cli.commands import command, description, option
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._auto_command import build_operation
from azure.cli._locale import L


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
@option('--key -y <key>', L('renew a specific key. Values {}'.format(key_values_string)))
def renew_account_keys(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()

    resource_group = args.get('resource-group')
    account_name = args.get('account-name')
    key_name = args.get('key')
    if key_name and key_name not in key_values:
        raise ValueError(L('Unrecognized key value: {}'.format(key_name)))
    else:
        for key in [key_name] if key_name else key_values:
            result = smc.storage_accounts.regenerate_key(
                resource_group_name=resource_group,
                account_name=account_name,
                key_name=key)

    return result

@command('storage account usage')
@description(L('Show the current count and limit of the storage accounts under the subscription.'))
def show_account_usage(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()
    return next((x for x in smc.usage.list() if x.name.value == 'StorageAccounts'), None)

@command('storage account connection-string')
@description(L('Show the connection string for a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--use-http', L('use http as the default endpoint protocol'))
def show_storage_connection_string(args, unexpected): #pylint: disable=unused-argument
    smc = _storage_client_factory()

    endpoint_protocol = 'http' if args.get('use-http') else 'https'
    storage_account = _resolve_storage_account(args)
    keys = smc.storage_accounts.list_keys(args.get('resource-group'), storage_account)

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
storage_account_type_string = ' | '.join(storage_account_types)

@command('storage account create')
@description(L('Create a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'), required=True)
@option('--location -l <location>',
        L('location in which to create the storage account'), required=True)
@option('--type -t <type>',
        L('Values: {}'.format(storage_account_type_string)), required=True)
@option('--tags <tags>',
        L('storage account tags. Tags are key=value pairs separated with semicolon(;)'))
def create_account(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage.models import StorageAccountCreateParameters

    smc = _storage_client_factory()

    resource_group = args.get('resource-group')
    account_name = args.get('account-name')

    try:
        account_type = storage_account_types[args.get('type')]
    except KeyError:
        raise IncorrectUsageError(L('type must be: {}'
                                    .format(storage_account_type_string)))
    params = StorageAccountCreateParameters(args.get('location'),
                                            account_type,
                                            _parse_dict(args, 'tags'))

    return smc.storage_accounts.create(resource_group, account_name, params)

@command('storage account set')
@description(L('Update storage account property (only one at a time).'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'), required=True)
@option('--type -t <type>', L('Values: {}'.format(storage_account_type_string)))
@option('--tags <tags>',
        L('storage account tags. Tags are key=value pairs separated with semicolon(;)'))
@option('--custom-domain <customDomain>', L('the custom domain name'))
@option('--subdomain', L('use indirect CNAME validation'))
def set_account(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage.models import StorageAccountUpdateParameters, CustomDomain

    smc = _storage_client_factory()

    resource_group = args.get('resource-group')
    account_name = args.get('account-name')
    domain = args.get('custom-domain')
    try:
        account_type = storage_account_types[args.get('type')] if args.get('type') else None
    except KeyError:
        raise IncorrectUsageError(L('type must be: {}'
                                    .format(storage_account_type_string)))
    params = StorageAccountUpdateParameters(_parse_dict(args, 'tags'), account_type, domain)

    return smc.storage_accounts.update(resource_group, account_name, params)

# CONTAINER COMMANDS

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}
public_access_string = ' | '.join(public_access_types)

@command('storage container create')
@description(L('Create a storage container.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--public-access -p <accessType>', L('Values: {}'.format(public_access_string)))
@option('--metadata -m <metaData>', L('dict of key=value pairs (separated by ;)'))
@option('--fail-on-exist', L('operation fails if container already exists'))
@option('--timeout <seconds>')
def create_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    try:
        public_access = public_access_types[args.get('public-access')] \
                                            if args.get('public-access') \
                                            else None
    except KeyError:
        raise IncorrectUsageError(L('public-access must be: {}'
                                    .format(public_access_string)))

    metadata = _parse_dict(args, 'metadata', allow_singles=False)

    if not bbs.create_container(
            container_name=args.get('container-name'),
            public_access=public_access,
            metadata=metadata,
            fail_on_exist=True if args.get('fail-on-exist') else False,
            timeout=_parse_int(args, 'timeout')):
        raise RuntimeError(L('Container creation failed.'))

@command('storage container delete')
@description(L('Delete a storage container.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--force -f', L('supress delete confirmation prompt'))
@option('--fail-not-exist', L('operation fails if container does not exist'))
@option('--lease-id <id>', L('delete only if lease is ID active and matches'))
@option('--if-modified-since <dateTime>', L('delete only if container modified since ' + \
    'supplied UTC datetime'))
@option('--in-unmodified-since <dateTime>', L('delete only if container has not been modified ' + \
    'since supplied UTC datetime'))
@option('--timeout <seconds>')
def delete_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    container_name = args.get('container-name')

    if args.get('force') is None:
        ans = input('Really delete {}? [Y/n] '.format(container_name))
        if not ans or ans[0].lower() != 'y':
            return 0

    if not bbs.delete_container(
            container_name=container_name,
            fail_not_exist=True if args.get('fail-not-exist') else False,
            lease_id=args.get('lease-id'),
            if_unmodified_since=_parse_datetime(args, 'if-unmodified-since'),
            if_modified_since=_parse_datetime(args, 'if-modified-since'),
            timeout=_parse_int(args, 'timeout')):
        raise RuntimeError(L('Container deletion failed.'))

@command('storage container exists')
@description(L('Check if a storage container exists.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--snapshot <datetime>', L('UTC datetime value which specifies a snapshot'))
@option('--timeout <seconds>')
def exists_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return str(bbs.exists(
        container_name=args.get('container-name'),
        snapshot=_parse_datetime(args, 'snapshot'),
        timeout=_parse_int(args, 'timeout')))

@command('storage container list')
@description(L('List storage containers.'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--prefix -p <prefix>', L('container name prefix to filter by'))
@option('--num-results <num>')
@option('--include-metadata')
@option('--marker <marker>', L('continuation token for enumerating additional results'))
@option('--timeout <seconds>')
def list_containers(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.list_containers(
        prefix=args.get('prefix'),
        num_results=_parse_int(args, 'num-results'),
        include_metadata=True if args.get('include-metadata') else False,
        marker=args.get('marker'),
        timeout=_parse_int(args, 'timeout'))

@command('storage container show')
@description(L('Show details of a storage container'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--lease-id <id>', L('delete only if lease is ID active and matches'))
@option('--timeout <seconds>')
def show_container(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.get_container_properties(
        container_name=args.get('container-name'),
        lease_id=args.get('lease-id'),
        timeout=_parse_int(args, 'timeout'))

lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
    lease_duration_values['min'],
    lease_duration_values['max'],
    lease_duration_values['infinite'])

@command('storage container lease acquire')
@description(L('Acquire a lock on a container for delete operations.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--lease-duration --ld <leaseDuration>',
        L('Values: {}'.format(lease_duration_values_string)), required=True)
@option('--proposed-lease-id --plid <id>', L('proposed lease id in GUID format'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--if-modified-since <dateTime>', L('delete only if container modified since ' + \
    'supplied UTC datetime'))
@option('--in-unmodified-since <dateTime>', L('delete only if container has not been modified ' + \
    'since supplied UTC datetime'))
@option('--timeout <seconds>')
def acquire_container_lease(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    try:
        lease_duration = int(args.get('lease-duration'))
    except ValueError:
        raise IncorrectUsageError('lease-duration must be: {}'.format(lease_duration_values_string))

    return bbs.acquire_container_lease(
        container_name=args.get('container-name'),
        lease_duration=lease_duration,
        proposed_lease_id=args.get('proposed-lease-id'),
        if_modified_since=_parse_int(args, 'if-modified-since'),
        if_unmodified_since=_parse_int(args, 'if-unmodified-since'),
        timeout=True if args.get('timeout') else False)

@command('storage container lease renew')
@description(L('Renew a lock on a container for delete operations.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--lease-id --lid <id>', L('lease id to renew in GUID format'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--if-modified-since <dateTime>', L('delete only if container modified since ' + \
    'supplied UTC datetime'))
@option('--in-unmodified-since <dateTime>', L('delete only if container has not been modified ' + \
    'since supplied UTC datetime'))
@option('--timeout <seconds>')
def renew_container_lease(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.renew_container_lease(
        container_name=args.get('container-name'),
        lease_id=args.get('lease-id'),
        if_modified_since=_parse_int(args, 'if-modified-since'),
        if_unmodified_since=_parse_int(args, 'if-unmodified-since'),
        timeout=True if args.get('timeout') else False)

@command('storage container lease release')
@description(L('Release a lock on a container for delete operations.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--lease-id --lid <id>', L('lease id in GUID format to release'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--if-modified-since <dateTime>', L('delete only if container modified since ' + \
    'supplied UTC datetime'))
@option('--in-unmodified-since <dateTime>', L('delete only if container has not been modified ' + \
    'since supplied UTC datetime'))
@option('--timeout <seconds>')
def release_container_lease(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    bbs.release_container_lease(
        container_name=args.get('container-name'),
        lease_id=args.get('lease-id'),
        if_modified_since=_parse_int(args, 'if-modified-since'),
        if_unmodified_since=_parse_int(args, 'if-unmodified-since'),
        timeout=True if args.get('timeout') else False)

@command('storage container lease change')
@description(L('Change the lease id for a container lease.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--lease-id --lid <leaseId>', L('the lease id to change'), required=True)
@option('--proposed-lease-id --plid <id>', L('proposed lease id in GUID format'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--if-modified-since <dateTime>', L('delete only if container modified since ' + \
    'supplied UTC datetime'))
@option('--in-unmodified-since <dateTime>', L('delete only if container has not been modified ' + \
    'since supplied UTC datetime'))
@option('--timeout <seconds>')
def change_container_lease(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.change_container_lease(
        container_name=args.get('container-name'),
        lease_id=args.get('lease-id'),
        proposed_lease_id=args.get('proposed-lease-id'),
        if_modified_since=_parse_int(args, 'if-modified-since'),
        if_unmodified_since=_parse_int(args, 'if-unmodified-since'),
        timeout=True if args.get('timeout') else False)

@command('storage container lease break')
@description(L('Break a lock on a container for delete operations.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--lease-break-period --lbp <period>',
        L('Values: {}'.format(lease_duration_values_string)), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--if-modified-since <dateTime>', L('delete only if container modified since ' + \
    'supplied UTC datetime'))
@option('--in-unmodified-since <dateTime>', L('delete only if container has not been modified ' + \
    'since supplied UTC datetime'))
@option('--timeout <seconds>')
def break_container_lease(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    try:
        lease_break_period = int(args.get('lease-break-period'))
    except ValueError:
        raise ValueError('lease-break-period must be: {}'.format(lease_duration_values_string))

    bbs.break_container_lease(
        container_name=args.get('container-name'),
        lease_break_period=lease_break_period,
        if_modified_since=_parse_int(args, 'if-modified-since'),
        if_unmodified_since=_parse_int(args, 'if-unmodified-since'),
        timeout=True if args.get('timeout') else False)

# BLOB COMMANDS
# TODO: Evaluate for removing hand-authored commands in favor of auto-commands (task ##115068835)

@command('storage blob upload-block-blob')
@description(L('Upload a block blob to a container.'))
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
    from azure.storage.blob import ContentSettings
    bbs = _get_blob_service_client(args)
    try:
        public_access = public_access_types[args.get('public-access')] \
                                            if args.get('public-access') \
                                            else None
    except KeyError:
        raise IncorrectUsageError(L('container.public-access must be: {}'
                                    .format(public_access_string)))

    bbs.create_container(args.get('container-name'), public_access=public_access)

    return bbs.create_blob_from_path(
        container_name=args.get('container-name'),
        blob_name=args.get('blob-name'),
        file_path=args.get('upload-from'),
        progress_callback=_update_progress,
        content_settings=ContentSettings(content_type=args.get('content.type'),
                                         content_disposition=args.get('content.disposition'),
                                         content_encoding=args.get('content.encoding'),
                                         content_language=args.get('content.language'),
                                         content_md5=args.get('content.md5'),
                                         cache_control=args.get('content.cache-control'))
        )

@command('storage blob list')
@command(L('List all blobs in a container.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--prefix -p <prefix>', L('blob name prefix to filter by'))

@option('--num-results <num>')
@option('--include <stuff>', L('specifies one or more additional datasets to include '\
    + 'in the response. Unsupported this release'))
@option('--delimiter <value>', L('Unsupported this release'))
@option('--marker <marker>', L('continuation token for enumerating additional results'))
@option('--timeout <seconds>')
def list_blobs(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    blobs = bbs.list_blobs(
        container_name=args.get('container-name'),
        prefix=args.get('prefix'),
        num_results=_parse_int(args, 'num-results'),
        include=None,
        delimiter=None,
        marker=args.get('marker'),
        timeout=_parse_int(args, 'timeout'))
    return list(blobs.items)

@command('storage blob delete')
@description(L('Delete a blob from a container.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--blob-name -b <blobName>', L('the name of the blob'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def delete_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.delete_blob(args.get('container-name'), args.get('blob-name'))

@command('storage blob exists')
@description(L('Check if a blob exists.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--blob-name -b <blobName>', L('the name of the blob'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--snapshot <datetime>', L('UTC datetime value which specifies a snapshot'))
@option('--timeout <seconds>')
def exists_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return str(bbs.exists(
        container_name=args.get('container-name'),
        blob_name=args.get('blob-name'),
        snapshot=_parse_datetime(args, 'snapshot'),
        timeout=_parse_int(args, 'timeout')))

@command('storage blob show')
@description(L('Show properties of the specified blob.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--blob-name -bn <name>', L('the name of the blob'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def show_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    return bbs.get_blob_properties(args.get('container-name'), args.get('blob-name'))

@command('storage blob download')
@description(L('Download the specified blob.'))
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--blob-name -bn <name>', L('the name of the blob'), required=True)
@option('--download-to -dt <path>', L('the file path to download to'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def download_blob(args, unexpected): #pylint: disable=unused-argument
    bbs = _get_blob_service_client(args)
    container_name = args.get('container-name')
    blob_name = args.get('blob-name')
    download_to = args.get('download-to')
    bbs.get_blob_to_path(container_name,
                         blob_name,
                         download_to,
                         progress_callback=_update_progress)

# SHARE COMMANDS

@command('storage share exists')
@description(L('Check if a file share exists.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def exist_share(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    return str(fsc.exists(share_name=args.get('share-name')))

@command('storage share list')
@description(L('List file shares within a storage account.'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
@option('--prefix -p <prefix>', L('share name prefix to filter by'))
def list_shares(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    return list(fsc.list_shares(prefix=args.get('prefix')))

@command('storage share contents')
@description(L('List files and directories inside a share path.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--directory-name -d <directoryName>', L('share subdirectory path to examine'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def list_files(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    return list(fsc.list_directories_and_files(
        args.get('share-name'),
        directory_name=args.get('directory-name')))

@command('storage share create')
@description(L('Create a new file share.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def create_share(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    if not fsc.create_share(args.get('share-name')):
        raise RuntimeError(L('Share creation failed.'))

@command('storage share delete')
@description(L('Create a new file share.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def delete_share(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    if not fsc.delete_share(args.get('share-name')):
        raise RuntimeError(L('Share deletion failed.'))

# DIRECTORY COMMANDS

@command('storage directory exists')
@description(L('Check if a directory exists.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--directory-name -d <directoryName>', L('the directory name'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def exist_directory(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    return str(fsc.exists(share_name=args.get('share-name'),
                          directory_name=args.get('directory-name')))

@command('storage directory create')
@description(L('Create a directory within a share.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--directory-name -d <directoryName>', L('the directory to create'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def create_directory(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    if not fsc.create_directory(
            share_name=args.get('share-name'),
            directory_name=args.get('directory-name')):
        raise RuntimeError(L('Directory creation failed.'))

@command('storage directory delete')
@description(L('Delete a directory within a share.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--directory-name -d <directoryName>', L('the directory to delete'), required=True)
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def delete_directory(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    if not fsc.delete_directory(
            share_name=args.get('share-name'),
            directory_name=args.get('directory-name')):
        raise RuntimeError(L('Directory deletion failed.'))

# FILE COMMANDS

@command('storage file download')
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--file-name -f <fileName>', L('the file name'), required=True)
@option('--local-file-name -lfn <path>', L('the path to the local file'), required=True)
@option('--directory-name -d <directoryName>', L('the directory name'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
def storage_file_download(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    fsc.get_file_to_path(args.get('share-name'),
                         args.get('directory-name'),
                         args.get('file-name'),
                         args.get('local-file-name'),
                         progress_callback=_update_progress)

@command('storage file exists')
@description(L('Check if a file exists.'))
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--file-name -f <fileName>', L('the file name'), required=True)
@option('--directory-name -d <directoryName>', L('subdirectory path to the file'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
@option('--connection-string -t <connectionString>', L('the storage connection string'))
def exist_file(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    return str(fsc.exists(share_name=args.get('share-name'),
                          directory_name=args.get('directory-name'),
                          file_name=args.get('file-name')))

@command('storage file upload')
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--file-name -f <fileName>', L('the file name'), required=True)
@option('--local-file-name -lfn <path>', L('the path to the local file'), required=True)
@option('--directory-name -d <directoryName>', L('the directory name'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
def storage_file_upload(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    fsc.create_file_from_path(args.get('share-name'),
                              args.get('directory-name'),
                              args.get('file-name'),
                              args.get('local-file-name'),
                              progress_callback=_update_progress)

@command('storage file delete')
@option('--share-name -s <shareName>', L('the file share name'), required=True)
@option('--file-name -f <fileName>', L('the file name'), required=True)
@option('--directory-name -d <directoryName>', L('the directory name'))
@option('--account-name -n <accountName>', L('the storage account name'))
@option('--account-key -k <accountKey>', L('the storage account key'))
def storage_file_delete(args, unexpected): #pylint: disable=unused-argument
    fsc = _get_file_service_client(args)
    fsc.delete_file(args.get('share-name'),
                    args.get('directory-name'),
                    args.get('file-name'))

# HELPER METHODS

def _get_blob_service_client(args):
    from azure.storage.blob import BlockBlobService
    return get_data_service_client(BlockBlobService,
                                   _resolve_storage_account(args),
                                   _resolve_storage_account_key(args),
                                   _resolve_connection_string(args))

def _get_file_service_client(args):
    from azure.storage.file import FileService
    return get_data_service_client(FileService,
                                   _resolve_storage_account(args),
                                   _resolve_storage_account_key(args),
                                   _resolve_connection_string(args))

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
def _parse_datetime(args, key):
    # TODO This should handle timezone
    datestring = args.get(key)
    if not datestring:
        return None
    time = datetime.strptime(datestring, DATETIME_FORMAT)
    return time

def _parse_dict(args, key, allow_singles=True):
    """ Parses dictionaries passed in as argument strings in key=value;key=value format.
    If 'allow_singles' is set to False, single tags will be ignored."""
    string_val = args.get(key)
    if not string_val:
        return None
    kv_list = [x for x in string_val.split(';') if '=' in x]     # key-value pairs
    result = dict(x.split('=') for x in kv_list)
    if allow_singles:
        s_list = [x for x in string_val.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result

def _parse_int(args, key):
    try:
        str_val = args.get(key)
        int_val = int(str_val) if str_val else None
    except ValueError:
        int_val = None
    return int_val

# TODO: Remove once these parameters are supported first-class by @option (task #116054675)
def _resolve_storage_account(args):
    return args.get('account-name') or environ.get('AZURE_STORAGE_ACCOUNT')

def _resolve_storage_account_key(args):
    return args.get('account-key') or environ.get('AZURE_STORAGE_ACCESS_KEY')

def _resolve_connection_string(args):
    return args.get('connection-string') or environ.get('AZURE_STORAGE_CONNECTION_STRING')

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
