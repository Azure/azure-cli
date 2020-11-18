# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.aro._params import load_arguments
from azure.cli.command_modules.aro.commands import load_command_table
from azure.cli.core import AzCommandsLoader, ModExtensionSuppress
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.aro._client_factory import cf_aro  # pylint: disable=unused-import

from azure.cli.command_modules.aro._help import helps  # pylint: disable=unused-import


class AroCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        aro_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.aro.custom#{}',
            client_factory=cf_aro)

        suppress = ModExtensionSuppress(__name__, 'aro', '1.0.0',
                                        reason='Its functionality is included in the core az CLI.',
                                        recommend_remove=True)
        super(AroCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                suppress_extension=suppress,
                                                custom_command_type=aro_custom,
                                                resource_type=ResourceType.MGMT_ARO)

    def load_command_table(self, args):
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = AroCommandsLoader
