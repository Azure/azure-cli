from msrest import Serializer
from ..commands import command, description, option
from ._command_creation import get_service_client
from .._argparse import IncorrectUsageError
from .._logging  import logger
from .._locale import L

@command('storage blob blockblob create')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--container -c <name>', required=True)
@option('--blob-name -bn <name>', required=True)
@option('--upload-from -uf <file>', required=True)
@option('--container.public-access -cpa <none, blob, container>')
@option('--content-settings.type -cst <type>')
@option('--content-settings.disposition -csd <setting>')
@option('--content-settings.encoding -cse <setting>')
@option('--content-settings.language -csl <setting>')
@option('--content-settings.md5 -csm <setting>')
@option('--content-settings.cache-control -cscc <setting>')
def create_block_blob(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings

    block_blob_service = BlockBlobService(account_name=args.get('account-name'),
                                          account_key=args.get('account-key'))

    # TODO: update this once enums are supported in commands first-class (task #115175885)
    public_access_types = {'none': None,
                           'blob': PublicAccess.Blob,
                           'container': PublicAccess.Container}
    try:
        public_access = public_access_types[args.get('container.public-access')] \
                        if args.get('container.public-access') \
                        else None
    except KeyError:
        raise IncorrectUsageError("container.public-access must be either none, blob or container")

    block_blob_service.create_container(args.get('container'), public_access=public_access)

    return block_blob_service.create_blob_from_path(
        args.get('container'),
        args.get('blob-name'),
        args.get('upload-from'),
        content_settings=ContentSettings(content_type=args.get('content-settings.type'), 
                                         content_disposition=args.get('content-settings.disposition'),
                                         content_encoding=args.get('content-settings.encoding'),
                                         content_language=args.get('content-settings.language'),
                                         content_md5=args.get('content-settings.md5'),
                                         cache_control=args.get('content-settings.cache-control')
                                         )
        )

@command('storage blob list')
@option('--account-name -an <name>', required=True)
@option('--account-key -ak <key>', required=True)
@option('--container -c <name>', required=True)
def list_blobs(args, unexpected): #pylint: disable=unused-argument
    from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings

    block_blob_service = BlockBlobService(account_name=args.get('account-name'),
                                          account_key=args.get('account-key'))

    blobs = block_blob_service.list_blobs(args.get('container'))
    return Serializer().serialize_data(blobs.items, "[Blob]")
