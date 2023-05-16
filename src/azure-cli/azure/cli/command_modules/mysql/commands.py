# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.mysql._client_factory import cf_mysql


def load_command_table(self, _):

    # TODO: Add command type here
    # mysql_sdk = CliCommandType(
    #    operations_tmpl='<PATH>.operations#.{}',
    #    client_factory=cf_mysql)


    with self.command_group('mysql') as g:
        g.custom_command('create', 'create_mysql')
        # g.command('delete', 'delete')
        g.custom_command('list', 'list_mysql')
        # g.show_command('show', 'get')
        # g.generic_update_command('update', setter_name='update', custom_func_name='update_mysql')


    with self.command_group('mysql', is_preview=True):
        pass

