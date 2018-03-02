# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.command_modules.dms._client_factory import dms_client_factory

from azure.cli.core.commands import CliCommandType

def load_command_table(self, _):
    
    dms_tasks_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.tasks_operations#TasksOperations.{}',
        client_factory=dms_client_factory
    )

    with self.command_group('dms task', dms_tasks_sdk) as g:
        g.command('list', 'list')
        g.command('create', 'create_or_update')
        g.command('set', 'create_or_update')
        g.command('show', 'get')
        g.command('delete', 'delete')
        g.command('update', 'update')
        g.command('cancel', 'cancel')