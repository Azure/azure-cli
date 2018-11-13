# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._format import (
    #LongRunningOperationResultTransform,
    transform_sqlvm_group_output,
    transform_sqlvm_group_list
)

from ._util import (
    get_sqlvirtualmachine_availability_group_listeners_operations,
    get_sqlvirtualmachine_operations,
    get_sqlvirtualmachine_sql_virtual_machine_groups_operations,
    get_sqlvirtualmachine_sql_virtual_machines_operations,
)

# pylint: disable=too-many-statements,line-too-long,too-many-locals
def load_command_table(self, _):

    ###############################################
    #      sql virtual machine operations         #
    ###############################################

    sqlvm_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations.operations#Operations.{}',
        client_factory=get_sqlvirtualmachine_operations)

    with self.command_group('sqlvm op',
                            sqlvm_operations,
                            client_factory=get_sqlvirtualmachine_operations) as g:

        g.command('list', 'list')

    ###############################################
    #            sql virtual machine              #
    ###############################################

    sqlvm_vm_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations.sql_virtual_machines_operations#SqlVirtualMachinesOperations.{}',
        client_factory=get_sqlvirtualmachine_sql_virtual_machines_operations
    )

    with self.command_group('sqlvm',
                            sqlvm_vm_operations,
                            client_factory=get_sqlvirtualmachine_sql_virtual_machines_operations) as g:
        g.command('show', 'get')
        g.custom_command('list', 'sqlvm_list')
        g.command('delete', 'delete', confirmation=True)
        g.command('update', 'update')
        g.custom_command('create', 'sqlvm_create')

    ###############################################
    #      sql virtual machine groups             #
    ###############################################

    sqlvm_group_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations.sql_virtual_machine_groups_operations#SqlVirtualMachineGroupsOperations.{}',
        client_factory=get_sqlvirtualmachine_sql_virtual_machine_groups_operations
    )

    with self.command_group('sqlvm group',
                            sqlvm_group_operations,
                            client_factory=get_sqlvirtualmachine_sql_virtual_machine_groups_operations) as g:
        g.command('show', 'get', transform=transform_sqlvm_group_output)
        g.custom_command('list', 'sqlvm_list', transform=transform_sqlvm_group_list)
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('create', 'sqlvm_group_create', transform=transform_sqlvm_group_output)
        g.command('update', 'update')


    ###############################################
    #      availability group listener            #
    ###############################################

    sqlvm_agl_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations.availability_group_listeners_operations#AvailabilityGroupListenersOperations.{}',
        client_factory=get_sqlvirtualmachine_availability_group_listeners_operations
    )

    with self.command_group('sqlvm aglistener',
                            sqlvm_agl_operations,
                            client_factory=get_sqlvirtualmachine_availability_group_listeners_operations) as g:
        g.command('show', 'get')
        g.command('list', 'list_by_group')
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('create', 'sqlvm_aglistener_create')


