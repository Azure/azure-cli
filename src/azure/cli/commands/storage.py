import logging
from ..main import CONFIG, SESSION
from ..commands import command, option

@command('storage test')
@option('<pos>')
@option('--bool')
@option('--arg <value>')
def test(args, unexpected):
    print('test', args.positional)
    print('test', args)

@command('storage test subtest')
def subtest(args, unexpected):
    print('subtest', args.positional)
    print('subtest', args)

@command('storage account check')
@option('--account-name <name>')
def checkname(args, unexpected):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    
    logging.info('''smc = StorageManagementClient(StorageManagementClientConfiguration())
smc.storage_accounts.check_name_availability({0.account_name!r})
'''.format(args))
    
    smc = StorageManagementClient(StorageManagementClientConfiguration())
    logging.warn(smc.storage_accounts.check_name_availability(args.account_name))
    
    
