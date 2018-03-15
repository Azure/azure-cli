# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.command_modules.dms._client_factory import dms_client_factory

from azure.cli.core.commands import CliCommandType

def load_command_table(self, _):

    dms_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.services_operations#ServicesOperations.{}',
        client_factory=dms_client_factory
    )
    
    dms_tasks_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.tasks_operations#TasksOperations.{}',
        client_factory=dms_client_factory
    )

    with self.command_group('dms', dms_sdk) as g:
        g.custom_command('check-name-availability', 'check_service_name_availability', client_factory=dms_client_factory)
        g.custom_command('check-status', 'check_service_status', client_factory=dms_client_factory)
        g.custom_command('create', 'create_service', client_factory=dms_client_factory)
        g.custom_command('delete', 'delete_service', client_factory=dms_client_factory)
        g.custom_command('list', 'list_services', client_factory=dms_client_factory)
        g.custom_command('show', 'get_service', client_factory=dms_client_factory)

    with self.command_group('dms task', dms_tasks_sdk) as g:
        #g.custom_command('list', 'list_tasks', client_factory=dms_client_factory)
        g.command('list', 'list')
        #g.command('create', 'create_or_update')
        #g.command('set', 'create_or_update')
        g.command('show', 'get')
        #g.command('delete', 'delete')
        #g.command('update', 'update')
        #g.command('cancel', 'cancel')