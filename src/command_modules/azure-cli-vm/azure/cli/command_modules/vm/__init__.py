import argparse
from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration
from azure.mgmt.compute.operations import (AvailabilitySetsOperations,
                                           VirtualMachineExtensionImagesOperations,
                                           VirtualMachineExtensionsOperations,
                                           VirtualMachineImagesOperations,
                                           UsageOperations,
                                           VirtualMachineSizesOperations,
                                           VirtualMachinesOperations,
                                           VirtualMachineScaleSetsOperations,
                                           VirtualMachineScaleSetVMsOperations)

from azure.cli.command_modules.vm.mgmt.lib import (ResourceManagementClient as VMClient,
                                                   ResourceManagementClientConfiguration
                                                   as VMClientConfig)
from azure.cli.command_modules.vm.mgmt.lib.operations import VMOperations

from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L

def _compute_client_factory(_):
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

command_table = CommandTable()

# pylint: disable=line-too-long
build_operation("vm availabilityset",
                "availability_sets",
                _compute_client_factory,
                [
                    AutoCommandDefinition(AvailabilitySetsOperations.delete, None),
                    AutoCommandDefinition(AvailabilitySetsOperations.get, 'AvailabilitySet'),
                    AutoCommandDefinition(AvailabilitySetsOperations.list, '[AvailabilitySet]'),
                    AutoCommandDefinition(AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]', 'list-sizes')
                ],
                command_table)


build_operation("vm machineextensionimage",
                "virtual_machine_extension_images",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage'),
                    AutoCommandDefinition(VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]'),
                ],
                command_table)

build_operation("vm extension",
                "virtual_machine_extensions",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineExtensionsOperations.delete, LongRunningOperation(L('Deleting VM extension'), L('VM extension deleted'))),
                    AutoCommandDefinition(VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension'),
                ],
                command_table)

build_operation("vm image",
                "virtual_machine_images",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineImagesOperations.get, 'VirtualMachineImage'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]'),
                ],
                command_table)

build_operation("vm usage",
                "usage",
                _compute_client_factory,
                [
                    AutoCommandDefinition(UsageOperations.list, '[Usage]'),
                ],
                command_table)

build_operation("vm size",
                "virtual_machine_sizes",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineSizesOperations.list, '[VirtualMachineSize]'),
                ],
                command_table)

build_operation("vm",
                "virtual_machines",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachinesOperations.delete, LongRunningOperation(L('Deleting VM'), L('VM Deleted'))),
                    AutoCommandDefinition(VirtualMachinesOperations.deallocate, LongRunningOperation(L('Deallocating VM'), L('VM Deallocated'))),
                    AutoCommandDefinition(VirtualMachinesOperations.generalize, None),
                    AutoCommandDefinition(VirtualMachinesOperations.get, 'VirtualMachine'),
                    AutoCommandDefinition(VirtualMachinesOperations.list, '[VirtualMachine]'),
                    AutoCommandDefinition(VirtualMachinesOperations.list_all, '[VirtualMachine]'),
                    AutoCommandDefinition(VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]', 'list-sizes'),
                    AutoCommandDefinition(VirtualMachinesOperations.power_off, LongRunningOperation(L('Powering off VM'), L('VM powered off'))),
                    AutoCommandDefinition(VirtualMachinesOperations.restart, LongRunningOperation(L('Restarting VM'), L('VM Restarted'))),
                    AutoCommandDefinition(VirtualMachinesOperations.start, LongRunningOperation(L('Starting VM'), L('VM Started'))),
                ],
                command_table)

build_operation("vm scaleset",
                "virtual_machine_scale_sets",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.deallocate, LongRunningOperation(L('Deallocating VM scale set'), L('VM scale set deallocated'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.delete, LongRunningOperation(L('Deleting VM scale set'), L('VM scale set deleted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet'),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.delete_instances, LongRunningOperation(L('Deleting VM scale set instances'), L('VM scale set instances deleted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.get_instance_view, 'VirtualMachineScaleSetInstanceView'),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]'),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]'),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]'),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.power_off, LongRunningOperation(L('Powering off VM scale set'), L('VM scale set powered off'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.restart, LongRunningOperation(L('Restarting VM scale set'), L('VM scale set restarted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.start, LongRunningOperation(L('Starting VM scale set'), L('VM scale set started'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.update_instances, LongRunningOperation(L('Updating VM scale set instances'), L('VM scale set instances updated'))),
                ],
                command_table)

build_operation("vm scalesetvm",
                "virtual_machine_scale_set_vms",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.deallocate, LongRunningOperation(L('Deallocating VM scale set VMs'), L('VM scale set VMs deallocated'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.delete, LongRunningOperation(L('Deleting VM scale set VMs'), L('VM scale set VMs deleted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.get, 'VirtualMachineScaleSetVM'),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView'),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]'),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.power_off, LongRunningOperation(L('Powering off VM scale set VMs'), L('VM scale set VMs powered off'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.restart, LongRunningOperation(L('Restarting VM scale set VMs'), L('VM scale set VMs restarted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.start, LongRunningOperation(L('Starting VM scale set VMs'), L('VM scale set VMs started'))),
                ],
                command_table)

# BUG: waiting on https://github.com/Azure/azure-cli/issues/115 to remove these specific params
VM_SPECIFIC_PARAMS = {
    'deployment_parameter_os_value': {
        'name': '--os',
        'metavar': 'OS',
    },
    'deployment_parameter_os_publisher_value': {
        'name': '--os-publisher',
        'metavar': 'OSPUBLISHER',
    },
    'deployment_parameter_admin_password_value': {
        'name': '--admin-password',
        'metavar': 'ADMINPASSWORD'
    },
    'deployment_parameter_ip_address_type_value': {
        'name': '--ip-address-type',
        'metavar': 'IPADDRESSTYPE',
    },
    'deployment_parameter_storage_type_value': {
        'name': '--storage-type',
        'metavar': 'STORAGETYPE',
    },
    'deployment_parameter_size_value': {
        'name': '--size',
        'metavar': 'SIZE',
    },
    'deployment_parameter_admin_username_value': {
        'name': '--admin-username',
        'metavar': 'ADMINUSERNAME',
        'required': True
    },
    'deployment_parameter_dns_name_for_public_ip_value': {
        'name': '--dns-name-for-public-ip',
        'metavar': 'DNSNAMEFORPUBLICIP',
        'required': True
    },
    'deployment_parameter_ip_address_prefix_value': {
        'name': '--ip-address-prefix',
        'metavar': 'IPADDRESSPREFIX',
    },
    'deployment_parameter_virtual_machine_name_value': {
        'name': '--virtual-machine-name',
        'metavar': 'VIRTUALMACHINENAME',
        'required': True
    },
    'deployment_parameter_subnet_prefix_value': {
        'name': '--subnet-prefix',
        'metavar': 'SUBNETPREFIX',
    },
    'deployment_parameter_os_sku_value': {
        'name': '--os-sku',
        'metavar': 'OSSKU',
    },
    'deployment_parameter_os_offer_value': {
        'name': '--os-offer',
        'metavar': 'OSOFFER',
    },
    'deployment_parameter_os_version_value': {
        'name': '--os-version',
        'metavar': 'OSVERSION',
    },
    'deployment_parameter_authentication_method_value': {
        'name': '--authentication-method',
        'metavar': 'AUTHMETHOD',
    },
    'deployment_parameter_ssh_key_value_value': {
        'name': '--ssh-key-value',
        'metavar': 'SSHKEY',
    },
    'deployment_parameter_ssh_key_path_value': {
        'name': '--ssh-key-path',
        'metavar': 'SSHPATH',
    }
}

build_operation('vm',
                'vm',
                lambda _: get_mgmt_service_client(VMClient, VMClientConfig),
                [
                    AutoCommandDefinition(VMOperations.create_or_update,
                                          LongRunningOperation(L('Creating virtual machine'), L('Virtual machine created')),
                                          'create')
                ],
                command_table,
                VM_SPECIFIC_PARAMS)
