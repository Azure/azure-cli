# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    artifact_ops = CliCommandType(
        operations_tmpl='azure.cli.command_modules.devops.custom#{}'
    )

    with self.command_group('artifacts universal', command_type=artifact_ops) as g:
        g.command('publish', 'publish_package')
        g.command('download', 'download_package')
