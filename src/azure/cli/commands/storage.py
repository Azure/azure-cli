from ..main import CONFIG, SESSION
from .._logging import logging
from .._util import TableOutput
from ..commands import command, description, option

@command('storage account list')
@description('List storage accounts')
@option('--resource-group -g <resourceGroup>', _("the resource group name"))
@option('--subscription -s <id>', _("the subscription id"))
def list_accounts(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    from azure.mgmt.storage.models import StorageAccount
    from msrestazure.azure_active_directory import UserPassCredentials
    
    username = ''   # TODO: get username somehow
    password = ''   # TODO: get password somehow

    logging.code('''smc = StorageManagementClient(StorageManagementClientConfiguration(
    credentials=UserPassCredentials(%r, %r),
    subscription_id=%r
)''', username, password, args.subscription)
    smc = StorageManagementClient(StorageManagementClientConfiguration(
        credentials=UserPassCredentials(username, password),
        subscription_id=args.subscription,
    ))

    group = args.get('resource-group')
    if group:
        logging.code('accounts = smc.storage_accounts.list_by_resource_group(%r)', group)
        accounts = smc.storage_accounts.list_by_resource_group(group)
    else:
        logging.code('accounts = smc.storage_accounts.list()')
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
    
    logging.code('''smc = StorageManagementClient(StorageManagementClientConfiguration())
smc.storage_accounts.check_name_availability({0.account_name!r})
'''.format(args))
    
    smc = StorageManagementClient(StorageManagementClientConfiguration())
    logging.warn(smc.storage_accounts.check_name_availability(args.account_name))
    
    
