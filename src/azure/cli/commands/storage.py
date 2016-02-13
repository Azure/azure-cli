import logging
from ..main import RC
from ..commands import command

@command('storage test <pos> --bool --arg <value>')
def test(args):
    print(args.positional)
    print(args)

@command('storage account check --account-name <name>')
def checkname(args):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    
    logging.info('''smc = StorageManagementClient(StorageManagementClientConfiguration())
smc.storage_accounts.check_name_availability({0.account_name!r})
'''.format(args))
    
    smc = StorageManagementClient(StorageManagementClientConfiguration())
    logging.warn(smc.storage_accounts.check_name_availability(args.account_name))
    
    
