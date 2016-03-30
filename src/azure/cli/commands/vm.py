from .._locale import L
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

from ._command_creation import get_mgmt_service_client
from ..commands._auto_command import build_operation
from ..commands import CommandTable, LongRunningOperation

def _compute_client_factory():
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

command_table = CommandTable()

# pylint: disable=line-too-long
build_operation("vm availabilityset",
                "availability_sets",
                _compute_client_factory,
                [
                    (AvailabilitySetsOperations.delete, None),
                    (AvailabilitySetsOperations.get, 'AvailabilitySet'),
                    (AvailabilitySetsOperations.list, '[AvailabilitySet]'),
                    (AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]')
                ],
                command_table)


build_operation("vm machineextensionimage",
                "virtual_machine_extension_images",
                _compute_client_factory,
                [
                    (VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage'),
                    (VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]'),
                    (VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]'),
                ],
                command_table)

build_operation("vm extension",
                "virtual_machine_extensions",
                _compute_client_factory,
                [
                    (VirtualMachineExtensionsOperations.delete, LongRunningOperation(L('Deleting VM extension'), L('VM extension deleted'))),
                    (VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension'),
                ],
                command_table)

build_operation("vm image",
                "virtual_machine_images",
                _compute_client_factory,
                [
                    (VirtualMachineImagesOperations.get, 'VirtualMachineImage'),
                    (VirtualMachineImagesOperations.list, '[VirtualMachineImageResource]'),
                    (VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]'),
                    (VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]'),
                    (VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]'),
                ],
                command_table)

build_operation("vm usage",
                "usage",
                _compute_client_factory,
                [
                    (UsageOperations.list, '[Usage]'),
                ],
                command_table)

build_operation("vm size",
                "virtual_machine_sizes",
                _compute_client_factory,
                [
                    (VirtualMachineSizesOperations.list, '[VirtualMachineSize]'),
                ],
                command_table)

build_operation("vm",
                "virtual_machines",
                _compute_client_factory,
                [
                    (VirtualMachinesOperations.delete, LongRunningOperation(L('Deleting VM'), L('VM Deleted'))),
                    (VirtualMachinesOperations.deallocate, LongRunningOperation(L('Deallocating VM'), L('VM Deallocated'))),
                    (VirtualMachinesOperations.generalize, None),
                    (VirtualMachinesOperations.get, 'VirtualMachine'),
                    (VirtualMachinesOperations.list, '[VirtualMachine]'),
                    (VirtualMachinesOperations.list_all, '[VirtualMachine]'),
                    (VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]'),
                    (VirtualMachinesOperations.power_off, LongRunningOperation(L('Powering off VM'), L('VM powered off'))),
                    (VirtualMachinesOperations.restart, LongRunningOperation(L('Restarting VM'), L('VM Restarted'))),
                    (VirtualMachinesOperations.start, LongRunningOperation(L('Starting VM'), L('VM Started'))),
                ],
                command_table)

build_operation("vm scaleset",
                "virtual_machine_scale_sets",
                _compute_client_factory,
                [
                    (VirtualMachineScaleSetsOperations.deallocate, LongRunningOperation(L('Deallocating VM scale set'), L('VM scale set deallocated'))),
                    (VirtualMachineScaleSetsOperations.delete, LongRunningOperation(L('Deleting VM scale set'), L('VM scale set deleted'))),
                    (VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet'),
                    (VirtualMachineScaleSetsOperations.delete_instances, LongRunningOperation(L('Deleting VM scale set instances'), L('VM scale set instances deleted'))),
                    (VirtualMachineScaleSetsOperations.get_instance_view, 'VirtualMachineScaleSetInstanceView'),
                    (VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]'),
                    (VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]'),
                    (VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]'),
                    (VirtualMachineScaleSetsOperations.power_off, LongRunningOperation(L('Powering off VM scale set'), L('VM scale set powered off'))),
                    (VirtualMachineScaleSetsOperations.restart, LongRunningOperation(L('Restarting VM scale set'), L('VM scale set restarted'))),
                    (VirtualMachineScaleSetsOperations.start, LongRunningOperation(L('Starting VM scale set'), L('VM scale set started'))),
                    (VirtualMachineScaleSetsOperations.update_instances, LongRunningOperation(L('Updating VM scale set instances'), L('VM scale set instances updated'))),
                ],
                command_table)

build_operation("vm scalesetvm",
                "virtual_machine_scale_set_vms",
                _compute_client_factory,
                [
                    (VirtualMachineScaleSetVMsOperations.deallocate, LongRunningOperation(L('Deallocating VM scale set VMs'), L('VM scale set VMs deallocated'))),
                    (VirtualMachineScaleSetVMsOperations.delete, LongRunningOperation(L('Deleting VM scale set VMs'), L('VM scale set VMs deleted'))),
                    (VirtualMachineScaleSetVMsOperations.get, 'VirtualMachineScaleSetVM'),
                    (VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView'),
                    (VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]'),
                    (VirtualMachineScaleSetVMsOperations.power_off, LongRunningOperation(L('Powering off VM scale set VMs'), L('VM scale set VMs powered off'))),
                    (VirtualMachineScaleSetVMsOperations.restart, LongRunningOperation(L('Restarting VM scale set VMs'), L('VM scale set VMs restarted'))),
                    (VirtualMachineScaleSetVMsOperations.start, LongRunningOperation(L('Starting VM scale set VMs'), L('VM scale set VMs started'))),
                ],
                command_table)

