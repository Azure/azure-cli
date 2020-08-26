# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-import

from azure.cli.core import AzCommandsLoader
import azure.cli.command_modules.ams._help


class MediaServicesCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.profiles import ResourceType
        super(MediaServicesCommandsLoader, self).__init__(cli_ctx=cli_ctx, resource_type=ResourceType.MGMT_MEDIA)

    def load_command_table(self, args):
        from azure.cli.command_modules.ams.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.ams._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = MediaServicesCommandsLoader
