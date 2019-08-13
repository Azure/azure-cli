# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
import azure.cli.command_modules.hdinsight._help  # pylint: disable=unused-import


class HDInsightCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        hdinsight_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.hdinsight.custom#{}',
            operation_group='hdinsight')

        super(HDInsightCommandsLoader, self).__init__(
            cli_ctx=cli_ctx,
            operation_group='hdinsight',
            custom_command_type=hdinsight_custom)

    def load_command_table(self, args):
        from .commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from ._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = HDInsightCommandsLoader
