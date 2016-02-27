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

# TODO: VM UsageOperations

# TODO: VM SizeOperations

_auto_command._operation_builder("vm",
                   "operations",
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

if False:
    _auto_command._operation_builder("vm",
                   "scaleset",
                   "virtual_machine_scalesets",
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


# TODO: VirtualMachineScaleSetVMsOperations