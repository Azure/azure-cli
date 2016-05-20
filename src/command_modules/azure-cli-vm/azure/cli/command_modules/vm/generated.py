from azure.mgmt.compute.operations import (AvailabilitySetsOperations,
                                           VirtualMachineExtensionImagesOperations,
                                           VirtualMachineExtensionsOperations,
                                           VirtualMachineImagesOperations,
                                           UsageOperations,
                                           VirtualMachineSizesOperations,
                                           VirtualMachinesOperations,
                                           VirtualMachineScaleSetsOperations,
                                           VirtualMachineScaleSetVMsOperations)
from azure.cli.commands._auto_command import build_operation, CommandDefinition, sdk_cli_command
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.commands import CommandTable, LongRunningOperation, patch_aliases
from azure.cli._locale import L
from azure.cli.command_modules.vm.mgmt_avail_set.lib import (AvailSetCreationClient
                                                             as AvailSetClient,
                                                             AvailSetCreationClientConfiguration
                                                             as AvailSetClientConfig)
from azure.cli.command_modules.vm.mgmt_avail_set.lib.operations import AvailSetOperations
from azure.cli.command_modules.vm.mgmt_vm_create.lib import (VMCreationClient as VMClient,
                                                             VMCreationClientConfiguration
                                                             as VMClientConfig)
from azure.cli.command_modules.vm.mgmt_vm_create.lib.operations import VMOperations
from azure.cli.command_modules.vm.mgmt_vmss_create.lib import (VMSSCreationClient as VMSSClient,
                                                               VMSSCreationClientConfiguration
                                                               as VMSSClientConfig)
from azure.cli.command_modules.vm.mgmt_vmss_create.lib.operations import VMSSOperations

from azure.cli.command_modules.vm._actions import VMImageFieldAction
from ._params import (PARAMETER_ALIASES, VM_CREATE_EXTRA_PARAMETERS, VM_CREATE_PARAMETER_ALIASES,
                      get_urn_aliases_completion_list, get_location_completion_list)
from ._factory import _compute_client_factory
from ._help import helps # pylint: disable=unused-import
from .custom import ConvenienceVmCommands

command_table = CommandTable()

# pylint: disable=line-too-long

factory = lambda **kwargs: _compute_client_factory(**kwargs).availability_sets
sdk_cli_command('vm availability-set delete', factory, AvailabilitySetsOperations.delete, None, command_table)
sdk_cli_command('vm availability-set show', factory, AvailabilitySetsOperations.get, 'AvailabilitySet', command_table)
sdk_cli_command('vm availability-set list', factory, AvailabilitySetsOperations.list, '[AvailabilitySet]', command_table)
sdk_cli_command('vm availability-set list-sizes', factory, AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).virtual_machine_extension_images
sdk_cli_command('vm machine-extension-image show', factory, VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage', command_table)
sdk_cli_command('vm machine-extension-image list-types', factory, VirtualMachineExtensionImagesOperations.list_types, 'VirtualMachineExtensionImage', command_table)
sdk_cli_command('vm machine-extension-image list-versions', factory, VirtualMachineExtensionImagesOperations.list_versions, 'VirtualMachineExtensionImage', command_table)

factory = ConvenienceVmCommands # TODO: Add good support for patch!
sdk_cli_command('vm disk attach-new', factory, ConvenienceVmCommands.attach_new_disk, 'object', command_table)
sdk_cli_command('vm disk attach-existing', factory, ConvenienceVmCommands.attach_existing_disk, 'object', command_table)
sdk_cli_command('vm disk attach-detach', factory, ConvenienceVmCommands.detach_disk, 'object', command_table)
sdk_cli_command('vm disk list', factory, ConvenienceVmCommands.list_disks, '[VMDisk]', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).virtual_machine_extensions
sdk_cli_command('vm extension delete', factory, VirtualMachineExtensionsOperations.delete, None, command_table)
sdk_cli_command('vm extension show', factory, VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).virtual_machine_extension_images
sdk_cli_command('vm extension image show', factory, VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage', command_table)
sdk_cli_command('vm extension image list-types', factory, VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]', command_table)
sdk_cli_command('vm extension image list-versions', factory, VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).virtual_machine_images
sdk_cli_command('vm image show', factory, VirtualMachineImagesOperations.get, 'VirtualMachineImage', command_table)
sdk_cli_command('vm image list-offers', factory, VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]', command_table)
sdk_cli_command('vm image list-publishers', factory, VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]', command_table)
sdk_cli_command('vm image list-skus', factory, VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).usage
sdk_cli_command('vm usage list', factory, UsageOperations.list, '[Usage]', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).virtual_machine_sizes
sdk_cli_command('vm size list', factory, VirtualMachineSizesOperations.list, '[VirtualMachineSize]', command_table)

factory = lambda **kwargs: _compute_client_factory(**kwargs).virtual_machines
sdk_cli_command('vm delete', factory, VirtualMachinesOperations.delete, None, command_table)
sdk_cli_command('vm deallocate', factory, VirtualMachinesOperations.deallocate, None, command_table)
sdk_cli_command('vm generalize', factory, VirtualMachinesOperations.generalize, None, command_table)
sdk_cli_command('vm show', factory, VirtualMachinesOperations.get, 'VirtualMachine', command_table)
sdk_cli_command('vm list-sizes', factory, VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]', command_table)
sdk_cli_command('vm power-off', factory, VirtualMachinesOperations.power_off, None, command_table)
sdk_cli_command('vm restart', factory, VirtualMachinesOperations.restart, None, command_table)
sdk_cli_command('vm start', factory, VirtualMachinesOperations.start, None, command_table)

factory = ConvenienceVmCommands # TODO: Make methods module level instead of class members (no need for wrapping in class anymore)
sdk_cli_command('vm list-ip-addresses', factory, ConvenienceVmCommands.list_ip_addresses, 'object', command_table)
sdk_cli_command('vm list', factory, ConvenienceVmCommands.list, '[VirtualMachine]', command_table)

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        return result.properties.outputs

factory = lambda **_: get_mgmt_service_client(VMClient, VMClientConfig).vm
vm_create_cmd = sdk_cli_command('vm create', factory, VMOperations.create_or_update, DeploymentOutputLongRunningOperation(), command_table)

factory = lambda **_: get_mgmt_service_client(VMSSClient, VMSSClientConfig).vmss
sdk_cli_command('vm scaleset create', factory, VMSSOperations.create_or_update, DeploymentOutputLongRunningOperation(), command_table)

# VM ScaleSet
factory = lambda **_: _compute_client_factory().virtual_machine_scale_sets
sdk_cli_command('vm scaleset deallocate', factory, VirtualMachineScaleSetsOperations.deallocate, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset delete', factory, VirtualMachineScaleSetsOperations.delete, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset show ', factory, VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet', command_table)
sdk_cli_command('vm scaleset delete-instances', factory, VirtualMachineScaleSetsOperations.delete_instances, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset get-instance-view', factory, VirtualMachineScaleSetsOperations.get_instance_view, 'VirtualMachineScaleSetInstanceView', command_table)
sdk_cli_command('vm scaleset list', factory, VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]', command_table)
sdk_cli_command('vm scaleset list-all', factory, VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]', command_table)
sdk_cli_command('vm scaleset list-skus', factory, VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]', command_table)
sdk_cli_command('vm scaleset power-off', factory, VirtualMachineScaleSetsOperations.power_off, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset restart', factory, VirtualMachineScaleSetsOperations.restart, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset start', factory, VirtualMachineScaleSetsOperations.start, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset update-instances', factory, VirtualMachineScaleSetsOperations.update_instances, LongRunningOperation(), command_table)

# VM ScaleSet VMs
factory = lambda **_: _compute_client_factory().virtual_machine_scale_set_vms
sdk_cli_command('vm scaleset-vm deallocate', factory, VirtualMachineScaleSetVMsOperations.deallocate, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset-vm delete', factory, VirtualMachineScaleSetVMsOperations.delete, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset-vm show', factory, VirtualMachineScaleSetVMsOperations.get, 'VirtualMachineScaleSetVM', command_table)
sdk_cli_command('vm scaleset-vm get-instance-view', factory, VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView', command_table)
sdk_cli_command('vm scaleset-vm list', factory, VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]', command_table)
sdk_cli_command('vm scaleset-vm power-off', factory, VirtualMachineScaleSetVMsOperations.power_off, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset-vm restart', factory, VirtualMachineScaleSetVMsOperations.restart, LongRunningOperation(), command_table)
sdk_cli_command('vm scaleset-vm start', factory, VirtualMachineScaleSetVMsOperations.start, LongRunningOperation(), command_table)


factory = lambda **_: get_mgmt_service_client(AvailSetClient, AvailSetClientConfig).avail_set
sdk_cli_command('vm availability-set create', factory, AvailSetOperations.create_or_update, LongRunningOperation(), command_table)

# Cool custom commands
sdk_cli_command('vm image list', ConvenienceVmCommands, ConvenienceVmCommands.list_vm_images, 'object', command_table)

sdk_cli_command('vm access set-linux-user', ConvenienceVmCommands, ConvenienceVmCommands.set_linux_user, LongRunningOperation(), command_table)
sdk_cli_command('vm access delete-linux-user', ConvenienceVmCommands, ConvenienceVmCommands.delete_linux_user, LongRunningOperation(), command_table)
sdk_cli_command('vm access set-windows-user-password', ConvenienceVmCommands, ConvenienceVmCommands.set_windows_user_password, LongRunningOperation(), command_table)
