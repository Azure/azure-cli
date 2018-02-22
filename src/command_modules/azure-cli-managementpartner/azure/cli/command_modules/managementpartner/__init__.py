# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.managementpartner._help  # pylint: disable=unused-import
from azure.cli.command_modules.managementpartner._client_factory import managementpartner_partner_client_factory
from ._exception_handler import managementpartner_exception_handler


class ManagementpartnerCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        managementpartner_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.managementpartner.custom#{}',
            client_factory=managementpartner_partner_client_factory,
            exception_handler=managementpartner_exception_handler
        )

        super(ManagementpartnerCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=managementpartner_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.managementpartner.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.managementpartner._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ManagementpartnerCommandsLoader
