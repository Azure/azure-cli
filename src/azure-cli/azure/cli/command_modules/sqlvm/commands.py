# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.arm import deployment_validate_table_format, handle_template_based_exception

from ._format import (
    transform_sqlvm_group_output,
    transform_sqlvm_group_list,
    transform_sqlvm_output,
    transform_sqlvm_list,
    transform_aglistener_output,
    transform_aglistener_list
)

from ._util import (
    get_sqlvirtualmachine_availability_group_listeners_operations,
    get_sqlvirtualmachine_sql_virtual_machine_groups_operations,
    get_sqlvirtualmachine_sql_virtual_machines_operations,
)


# pylint: disable=too-many-statements,line-too-long,too-many-locals
def load_command_table(self, _):

    ###############################################
    #            sql virtual machine              #
    ###############################################

    sqlvm_vm_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations#SqlVirtualMachinesOperations.{}',
        client_factory=get_sqlvirtualmachine_sql_virtual_machines_operations
    )

    with self.command_group('sql vm',
                            sqlvm_vm_operations,
                            client_factory=get_sqlvirtualmachine_sql_virtual_machines_operations) as g:
        g.generic_update_command('update', custom_func_name='sqlvm_update', setter_name='begin_create_or_update', transform=transform_sqlvm_output)
        g.show_command('show', 'get', transform=transform_sqlvm_output)
        g.custom_command('list', 'sqlvm_list', transform=transform_sqlvm_list)
        g.custom_command('add-to-group', 'sqlvm_add_to_group', transform=transform_sqlvm_output)
        g.custom_command('remove-from-group', 'sqlvm_remove_from_group', transform=transform_sqlvm_output)
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('create', 'sqlvm_create', transform=transform_sqlvm_output, table_transformer=deployment_validate_table_format, exception_handler=handle_template_based_exception)
        g.command('delete', 'begin_delete', confirmation=True)
        g.command('start-assessment', 'begin_start_assessment')

    ###############################################
    #      sql virtual machine groups             #
    ###############################################

    sqlvm_group_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations#SqlVirtualMachineGroupsOperations.{}',
        client_factory=get_sqlvirtualmachine_sql_virtual_machine_groups_operations
    )

    with self.command_group('sql vm group',
                            sqlvm_group_operations,
                            client_factory=get_sqlvirtualmachine_sql_virtual_machine_groups_operations) as g:
        g.generic_update_command('update', custom_func_name='sqlvm_group_update', setter_name='begin_create_or_update', transform=transform_sqlvm_group_output)
        g.show_command('show', 'get', transform=transform_sqlvm_group_output)
        g.custom_command('list', 'sqlvm_group_list', transform=transform_sqlvm_group_list)
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('create', 'sqlvm_group_create', transform=transform_sqlvm_group_output, table_transformer=deployment_validate_table_format, exception_handler=handle_template_based_exception)

    ###############################################
    #      availability group listener            #
    ###############################################

    sqlvm_agl_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sqlvirtualmachine.operations#AvailabilityGroupListenersOperations.{}',
        client_factory=get_sqlvirtualmachine_availability_group_listeners_operations
    )

    with self.command_group('sql vm group ag-listener',
                            sqlvm_agl_operations,
                            client_factory=get_sqlvirtualmachine_availability_group_listeners_operations) as g:
        g.generic_update_command('update', custom_func_name='aglistener_update', setter_name='begin_create_or_update', transform=transform_aglistener_output)
        g.show_command('show', 'get', transform=transform_aglistener_output)
        g.command('list', 'list_by_group', transform=transform_aglistener_list)
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('create', 'sqlvm_aglistener_create', transform=transform_aglistener_output, table_transformer=deployment_validate_table_format, exception_handler=handle_template_based_exception)

    with self.command_group('sql vm', is_preview=True):
        pass
