# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):  # pylint: disable=unused-argument
    edge_action_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.edge_action.custom#{}')

    with self.command_group('edge-action version', edge_action_custom) as g:
        g.custom_command('deploy-from-file', 'deploy_edge_action_version')
