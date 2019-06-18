# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-import
# pylint: disable=line-too-long

from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.servicebus._help import helps


class ServicebusCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        servicebus_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.servicebus.custom#{}')
        super(ServicebusCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=servicebus_custom,
                                                       resource_type=ResourceType.MGMT_SERVICEBUS,
                                                       suppress_extension=ModExtensionSuppress(__name__, 'servicebus', '0.0.1',
                                                                                               reason='These commands are now in the CLI.',
                                                                                               recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.servicebus.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.servicebus._params import load_arguments_sb
        load_arguments_sb(self, command)


COMMAND_LOADER_CLS = ServicebusCommandsLoader
