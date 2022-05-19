# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):

    configure_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.configure.custom#{}')

    with self.command_group('', configure_custom) as g:
        g.command('configure', 'handle_configure')

    with self.command_group('cache', configure_custom) as g:
        g.command('list', 'list_cache_contents')
        g.command('show', 'show_cache_contents')  # pylint: disable=show-command
        g.command('delete', 'delete_cache_contents')
        g.command('purge', 'purge_cache_contents')
