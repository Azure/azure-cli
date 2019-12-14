# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.acs.commands import load_command_table
from azure.cli.command_modules.acs._params import load_arguments

import azure.cli.command_modules.acs._help  # pylint: disable=unused-import


class ContainerServiceCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        acs_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.acs.custom#{}')
        super(ContainerServiceCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                             custom_command_type=acs_custom,
                                                             resource_type=ResourceType.MGMT_CONTAINERSERVICE)

    def load_command_table(self, args):
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = ContainerServiceCommandsLoader
