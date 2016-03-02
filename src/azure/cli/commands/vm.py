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

from ._command_creation import get_service_client
from ..commands._auto_command import build_operation, LongRunningOperation

def _compute_client_factory():
    return get_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

# pylint: disable=line-too-long
build_operation("vm",
                "availabilityset",
                "availability_sets",
                _compute_client_factory,
                [
                    (AvailabilitySetsOperations.delete, None),
                    (AvailabilitySetsOperations.get, 'AvailabilitySet'),
                    (AvailabilitySetsOperations.list, '[AvailabilitySet]'),
                    (AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]')
                ])


build_operation("vm",
                "machineextensionimages",
                "virtual_machine_extension_images",
                _compute_client_factory,
                [
                    (VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage'),
                    (VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]'),
                    (VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]'),
                ])

build_operation("vm",
                "extensions",
                "virtual_machine_extensions",
                _compute_client_factory,
                [
                    (VirtualMachineExtensionsOperations.delete, None),
                    (VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension'),
                ])

build_operation("vm",
                "image",
                "virtual_machine_images",
                _compute_client_factory,
                [
                    (VirtualMachineImagesOperations.get, 'VirtualMachineImage'),
                    (VirtualMachineImagesOperations.list, '[VirtualMachineImageResource]'),
                    (VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]'),
                    (VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]'),
                    (VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]'),
                ])

build_operation("vm",
                "usage",
                "usage",
                _compute_client_factory,
                [
                    (UsageOperations.list, '[Usage]'),
                ])

build_operation("vm",
                "size",
                "virtual_machine_sizes",
                _compute_client_factory,
                [
                    (VirtualMachineSizesOperations.list, '[VirtualMachineSize]'),
                ])

build_operation("vm",
                "",
                "virtual_machines",
                _compute_client_factory,
                [
                    (VirtualMachinesOperations.delete, None),
                    (VirtualMachinesOperations.deallocate, None),
                    (VirtualMachinesOperations.generalize, None),
                    (VirtualMachinesOperations.get, 'VirtualMachine'),
                    (VirtualMachinesOperations.list, '[VirtualMachine]'),
                    (VirtualMachinesOperations.list_all, '[VirtualMachine]'),
                    (VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]'),
                    (VirtualMachinesOperations.power_off, None),
                    (VirtualMachinesOperations.restart, LongRunningOperation(L('Restarting VM'), L('VM Restarted'))),
                    (VirtualMachinesOperations.start, LongRunningOperation(L('Starting VM'), L('VM Started'))),
                ])

build_operation("vm",
                "scaleset",
                "virtual_machine_scale_sets",
                _compute_client_factory,
                [
                    (VirtualMachineScaleSetsOperations.deallocate, None),
                    (VirtualMachineScaleSetsOperations.delete, None),
                    (VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet'),
                    (VirtualMachineScaleSetsOperations.delete_instances, None),
                    (VirtualMachineScaleSetsOperations.get_instance_view, 'VirtualMachineScaleSetInstanceView'),
                    (VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]'),
                    (VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]'),
                    (VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]'),
                    (VirtualMachineScaleSetsOperations.power_off, None),
                    (VirtualMachineScaleSetsOperations.restart, None),
                    (VirtualMachineScaleSetsOperations.start, None),
                    (VirtualMachineScaleSetsOperations.update_instances, None),
                ])

build_operation("vm",
                "vmscaleset",
                "virtual_machine_scale_set_vms",
                _compute_client_factory,
                [
                    (VirtualMachineScaleSetVMsOperations.deallocate, None),
                    (VirtualMachineScaleSetVMsOperations.delete, None),
                    (VirtualMachineScaleSetVMsOperations.get, None),
                    (VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView'),
                    (VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]'),
                    (VirtualMachineScaleSetVMsOperations.power_off, None),
                    (VirtualMachineScaleSetVMsOperations.restart, None),
                    (VirtualMachineScaleSetVMsOperations.start, None),
                ])
