# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.servicediscovery._client_factory import cf_servicediscovery


def load_command_table(self, _):

    # TODO: Add command type here
    # servicediscovery_sdk = CliCommandType(
    #    operations_tmpl='<PATH>.operations#.{}',
    #    client_factory=cf_servicediscovery)

    with self.command_group('discovery namespace') as g:
        g.custom_command('create', 'create_namespace')
        g.custom_command('delete', 'delete_namespace')
        g.custom_command('list', 'list_namespace')
        g.custom_command('show', 'show_namespace')


    with self.command_group('discovery service') as g:
        g.custom_command('create', 'create_service')
        g.custom_command('delete', 'delete_service')
        g.custom_command('list', 'list_service')
        g.custom_command('show', 'show_service')


    with self.command_group('discovery instance') as g:
        g.custom_command('create', 'create_instance')
        g.custom_command('delete', 'delete_instance')
        g.custom_command('list', 'list_instance')
        g.custom_command('show', 'show_instance')


    with self.command_group('container-app') as g:
        g.custom_command('create', 'create_containerapp_discovery')