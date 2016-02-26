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
@option('--account-name <name>')
def checkname(args, unexpected): #pylint: disable=unused-argument 
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    smc = get_service_client(StorageManagementClient, StorageManagementClientConfiguration)
    logger.warning(smc.storage_accounts.check_name_availability(args.account_name))
