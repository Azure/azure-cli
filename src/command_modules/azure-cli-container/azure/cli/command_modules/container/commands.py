# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import empty_on_404
from ._client_factory import cf_container_groups, cf_container_logs
from ._format import transform_container_group_list, transform_container_group


def load_command_table(self, _):
    with self.command_group('container', client_factory=cf_container_groups) as g:
        g.custom_command('list', 'list_containers', table_transformer=transform_container_group_list)
        g.custom_command('create', 'create_container', table_transformer=transform_container_group)
        g.custom_command('show', 'get_container', exception_handler=empty_on_404,
                         table_transformer=transform_container_group)
        g.custom_command('delete', 'delete_container', confirmation=True)
        g.custom_command('logs', 'container_logs', client_factory=cf_container_logs)
        g.custom_command('exec', 'container_exec')
        g.custom_command('export', 'container_export')
        g.custom_command('attach', 'attach_to_container')
