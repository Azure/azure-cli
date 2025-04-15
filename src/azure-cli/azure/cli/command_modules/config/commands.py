# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.config._validators import validate_param_persist, validate_param_persist_for_delete


def load_command_table(self, _):
    config_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.config.custom#{}')

    with self.command_group('config', config_custom, is_experimental=True) as g:
        g.command('set', 'config_set')
        g.command('get', 'config_get')
        g.command('unset', 'config_unset')

    with self.command_group('config param-persist', config_custom, is_experimental=True) as g:
        g.command('on', 'turn_param_persist_on')
        g.command('off', 'turn_param_persist_off')
        g.show_command('show', 'show_param_persist', validator=validate_param_persist)
        g.command('delete', 'delete_param_persist', validator=validate_param_persist_for_delete)
