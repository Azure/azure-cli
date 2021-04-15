# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404
from azure.cli.command_modules.webpubsub._client_factory import cf_webpubsub


def load_command_table(self, _):

    webpubsub_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.webpubsub.custom#{}',
        client_factory=cf_webpubsub
    )

    with self.command_group('webpubsub', webpubsub_sdk) as g:
        g.command('create', 'create_webpubsub')
        g.command('delete', 'delete_webpubsub')
        g.command('list', 'list_webpubsub')
        g.show_command('show', 'show_webpubsub', exception_handler=empty_on_404)
        g.generic_update_command('update', getter_name='webpubsub_get',
                                 setter_name='webpubsub_set', custom_func_name='update_webpubsub')
