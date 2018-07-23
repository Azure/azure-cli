# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.batch._help  # pylint: disable=unused-import
from azure.cli.command_modules.batch._exception_handler import batch_exception_handler
from azure.cli.command_modules.batch._command_type import BatchCommandGroup


class BatchCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        batch_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.batch.custom#{}',
            exception_handler=batch_exception_handler)
        super(BatchCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                  custom_command_type=batch_custom,
                                                  command_group_cls=BatchCommandGroup,
                                                  min_profile='2017-03-10-profile')
        self.module_name = __name__

    def load_command_table(self, args):
        super(BatchCommandsLoader, self).load_command_table(args)
        from azure.cli.command_modules.batch.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        super(BatchCommandsLoader, self).load_arguments(command)
        from azure.cli.command_modules.batch._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = BatchCommandsLoader
