# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.maps._help  # pylint: disable=unused-import
from azure.cli.command_modules.maps._client_factory import cf_accounts


class MapsCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        custom_type = CliCommandType(
            operations_tmpl='azure.cli.command_modules.maps.custom#{}',
            client_factory=cf_accounts)
        super(MapsCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                 custom_command_type=custom_type,
                                                 resource_type=ResourceType.MGMT_MAPS)

    def load_command_table(self, args):
        from azure.cli.command_modules.maps.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.maps._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = MapsCommandsLoader
