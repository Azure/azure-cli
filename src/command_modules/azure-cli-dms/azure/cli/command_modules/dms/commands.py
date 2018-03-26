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

    dms_skus_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.resource_skus_operations#ResourceSkusOperations.{}',
        client_factory=dms_client_factory
    )
    
    dms_tasks_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.tasks_operations#TasksOperations.{}',
        client_factory=dms_client_factory
    )

    with self.command_group('dms', dms_sdk, client_factory=dms_client_factory) as g:
        g.custom_command('check-name-availability', 'check_service_name_availability')
        g.custom_command('check-status', 'check_service_status')
        g.custom_command('create', 'create_service')
        g.custom_command('delete', 'delete_service')
        g.custom_command('list', 'list_services')
        g.custom_command('show', 'get_service')
        g.custom_command('start', 'start_service')
        g.custom_command('stop', 'stop_service')
        g.custom_command('subtest', 'subtest')

    with self.command_group('dms', dms_skus_sdk, client_factory=dms_client_factory) as g:
        g.custom_command('list-skus', 'list_skus')

    with self.command_group('dms task', dms_tasks_sdk, client_factory=dms_client_factory) as g:
        #g.custom_command('list', 'list_tasks')
        g.command('list', 'list')
        #g.command('create', 'create_or_update')
        #g.command('set', 'create_or_update')
        g.command('show', 'get')
        #g.command('delete', 'delete')
        #g.command('update', 'update')
        #g.command('cancel', 'cancel')