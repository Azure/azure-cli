from azure.storage.blob import PublicAccess
from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client, get_data_service_client
from .._argparse import IncorrectUsageError
from .._locale import L

@command('storage account list')
@description(L('List storage accounts.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'))
@option('--subscription -s <id>', L('the subscription id'))
def list_accounts(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials

    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

    group = args.get('resource-group')
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()

    return list(accounts)

@command('storage account check')
@description(L('Check whether an account name is valid and not in use.'))
@option('--account-name -an <name>', required=True)
def checkname(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    availability = smc.storage_accounts.check_name_availability(args.get('account-name'))
    return availability

@command('storage account show')
@description(L('Show details of a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -an <name>', L('the storage account name'), required=True)
def show_account(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    result = smc.storage_accounts.get_properties(args.get('resource-group'), args.get('account-name'))
    return result

@command('storage account keys list')
@description(L('List the keys for a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -an <name>', L('the storage account name'), required=True)
def list_account_keys(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    result = smc.storage_accounts.list_keys(args.get('resource-group'), args.get('account-name'))
    return result

@command('storage account keys renew')
@description(L('Regenerate a key for a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -an <name>', L('the storage account name'), required=True)
@option('--primary -p', L('renew the primary key'))
@option('--secondary -s', L('renew the secondary key'))
def renew_account_keys(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    key_name = 'key1' if args.get('primary') is not None else None
    if not key_name:
        key_name = 'key2' if args.get('secondary') is not None else None
    if not key_name:
        raise ValueError('Must specify a key to renew')
    result = smc.storage_accounts.regenerate_key(
        resource_group_name=args.get('resource-group'), 
        account_name=args.get('account-name'),
        key_name=key_name)
    return result

@command('storage account usage show')
@description(L('Show the current count and limit of the storage accounts under the subscription.'))
def show_account_usage(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    # TODO: format is not great. Keys are alphabetical instead of a more logical order
    result = {'subscription':smc.usage.config.subscription_id}
    for item in smc.usage.list():
        if item.name.value == 'StorageAccounts':
            result['used'] = item.current_value
            result['limit'] = item.limit
            break
    return result

@command('storage account connectionstring show')
@description(L('Show the connection string for a storage account.'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--account-name -an <name>', L('the storage account name'), required=True)
@option('--use-http <useHttp>', L('use http as the default endpoint protocol'))
def show_storage_connection_string(args, unexpected):
    import json
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    endpoint_protocol = 'http' if args.get('use-http') is not None else 'https'
    results = {'DefaultEndpointsProtocol':endpoint_protocol}
    results['AccountName'] = args.get('account-name')
    keys = smc.storage_accounts.list_keys(args.get('resource-group'), args.get('account-name'))
    results['AccountKey'] = keys.key1
    return results

@command('storage account container create')
@description(L('Create a storage container.'))
@option('--account-name -an <name>', L('the storage account name'), required=True)
@option('--account-key -ak <key>', L('the storage account key'), required=True)
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
def create_container(args, unexpected):
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService, 
                                  args.get('account-name'),
                                  args.get('account-key'))
    result_code = 1 if bbs.create_container(args.get('container-name')) else 0
    result = {'CreateContainer':result_code}
    return result 

@command('storage account container delete')
@description(L('Delete a storage container.'))
@option('--account-name -an <name>', L('the storage account name'), required=True)
@option('--account-key -ak <key>', L('the storage account key'), required=True)
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
@option('--quiet <quiet>', L('supress delete confirmation prompt'))
def delete_container(args, unexpected):
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  args.get('account-name'),
                                  args.get('account-key'))
    container_name = args.get('container-name')
    prompt_for_delete = args.get('quiet') is None
    if prompt_for_delete:
        # TODO: prompt user to confirm delete
        print('Really delete %s? ' % container_name)
        pass
    result_code = 1 if bbs.delete_container(container_name) else 0
    result = {'DeleteContainer':result_code}
    return result

@command('storage account container list')
@description(L('List storage containers.'))
@option('--account-name -an <name>', L('the storage account name'), required=True)
@option('--account-key -ak <key>', L('the storage account key'), required=True)
@option('--prefix -p <prefix>', L('prefix of container names to return'))
def list_containers(args, unexpected):
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  args.get('account-name'),
                                  args.get('account-key'))
    results = bbs.list_containers(args.get('prefix'))
    # TODO: summarize the list? Right now, simply return the data.
    return results

@command('storage account container show')
@description(L('Show details of a storage container'))
@option('--account-name -an <name>', L('the storage account name'), required=True)
@option('--account-key -ak <key>', L('the storage account key'), required=True)
@option('--container-name -c <containerName>', L('the name of the container'), required=True)
def show_container(args, unexpected):
    from azure.storage.blob import BlockBlobService, ContentSettings
    bbs = get_data_service_client(BlockBlobService,
                                  args.get('account-name'),
                                  args.get('account-key'))
    result = bbs.get_container_properties(args.get('container-name'))
    return result

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None,
                       'blob': PublicAccess.Blob,
                       'container': PublicAccess.Container}
public_access_string = ' | '.join(public_access_types)

@command('storage blob blockblob create')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--container-name -c <name>', required=True)
@option('--blob-name -bn <name>', required=True)
@option('--upload-from -uf <file>', required=True)
@option('--container.public-access -cpa <accessType>', 'Values: {}'.format(public_access_string))
@option('--content.type -cst <type>')
@option('--content.disposition -csd <disposition>')
@option('--content.encoding -cse <encoding>')
@option('--content.language -csl <language>')
@option('--content.md5 -csm <md5>')
@option('--content.cache-control -cscc <cacheControl>')
def create_block_blob(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings

    block_blob_service = get_data_service_client(BlockBlobService, args.get('account-name'),
                                                 args.get('account-key'))

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
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--container -c <name>', required=True)
def list_blobs(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, ContentSettings

    block_blob_service = get_data_service_client(BlockBlobService, args.get('account-name'),
                                                 args.get('account-key'))

    blobs = block_blob_service.list_blobs(args.get('container'))
    return blobs.items

@command('storage file create')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--share-name -sn <setting>', required=True)
@option('--file-name -fn <setting>', required=True)
@option('--local-file-name -lfn <setting>', required=True)
@option('--directory-name -dn <setting>')
def storage_file_create(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.file import FileService

    file_service = get_data_service_client(FileService, args.get('account-name'),
                                           args.get('account-key'))

    file_service.create_file_from_path(args.get('share-name'),
                                       args.get('directory-name'),
                                       args.get('file-name'),
                                       args.get('local-file-name'))
