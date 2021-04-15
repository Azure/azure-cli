# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404
from azure.cli.command_modules.webpubsub._client_factory import cf_webpubsub


def load_command_table(self, _):

    webpubsub_general_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.webpubsub.custom#{}',
        client_factory=cf_webpubsub
    )

    webpubsub_key_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.webpubsub.key#{}',
        client_factory=cf_webpubsub
    )

    webpubsub_network_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.webpubsub.network#{}',
        client_factory=cf_webpubsub
    )

    webpubsub_eventhandler_utils = CliCommandType(
        operations_tmpl='azure.cli.command_modules.webpubsub.eventhandler#{}',
        client_factory=cf_webpubsub
    )

    with self.command_group('webpubsub', webpubsub_general_utils) as g:
        g.command('create', 'webpubsub_create')
        g.command('delete', 'webpubsub_delete')
        g.command('list', 'webpubsub_list')
        g.show_command('show', 'webpubsub_show', exception_handler=empty_on_404)
        g.command('restart', 'webpubsub_restart', exception_handler=empty_on_404)
        g.generic_update_command('update', getter_name='webpubsub_get',
                                 setter_name='webpubsub_set',
                                 custom_func_name='update_webpubsub')

    with self.command_group('webpubsub key', webpubsub_key_utils) as g:
        g.command('list', 'webpubsub_key_list')
        g.command('regenerate', 'webpubsub_key_regenerate')

    with self.command_group('webpubsub network-rule', webpubsub_network_utils) as g:
        g.command('list', 'list_network_rules')
        g.command('update', 'update_network_rules')

    with self.command_group('webpubsub event-handler', webpubsub_eventhandler_utils) as g:
        g.command('list', 'event_handler_list')
        g.command('update', 'event_handler_update')
        g.command('clear', 'event_handler_clear')
