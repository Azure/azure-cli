from msrest import Serializer
from ..commands import command, description, option
from ._command_creation import get_service_client
from .._argparse import IncorrectUsageError
from .._logging  import logger
from .._locale import L

@command('storage file create')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--share-name -sn <setting>', required=True)
@option('--file-name -fn <setting>', required=True)
@option('--local-file-name -lfn <setting>', required=True)
@option('--directory-name -dn <setting>')
def storage_file_create(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.file import FileService

    file_service = FileService(account_name=args.get('account-name'),
                               account_key=args.get('account-key'))

    file_service.create_file_from_path(args.get('share-name'), 
                                       args.get('directory-name'), 
                                       args.get('file-name'),
                                       args.get('local-file-name'))
