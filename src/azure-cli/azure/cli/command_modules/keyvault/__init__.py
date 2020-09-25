# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType
import azure.cli.command_modules.keyvault._help  # pylint: disable=unused-import


class KeyVaultCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.keyvault._client_factory import keyvault_mgmt_client_factory
        from azure.cli.command_modules.keyvault._command_type import KeyVaultCommandGroup, KeyVaultArgumentContext
        from azure.cli.core import ModExtensionSuppress
        keyvault_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.keyvault.custom#{}',
            client_factory=keyvault_mgmt_client_factory
        )

        super(KeyVaultCommandsLoader, self).__init__(
            cli_ctx=cli_ctx,
            resource_type=ResourceType.MGMT_KEYVAULT,
            custom_command_type=keyvault_custom,
            command_group_cls=KeyVaultCommandGroup,
            argument_context_cls=KeyVaultArgumentContext,
            # Suppress myextension up to and including version 0.1.3
            suppress_extension=ModExtensionSuppress(__name__, 'keyvault-preview',
                                                    '0.1.3',
                                                    reason='These commands are now in the CLI.',
                                                    recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.keyvault.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.keyvault._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = KeyVaultCommandsLoader
