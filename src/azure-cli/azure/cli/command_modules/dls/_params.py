# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    tags_type, get_resource_name_completion_list, resource_group_name_type, get_enum_type)

from azure.cli.command_modules.dls._validators import validate_resource_group_name
from azure.mgmt.datalake.store.models import (
    FirewallState,
    TrustedIdProviderState,
    TierType,
    FirewallAllowAzureIpsState)

from azure.mgmt.datalake.store.models import EncryptionConfigType


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):
    from ._validators import (
        validate_subnet
    )
    # ARGUMENT DEFINITIONS
    datalake_store_name_type = CLIArgumentType(help='Name of the Data Lake Store account.', options_list=['--account_name'], completer=get_resource_name_completion_list('Microsoft.DataLakeStore/accounts'), id_part='name')

    # PARAMETER REGISTRATIONS
    # global
    with self.argument_context('dls') as c:
        c.argument('account_name', datalake_store_name_type, options_list=['--account', '-n'])
        c.argument('top', help='Maximum number of items to return.', type=int)
        c.argument('skip', help='The number of items to skip over before returning elements.', type=int)
        c.argument('count', help='The Boolean value of true or false to request a count of the matching resources included with the resources in the response, e.g. Categories?$count=true.', type=bool)

    # global account
    with self.argument_context('dls account') as c:
        c.argument('tags', tags_type)
        c.argument('resource_group_name', resource_group_name_type, id_part=None, required=False, help='If not specified, will attempt to discover the resource group for the specified Data Lake Store account.', validator=validate_resource_group_name)
        c.argument('tier', arg_type=get_enum_type(TierType), help='The desired commitment tier for this account to use.')
        c.argument('default_group', help='Name of the default group to give permissions to for freshly created files and folders in the Data Lake Store account.')
        c.argument('key_version', help='Key version for the user-assigned encryption type.')

    # account
    for scope in ['dls account show', 'dls account delete']:
        with self.argument_context(scope) as c:
            c.argument('name', datalake_store_name_type, options_list=['--account', '-n'])

    with self.argument_context('dls account create') as c:
        c.argument('resource_group_name', resource_group_name_type, validator=None)
        c.argument('account_name', datalake_store_name_type, options_list=['--account', '-n'], completer=None)
        c.argument('encryption_type', arg_type=get_enum_type(EncryptionConfigType), help='Indicates what type of encryption to provision the account with. By default, encryption is ServiceManaged. If no encryption is desired, it must be explicitly set with the --disable-encryption flag.')
        c.argument('disable_encryption', help='Indicates that the account will not have any form of encryption applied to it.', action='store_true')

    with self.argument_context('dls account update') as c:
        c.argument('trusted_id_provider_state', arg_type=get_enum_type(TrustedIdProviderState), help='Enable/disable the existing trusted ID providers.')
        c.argument('firewall_state', arg_type=get_enum_type(FirewallState), help='Enable/disable existing firewall rules.')
        c.argument('allow_azure_ips', arg_type=get_enum_type(FirewallAllowAzureIpsState), help='Allow/block Azure originating IPs through the firewall')

    with self.argument_context('dls account list') as c:
        c.argument('resource_group_name', resource_group_name_type, validator=None)

    #####
    # virtual network rule
    #####
    with self.argument_context('dls account network-rule') as c:
        c.argument('account_name', datalake_store_name_type, options_list=['--account-name'], id_part=None)
        c.argument('resource_group_name', resource_group_name_type, id_part='resource_group')

        c.argument('virtual_network_rule_name',
                   options_list=['--name', '-n'],
                   help='The virtual network rule name',
                   id_part='name')

        c.argument('subnet',
                   options_list=['--subnet'],
                   help='Name or ID of the subnet that allows access to DLS. '
                   'If subnet name is provided, --name must be provided.')

    with self.argument_context('dls account network-rule create') as c:
        c.extra('vnet_name',
                help='The virtual network rule name',
                validator=validate_subnet)

    with self.argument_context('dls account network-rule update') as c:
        c.argument('subnet_id',
                   options_list=['--subnet'],
                   help='Name or ID of the subnet that allows access to DLS. '
                   'If subnet name is provided, --name must be provided.')

        c.extra('vnet_name', help='The virtual network rule name')

    with self.argument_context('dls account network-rule list') as c:
        c.argument('virtual_network_rule_name', id_part=None)

    # filesystem
    with self.argument_context('dls fs') as c:
        c.argument('path', help='The path in the specified Data Lake Store account where the action should take place. In the format \'/folder/file.txt\', where the first \'/\' after the DNS indicates the root of the file system.')
        c.argument('overwrite', help='Indicates that, if the destination file or folder exists, it should be overwritten', action='store_true')
        c.argument('chunk_size', help='Number of bytes for a chunk. Large files are split into chunks. Files smaller than this number will always be transferred in a single thread.', type=int, default=268435456, required=False)
        c.argument('buffer_size', help='Number of bytes for internal buffer. This block cannot be bigger than a chunk and cannot be smaller than a block.', type=int, default=4194304, required=False)
        c.argument('block_size', help='Number of bytes for a block. Within each chunk, we write a smaller block for each API call. This block cannot be bigger than a chunk.', type=int, default=4194304, required=False)
        c.ignore('progress_callback')

    with self.argument_context('dls fs create') as c:
        c.argument('force', help='Indicates that, if the file or folder exists, it should be overwritten', action='store_true')
        c.argument('folder', help='Indicates that this new item is a folder and not a file.', action='store_true')

    with self.argument_context('dls fs delete') as c:
        c.argument('recurse', help='Indicates this should be a recursive delete of the folder.', action='store_true')

    with self.argument_context('dls fs upload') as c:
        c.argument('thread_count', help='Specify the parallelism of the upload. Default is the number of cores in the local machine.', type=int)

    with self.argument_context('dls fs download') as c:
        c.argument('thread_count', help='Specify the parallelism of the download. Default is the number of cores in the local machine.', type=int)

    with self.argument_context('dls fs preview') as c:
        c.argument('force', help='Indicates that, if the preview is larger than 1MB, still retrieve it. This can potentially be very slow, depending on how large the file is.', action='store_true')

    with self.argument_context('dls fs join') as c:
        c.argument('force', help='Indicates that, if the destination file already exists, it should be overwritten', action='store_true')
        c.argument('source_paths', help='The list of files in the specified Data Lake Store account to join.', nargs='+')

    with self.argument_context('dls fs move') as c:
        c.argument('force', help='Indicates that, if the destination file or folder already exists, it should be overwritten and replaced with the file or folder being moved.', action='store_true')

    with self.argument_context('dls fs set-expiry') as c:
        c.argument('expiration_time', help='The absolute value of the expiration time expressed as milliseconds since the epoch.')

    # filesystem access params
    with self.argument_context('dls fs access') as c:
        c.argument('acl_spec', help=" The ACL specification to set on the path in the format '[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,...'.")

    with self.argument_context('dls fs access set-permission') as c:
        c.argument('permission', help='The octal representation of the permissions for user, group and mask (for example: 777 is full rwx for all entities)', type=int)

    with self.argument_context('dls fs access remove-all') as c:
        c.argument('default_acl', help='A switch that, if specified, indicates that the remove ACL operation should remove the default ACL of the folder. Otherwise the regular ACL is removed.', action='store_true')
