from msrest import Serializer
from ..commands import command, description, option
from ._command_creation import get_service_client
from .._logging  import logger
from .._locale import L

@command('storage account list')
@description(L('List storage accounts'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'))
@option('--subscription -s <id>', L('the subscription id'))
def list_accounts(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials

    smc = get_service_client(StorageManagementClient, StorageManagementClientConfiguration)

    group = args.get('resource-group')
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()

    serializable = Serializer().serialize_data(accounts, "[StorageAccount]")
    return serializable

@command('storage account check')
@option('--account-name -an <name>')
def checkname(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    logger.warning(smc.storage_accounts.check_name_availability(args.account_name))

@command('storage blob blockblob create')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--container -c <name>', required=True)
@option('--blob-name -bn <name>', required=True)
@option('--upload-from -uf <file>', required=True)
@option('--content-settings.type -cs <type>')
def create_block_blob(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings

    block_blob_service = BlockBlobService(account_name=args.get('account-name'), 
                                          account_key=args.get('account-key'))

    block_blob_service.create_container(args.get('container'), 
                                        public_access=PublicAccess.Container)

    return block_blob_service.create_blob_from_path(
        args.get('container'),
        args.get('blob-name'),
        args.get('upload-from'),
        content_settings=ContentSettings(content_type=args.get('content-settings.type')))

@command('storage blob list')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--container -c <name>', required=True)
def list_blobs(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings

    block_blob_service = BlockBlobService(account_name=args.get('account-name'), 
                                          account_key=args.get('account-key'))

    return [b.name for b in block_blob_service.list_blobs(args.get('container'))]
