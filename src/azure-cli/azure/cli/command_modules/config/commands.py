# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):

    config_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.config.custom#{}')

    with self.command_group('config', config_custom, is_experimental=True) as g:
        g.command('set', 'config_set')
        g.command('get', 'config_get')
        g.command('unset', 'config_unset')
