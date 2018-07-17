# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands import AzCommandGroup, AzArgumentContext

import azure.cli.command_modules.storage._help  # pylint: disable=unused-import


class StorageCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType

        storage_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.storage.custom#{}')
        super(StorageCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    resource_type=ResourceType.DATA_STORAGE,
                                                    custom_command_type=storage_custom,
                                                    command_group_cls=StorageCommandGroup,
                                                    argument_context_cls=StorageArgumentContext)

    def load_command_table(self, args):
        super(StorageCommandsLoader, self).load_command_table(args)
        from azure.cli.command_modules.storage.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        super(StorageCommandsLoader, self).load_arguments(command)
        from azure.cli.command_modules.storage._params import load_arguments
        load_arguments(self, command)


class StorageArgumentContext(AzArgumentContext):
    def register_sas_arguments(self):
        from azure.cli.command_modules.storage._validators import ipv4_range_type, get_datetime_type
        self.argument('ip', type=ipv4_range_type,
                      help='Specifies the IP address or range of IP addresses from which to accept requests. Supports '
                           'only IPv4 style addresses.')
        self.argument('expiry', type=get_datetime_type(True),
                      help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes invalid. Do not '
                           'use if a stored access policy is referenced with --id that specifies this value.')
        self.argument('start', type=get_datetime_type(True),
                      help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes valid. Do not use '
                           'if a stored access policy is referenced with --id that specifies this value. Defaults to '
                           'the time of the request.')
        self.argument('protocol', options_list=('--https-only',), action='store_const', const='https',
                      help='Only permit requests made with the HTTPS protocol. If omitted, requests from both the HTTP '
                           'and HTTPS protocol are permitted.')

    def register_content_settings_argument(self, settings_class, update, arg_group=None, guess_from_file=None):
        from azure.cli.command_modules.storage._validators import get_content_setting_validator

        self.ignore('content_settings')
        self.extra('content_type', default=None, help='The content MIME type.', arg_group=arg_group,
                   validator=get_content_setting_validator(settings_class, update, guess_from_file=guess_from_file))
        self.extra('content_encoding', default=None, help='The content encoding type.', arg_group=arg_group)
        self.extra('content_language', default=None, help='The content language.', arg_group=arg_group)
        self.extra('content_disposition', default=None, arg_group=arg_group,
                   help='Conveys additional information about how to process the response payload, and can also be '
                        'used to attach additional metadata.')
        self.extra('content_cache_control', default=None, help='The cache control string.', arg_group=arg_group)
        self.extra('content_md5', default=None, help='The content\'s MD5 hash.', arg_group=arg_group)

    def register_path_argument(self, default_file_param=None, options_list=None):
        from ._validators import get_file_path_validator
        from .completers import file_path_completer

        path_help = 'The path to the file within the file share.'
        if default_file_param:
            path_help = '{} If the file name is omitted, the source file name will be used.'.format(path_help)
        self.extra('path', options_list=options_list or ('--path', '-p'),
                   required=default_file_param is None, help=path_help,
                   validator=get_file_path_validator(default_file_param=default_file_param),
                   completer=file_path_completer)
        self.ignore('file_name')
        self.ignore('directory_name')

    def register_source_uri_arguments(self, validator, blob_only=False):
        self.argument('copy_source', options_list=('--source-uri', '-u'), validator=validator, required=False,
                      arg_group='Copy Source')
        self.extra('source_sas', default=None, arg_group='Copy Source',
                   help='The shared access signature for the source storage account.')
        self.extra('source_container', default=None, arg_group='Copy Source',
                   help='The container name for the source storage account.')
        self.extra('source_blob', default=None, arg_group='Copy Source',
                   help='The blob name for the source storage account.')
        self.extra('source_snapshot', default=None, arg_group='Copy Source',
                   help='The blob snapshot for the source storage account.')
        self.extra('source_account_name', default=None, arg_group='Copy Source',
                   help='The storage account name of the source blob.')
        self.extra('source_account_key', default=None, arg_group='Copy Source',
                   help='The storage account key of the source blob.')
        if not blob_only:
            self.extra('source_path', default=None, arg_group='Copy Source',
                       help='The file path for the source storage account.')
            self.extra('source_share', default=None, arg_group='Copy Source',
                       help='The share name for the source storage account.')

    def register_common_storage_account_options(self):
        from azure.cli.core.commands.parameters import get_three_state_flag, get_enum_type
        from ._validators import validate_encryption_services

        t_access_tier, t_sku_name, t_encryption_services = self.command_loader.get_models(
            'AccessTier', 'SkuName', 'EncryptionServices', resource_type=ResourceType.MGMT_STORAGE)

        self.argument('https_only', help='Allows https traffic only to storage service.',
                      arg_type=get_three_state_flag())
        self.argument('sku', help='The storage account SKU.', arg_type=get_enum_type(t_sku_name))
        self.argument('assign_identity', action='store_true', resource_type=ResourceType.MGMT_STORAGE,
                      min_api='2017-06-01',
                      help='Generate and assign a new Storage Account Identity for this storage account for use '
                           'with key management services like Azure KeyVault.')
        self.argument('access_tier', arg_type=get_enum_type(t_access_tier),
                      help='The access tier used for billing StandardBlob accounts. Cannot be set for StandardLRS, '
                           'StandardGRS, StandardRAGRS, or PremiumLRS account types. It is required for '
                           'StandardBlob accounts during creation')

        if t_encryption_services:
            encryption_choices = list(
                t_encryption_services._attribute_map.keys())  # pylint: disable=protected-access
            self.argument('encryption_services', arg_type=get_enum_type(encryption_choices),
                          resource_type=ResourceType.MGMT_STORAGE, min_api='2016-12-01', nargs='+',
                          validator=validate_encryption_services, help='Specifies which service(s) to encrypt.')


class StorageCommandGroup(AzCommandGroup):
    def storage_command(self, name, method_name=None, command_type=None, **kwargs):
        """ Registers an Azure CLI Storage Data Plane command. These commands always include the four parameters which
        can be used to obtain a storage client: account-name, account-key, connection-string, and sas-token. """
        if command_type:
            command_name = self.command(name, method_name, command_type=command_type, **kwargs)
        else:
            command_name = self.command(name, method_name, **kwargs)
        self._register_data_plane_account_arguments(command_name)

    def storage_custom_command(self, name, method_name, **kwargs):
        command_name = self.custom_command(name, method_name, **kwargs)
        self._register_data_plane_account_arguments(command_name)

    def _register_data_plane_account_arguments(self, command_name):
        """ Add parameters required to create a storage client """
        from azure.cli.core.commands.parameters import get_resource_name_completion_list
        from azure.cli.command_modules.storage._validators import validate_client_parameters
        command = self.command_loader.command_table.get(command_name, None)
        if not command:
            return

        group_name = 'Storage Account'
        command.add_argument('account_name', '--account-name', required=False, default=None,
                             arg_group=group_name,
                             completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'),
                             help='Storage account name. Related environment variable: AZURE_STORAGE_ACCOUNT. Must be '
                                  'used in conjunction with either storage account key or a SAS token. If neither are '
                                  'present, the command will try to query the storage account key using the '
                                  'authenticated Azure account. If a large number of storage commands are executed the '
                                  'API quota may be hit')
        command.add_argument('account_key', '--account-key', required=False, default=None,
                             arg_group=group_name,
                             help='Storage account key. Must be used in conjunction with storage account name. '
                                  'Environment variable: AZURE_STORAGE_KEY')
        command.add_argument('connection_string', '--connection-string', required=False, default=None,
                             validator=validate_client_parameters, arg_group=group_name,
                             help='Storage account connection string. Environment variable: '
                                  'AZURE_STORAGE_CONNECTION_STRING')
        command.add_argument('sas_token', '--sas-token', required=False, default=None,
                             arg_group=group_name,
                             help='A Shared Access Signature (SAS). Must be used in conjunction with storage account '
                                  'name. Environment variable: AZURE_STORAGE_SAS_TOKEN')


COMMAND_LOADER_CLS = StorageCommandsLoader
