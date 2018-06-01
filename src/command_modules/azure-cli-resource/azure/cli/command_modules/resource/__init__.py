# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.resource._help  # pylint: disable=unused-import


class ResourceCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core import ModExtensionSuppress
        resource_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.resource.custom#{}')
        super(ResourceCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                     custom_command_type=resource_custom,
                                                     suppress_extension=ModExtensionSuppress(
                                                         __name__, 'managementgroups', '0.1.0',
                                                         reason='The management groups commands are now in CLI.',
                                                         recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.resource.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.resource._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ResourceCommandsLoader
