import logging

def add_storage_commands(create_command):
    cna = create_command('checkname')
    cna.add_argument('--account_name', '-a', type=str, metavar='NAME')
    
def checkname(args):
    logging.info('''smc = StorageManagementClient(StorageManagementClientConfiguration())
smc.storage_accounts.check_name_availability({account_name!r})
'''.format_map(vars(args)))