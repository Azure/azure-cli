# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import cf_container_groups, cf_container
from ._format import transform_container_group_list, transform_container_group


container_group_sdk = CliCommandType(
    operations_tmpl='azure.mgmt.containerinstance.operations.container_groups_operations#ContainerGroupsOperations.{}',
    client_factory=cf_container_groups
)


def load_command_table(self, _):
    with self.command_group('container', client_factory=cf_container_groups) as g:
        g.custom_command('list', 'list_containers', table_transformer=transform_container_group_list)
        g.custom_command('create', 'create_container', supports_no_wait=True,
                         table_transformer=transform_container_group)
        g.custom_show_command('show', 'get_container', table_transformer=transform_container_group)
        g.custom_command('delete', 'delete_container', confirmation=True)
        g.custom_command('logs', 'container_logs', client_factory=cf_container)
        g.custom_command('exec', 'container_exec')
        g.custom_command('export', 'container_export')
        g.custom_command('attach', 'attach_to_container')

    with self.command_group('container', container_group_sdk) as g:
        g.command('restart', 'restart')
        g.command('stop', 'stop')
