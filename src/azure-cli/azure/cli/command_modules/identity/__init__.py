# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.identity._help  # pylint: disable=unused-import
from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType

class IdentityCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.identity._client_factory import (_msi_user_identities_operations,
                                                                      _msi_federated_identity_credentials_operations)

        # Base identity commands
        identity_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.identity.custom#{}',
            client_factory=_msi_user_identities_operations
        )

        # Federated credential commands
        federated_identity_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.identity.custom#{}',
            client_factory=_msi_federated_identity_credentials_operations
        )

        super().__init__(cli_ctx=cli_ctx,
                        resource_type=ResourceType.MGMT_MSI,
                        custom_command_type=identity_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.identity.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.identity._params import load_arguments
        load_arguments(self, command)

COMMAND_LOADER_CLS = IdentityCommandsLoader
