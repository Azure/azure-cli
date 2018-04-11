# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (get_location_type, get_enum_type, tags_type)
from azure.cli.command_modules.ams._completers import get_role_definition_name_completion_list

from azure.mediav3.models import (EncoderNamedPreset, Priority, AssetContainerPermission)

from ._validators import storage_account_id

# pylint: disable=line-too-long


def load_arguments(self, _):  # pylint: disable=too-many-locals, too-many-statements
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
    account_name_arg_type = CLIArgumentType(options_list=('--account-name', '-a'), metavar='ACCOUNT_NAME')
    storage_account_arg_type = CLIArgumentType(options_list=('--storage-account'), metavar='STORAGE_NAME')
    password_arg_type = CLIArgumentType(options_list=('--password', '-p'), metavar='PASSWORD_NAME')
    transform_name_arg_type = CLIArgumentType(options_list=('--transform-name', '-t'), metavar='TRANSFORM_NAME')
    expiry_arg_type = CLIArgumentType(options_list=('--expiry'), metavar='EXPIRY_TIME')

    with self.argument_context('ams account') as c:
        c.argument('account_name', name_arg_type, id_part='name',
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx),
                   validator=get_default_location_from_resource_group)
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('ams account create') as c:
        c.argument('storage_account', storage_account_arg_type,
                   help='The name or resource ID of the primary storage account to attach to the Azure Media Services account. Blob only accounts are not allowed as primary.',
                   validator=storage_account_id)

    with self.argument_context('ams account storage') as c:
        c.argument('account_name', account_name_arg_type,
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('storage_account', name_arg_type,
                   help='The name or resource ID of the secondary storage account to detach from the Azure Media Services account.',
                   validator=storage_account_id)

    with self.argument_context('ams account sp') as c:
        c.argument('account_name', account_name_arg_type,
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('sp_name', name_arg_type,
                   help="The app name or app URI to associate the RBAC with. If not present, a default name like '{amsaccountname}-access-sp' will be generated.")
        c.argument('sp_password', password_arg_type,
                   help="The password used to log in. Also known as 'Client Secret'. If not present, a random secret will be generated.")
        c.argument('role', completer=get_role_definition_name_completion_list)
        c.argument('xml', help='Enables xml output format.')
        c.argument('years', type=int, default=None)

    with self.argument_context('ams transform') as c:
        c.argument('account_name', account_name_arg_type, id_part='name',
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('transform_name', name_arg_type, id_part='child_name_1',
                   help='The name of the transform.')
        c.argument('preset_names', arg_type=get_enum_type(EncoderNamedPreset),
                   nargs='+',
                   help='Space-separated list of built preset names.')
        c.argument('description', help='Customer supplied description of the transform.')

    with self.argument_context('ams transform list') as c:
        c.argument('account_name', id_part=None)

    with self.argument_context('ams asset') as c:
        c.argument('account_name', account_name_arg_type, id_part='name',
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('asset_name', name_arg_type, id_part='child_name_1',
                   help='The name of the asset.')

    with self.argument_context('ams asset list') as c:
        c.argument('account_name', id_part=None)

    with self.argument_context('ams asset create') as c:
        c.argument('alternate_id', help='The alternate id of the asset.')
        c.argument('description', help='The asset description.')
        c.argument('asset_name', name_arg_type, help='The name of the asset.')

    with self.argument_context('ams asset get-sas-urls') as c:
        c.argument('permissions', arg_type=get_enum_type(AssetContainerPermission),
                   help='The permissions to set on the SAS URL.')
        c.argument('expiry_time', expiry_arg_type, help="Specifies the UTC datetime (Y-m-d'T'H:M'Z') at which the SAS becomes invalid.")

    with self.argument_context('ams job') as c:
        c.argument('account_name', account_name_arg_type, id_part='name',
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('transform_name', transform_name_arg_type, id_part='child_name_1',
                   help='The name of the transform.')
        c.argument('job_name', name_arg_type, id_part='child_name_2',
                   help='The name of the job.')

    with self.argument_context('ams job list') as c:
        c.argument('account_name', id_part=None)

    with self.argument_context('ams job start') as c:
        c.argument('priority', arg_type=get_enum_type(Priority),
                   help='The priority with which the job should be processed.')
        c.argument('description', help='The job description.')
        c.argument('input_asset_name',
                   arg_group='Asset Job Input',
                   help='The name of the input asset.')
        c.argument('output_asset_names',
                   nargs='+', help='Space-separated list of output asset names.')
        c.argument('base_uri',
                   arg_group='Http Job Input',
                   help='Base uri for http job input. It will be concatenated with provided file names. If no base uri is given, then the provided file list is assumed to be fully qualified uris.')
        c.argument('files',
                   nargs='+',
                   help='Space-separated list of files. It can be used to tell the service to only use the files specified from the input asset.')

    with self.argument_context('ams job cancel') as c:
        c.argument('delete', help='Delete the job being cancelled.')

    with self.argument_context('ams streaming') as c:
        c.argument('account_name', account_name_arg_type, id_part='name',
                   help='The name of the Azure Media Services account within the resource group.')
        c.argument('default_content_key_policy_name',
                   help='The default content key policy name used by the streaming locator.')

    with self.argument_context('ams streaming locator') as c:
        c.argument('streaming_locator_name', name_arg_type, id_part='child_name_1',
                   help='The name of the streaming locator.')
        c.argument('asset_name',
                   help='The name of the asset used by the streaming locator.')
        c.argument('streaming_policy_name',
                   help='The name of the streaming policy used by the streaming locator.')
        c.argument('start_time',
                   help="Start time (Y-m-d'T'H:M'Z') of the streaming locator.")
        c.argument('end_time',
                   help="End time (Y-m-d'T'H:M'Z') of the streaming locator.")

    with self.argument_context('ams streaming policy') as c:
        c.argument('streaming_policy_name', name_arg_type, id_part='child_name_1',
                   help='The name of the streaming policy.')
        c.argument('download',
                   arg_group='Encryption Protocols',
                   help='Enable Download protocol.')
        c.argument('dash',
                   arg_group='Encryption Protocols',
                   help='Enable Dash protocol.')
        c.argument('hls',
                   arg_group='Encryption Protocols',
                   help='Enable Hls protocol.')
        c.argument('smooth_streaming',
                   arg_group='Encryption Protocols',
                   help='Enable SmoothStreaming protocol.')

    with self.argument_context('ams streaming endpoint list') as c:
        c.argument('account_name', id_part=None)
