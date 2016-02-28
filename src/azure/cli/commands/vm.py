import azure.mgmt.compute

from ._command_creation import get_service_client

from ..commands import _auto_command
from .._profile import Profile

def _compute_client_factory():
    return get_service_client(azure.mgmt.compute.ComputeManagementClient, azure.mgmt.compute.ComputeManagementClientConfiguration)
                
_auto_command._operation_builder("vm",
                   "availabilityset",
                   "availability_sets",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.AvailabilitySetsOperations.delete, None),
                    (azure.mgmt.compute.operations.AvailabilitySetsOperations.get, 'AvailabilitySet'),
                    (azure.mgmt.compute.operations.AvailabilitySetsOperations.list, '[AvailabilitySet]'),
                    (azure.mgmt.compute.operations.AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]')
                    ])


_auto_command._operation_builder("vm",
                   "machineextensionimages",
                   "virtual_machine_extension_images",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage'),
                    (azure.mgmt.compute.operations.VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]'),
                    (azure.mgmt.compute.operations.VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]'),
                    ])

_auto_command._operation_builder("vm",
                   "extensions",
                   "virtual_machine_extensions",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.VirtualMachineExtensionsOperations.delete, None),
                    (azure.mgmt.compute.operations.VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension'),
                    ])

_auto_command._operation_builder("vm",
                   "image",
                   "virtual_machine_images",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.VirtualMachineImagesOperations.get, 'VirtualMachineImage'),
                    (azure.mgmt.compute.operations.VirtualMachineImagesOperations.list, '[VirtualMachineImageResource]'),
                    (azure.mgmt.compute.operations.VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]'),
                    (azure.mgmt.compute.operations.VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]'),
                    (azure.mgmt.compute.operations.VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]'),
                    ])

_auto_command._operation_builder("vm",
                   "usage",
                   "usage",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.UsageOperations.list, '[Usage]'),
                    ])

_auto_command._operation_builder("vm",
                   "size",
                   "virtual_machine_sizes",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.VirtualMachineSizesOperations.list, '[VirtualMachineSize]'),
                    ])

_auto_command._operation_builder("vm",
                   "",
                   "virtual_machines",
                    _compute_client_factory,
                    [
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.delete, None),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.deallocate, None),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.generalize, None),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.get, 'VirtualMachine'),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.list, '[VirtualMachine]'),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.list_all, '[VirtualMachine]'),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]'),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.power_off, None),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.restart, None),
                    (azure.mgmt.compute.operations.VirtualMachinesOperations.start, None),
                    ])

_auto_command._operation_builder("vm",
                "scaleset",
                "virtual_machine_scale_sets",
                _compute_client_factory,
                [
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.deallocate, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.delete, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.delete_instances, None), 
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.get_instance_view, 'VirtualMachineScaleSetInstanceView'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.power_off, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.restart, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.start, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.update_instances, None),
                ])

_auto_command._operation_builder("vm",
                "vmscaleset",
                "virtual_machine_scale_set_vms",
                _compute_client_factory,
                [
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.deallocate, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.delete, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.get, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]'),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.power_off, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.restart, None),
                (azure.mgmt.compute.operations.VirtualMachineScaleSetVMsOperations.start, None),
                ])