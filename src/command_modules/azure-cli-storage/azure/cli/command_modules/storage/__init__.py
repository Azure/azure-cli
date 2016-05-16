# pylint: disable=unused-import
from .generated import command_table
@command_table.command('storage share mount')
@command_table.description('Mount an SMB 3.0 file share in Windows or Linux (not OSX). Must ' + \
    'have inbound and outbound TCP access of port 445. For Linux, the share will be mounted as ' + \
    'the share name. For Windows, a drive letter must be specified.')
@command_table.option(**PARAMETER_ALIASES['share_name'])
@command_table.option('--drive', required=False,
                      help=L('the desired drive letter (Required on Windows)'))
@command_table.option(**PARAMETER_ALIASES['account_name'])
@command_table.option(**PARAMETER_ALIASES['account_key'])
def mount_share(args):
    drive = args.get('drive')
    share_name = args.get('share_name')
    account_name = args.get('account_name')
    account_key = args.get('account_key')
    if not account_name or not account_key:
        raise IncorrectUsageError('storage account name and key are required, or appropriate ' + \
            'environment variables must be set')
    if os.name == 'nt':
        if not drive:
            raise IncorrectUsageError('drive letter is required for Windows')
        command = 'net use {}: \\\\{}.file.core.windows.net\\{} {} /user:{}'.format(
            drive, account_name, share_name, account_key, account_name)
    elif os.name == 'posix':
        try:
            subprocess.check_output('apt show cifs-utils'.split())
        except subprocess.CalledProcessError:
            raise RuntimeError('\'cifs-utils\' package required to run this command')
        if not os.path.isdir(share_name):
            os.makedirs(share_name)
        command = 'sudo mount -t cifs //{}.file.core.windows.net/{} ./{} ' + \
                  '-o vers=3.0,username={},password={},dir_mode=0777,file_mode=0666'
        command.format(account_name, share_name, share_name, account_name, account_key)
    try:
        subprocess.check_output(command.split())
    except subprocess.CalledProcessError:
        raise RuntimeError('Unable to mount \'{}\''.format(share_name))
