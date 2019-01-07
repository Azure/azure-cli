# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.tools import resource_id, is_valid_resource_id
from azure.cli.core.util import CLIError
from azure.cli.core.commands.client_factory import get_subscription_id


# pylint: disable=too-many-statements,line-too-long
def validate_sqlvm_group(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the group is in the same resource group.
    '''
    group = namespace.sql_virtual_machine_group_resource_id

    if group and not is_valid_resource_id(group):
        namespace.sql_virtual_machine_group_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.SqlVirtualMachine', type='sqlVirtualMachineGroups',
            name=group
        )


# pylint: disable=too-many-statements,line-too-long
def validate_sqlvm_list(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the vm is in the same resource group.
    '''
    vms = namespace.sql_virtual_machine_instances

    for n, sqlvm in enumerate(vms):
        if sqlvm and not is_valid_resource_id(sqlvm):
            # add the correct resource id
            namespace.sql_virtual_machine_instances[n] = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.SqlVirtualMachine', type='sqlVirtualMachines',
                name=sqlvm
            )


# pylint: disable=too-many-statements,line-too-long
def _prompt_for_password(namespace):
    from knack.prompting import prompt_pass, NoTTYException
    try:
        namespace.admin_password = prompt_pass('Admin Password: ', confirm=True)
    except NoTTYException:
        raise CLIError('Please specify password in non-interactive mode.')


# pylint: disable=too-many-statements,line-too-long
def _prompt_for_key(namespace):
    from knack.prompting import prompt_pass, NoTTYException
    try:
        namespace.storage_account_key = prompt_pass('Storage key: ')
    except NoTTYException:
        raise CLIError('Please specify storage account key in non-interactive mode.')
