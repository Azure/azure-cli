# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_three_state_flag,
)


def load_arguments(self, _):
    project_name_type = CLIArgumentType(
        options_list=['--project-name'],
        help='Name of the Azure Migrate project.',
        id_part='name'
    )

    subscription_id_type = CLIArgumentType(
        options_list=['--subscription-id'],
        help='Azure subscription ID. Uses the default subscription if not '
             'specified.'
    )

    with self.argument_context('migrate') as c:
        c.argument('subscription_id', subscription_id_type)

    with self.argument_context('migrate local get-discovered-server') as c:
        c.argument('project_name', project_name_type, required=True)
        c.argument(
            'resource_group_name',
            options_list=['--resource-group-name', '--resource-group', '-g'],
            help='Name of the resource group containing the Azure Migrate '
                 'project.',
            required=True)
        c.argument(
            'display_name',
            help='Display name of the source machine to filter by.')
        c.argument('source_machine_type',
                   arg_type=get_enum_type(['VMware', 'HyperV']),
                   help='Type of the source machine.')
        c.argument('subscription_id', subscription_id_type)
        c.argument(
            'name',
            help='Internal name of the specific source machine to retrieve.')
        c.argument(
            'appliance_name',
            help='Name of the appliance (site) containing the machines.')

    with self.argument_context('migrate local replication init') as c:
        c.argument(
            'resource_group_name',
            options_list=['--resource-group-name', '--resource-group', '-g'],
            help='Specifies the Resource Group of the Azure Migrate '
                 'Project.',
            required=True)
        c.argument(
            'project_name',
            project_name_type,
            required=True,
            help='Specifies the name of the Azure Migrate project to be '
                 'used for server migration.')
        c.argument(
            'source_appliance_name',
            options_list=['--source-appliance-name'],
            help='Specifies the source appliance name for the AzLocal '
                 'scenario.',
            required=True)
        c.argument(
            'target_appliance_name',
            options_list=['--target-appliance-name'],
            help='Specifies the target appliance name for the AzLocal '
                 'scenario.',
            required=True)
        c.argument(
            'cache_storage_account_id',
            options_list=['--cache-storage-account-id',
                          '--cache-storage-id'],
            help='Specifies the Storage Account ARM Id to be used for '
                 'private endpoint scenario.')
        c.argument('subscription_id', subscription_id_type)
        c.argument(
            'pass_thru',
            options_list=['--pass-thru'],
            arg_type=get_three_state_flag(),
            help='Returns true when the command succeeds.')

    with self.argument_context('migrate local replication new') as c:
        c.argument(
            'machine_id',
            options_list=['--machine-id'],
            help='Specifies the machine ARM ID of the discovered server to '
                 'be migrated. Required if --machine-index is not provided.',
            required=False)
        c.argument(
            'machine_index',
            options_list=['--machine-index'],
            type=int,
            help='Specifies the index (1-based) of the discovered server '
                 'from the list. Required if --machine-id is not provided.')
        c.argument(
            'project_name',
            project_name_type,
            required=False,
            help='Name of the Azure Migrate project. Required when using '
                 '--machine-index.')
        c.argument(
            'resource_group_name',
            options_list=['--resource-group-name', '--resource-group', '-g'],
            help='Name of the resource group containing the Azure Migrate '
                 'project. Required when using --machine-index.')
        c.argument(
            'target_storage_path_id',
            options_list=['--target-storage-path-id'],
            help='Specifies the storage path ARM ID where the VMs will be '
                 'stored.',
            required=True)
        c.argument(
            'target_vm_cpu_core',
            options_list=['--target-vm-cpu-core'],
            type=int,
            help='Specifies the number of CPU cores.')
        c.argument(
            'target_virtual_switch_id',
            options_list=['--target-virtual-switch-id', '--network-id'],
            help='Specifies the logical network ARM ID that the VMs will '
                 'use.')
        c.argument(
            'target_test_virtual_switch_id',
            options_list=['--target-test-virtual-switch-id',
                          '--test-network-id'],
            help='Specifies the test logical network ARM ID that the VMs '
                 'will use.')
        c.argument(
            'is_dynamic_memory_enabled',
            options_list=['--is-dynamic-memory-enabled', '--dynamic-memory'],
            arg_type=get_enum_type(['true', 'false']),
            help='Specifies if RAM is dynamic or not.')
        c.argument(
            'target_vm_ram',
            options_list=['--target-vm-ram'],
            type=int,
            help='Specifies the target RAM size in MB.')
        c.argument(
            'disk_to_include',
            options_list=['--disk-to-include'],
            nargs='+',
            help='Specifies the disks on the source server to be included '
                 'for replication. Space-separated list of disk IDs.')
        c.argument(
            'nic_to_include',
            options_list=['--nic-to-include'],
            nargs='+',
            help='Specifies the NICs on the source server to be included '
                 'for replication. Space-separated list of NIC IDs.')
        c.argument(
            'target_resource_group_id',
            options_list=['--target-resource-group-id', '--target-rg-id'],
            help='Specifies the target resource group ARM ID where the '
                 'migrated VM resources will reside.',
            required=True)
        c.argument(
            'target_vm_name',
            options_list=['--target-vm-name'],
            help='Specifies the name of the VM to be created.',
            required=True)
        c.argument(
            'os_disk_id',
            options_list=['--os-disk-id'],
            help='Specifies the operating system disk for the source server '
                 'to be migrated.')
        c.argument(
            'source_appliance_name',
            options_list=['--source-appliance-name'],
            help='Specifies the source appliance name for the AzLocal '
                 'scenario.',
            required=True)
        c.argument(
            'target_appliance_name',
            options_list=['--target-appliance-name'],
            help='Specifies the target appliance name for the AzLocal '
                 'scenario.',
            required=True)
        c.argument('subscription_id', subscription_id_type)
