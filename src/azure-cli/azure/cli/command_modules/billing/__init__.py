# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.billing._help  # pylint: disable=unused-import


class BillingCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        billing_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.billing.custom#{}')
        super(BillingCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=billing_custom,
                                                    resource_type=ResourceType.MGMT_BILLING)

    def load_command_table(self, args):
        from azure.cli.command_modules.billing.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.billing._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = BillingCommandsLoader
