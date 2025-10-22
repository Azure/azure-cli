# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):
    # Azure Local Migration Commands
    with self.command_group('migrate local') as g:
        g.custom_command('get-discovered-server', 'get_discovered_server')

    with self.command_group('migrate local replication') as g:
        g.custom_command('init', 'initialize_replication_infrastructure')
        g.custom_command('new', 'new_local_server_replication')
