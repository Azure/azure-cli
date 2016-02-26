from ..main import SESSION
from .._logging import logger
from .._util import TableOutput
from ..commands import command, description, option
from .._profile import Profile

@command('storage account list')
@description(_('List storage accounts'))
@option('--resource-group -g <resourceGroup>', _('the resource group name'))
@option('--subscription -s <id>', _('the subscription id'))
def list_accounts(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials

    profile = Profile()
    smc = StorageManagementClient(StorageManagementClientConfiguration(
        *profile.get_login_credentials(),
    ))

    group = args.get('resource-group')
    if group:
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        accounts = smc.storage_accounts.list()

    with TableOutput() as to:
        for acc in accounts:
            assert isinstance(acc, StorageAccount)
            to.cell('Name', acc.name)
            to.cell('Type', acc.account_type)
            to.cell('Location', acc.location)
            to.end_row()
        if not to.any_rows:
            print('No storage accounts defined')

@command('storage account check')
@option('--account-name <name>')
def checkname(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    
    smc = StorageManagementClient(StorageManagementClientConfiguration())
    logger.warn(smc.storage_accounts.check_name_availability(args.account_name))
    
    
