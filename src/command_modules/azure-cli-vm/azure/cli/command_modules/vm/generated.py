from azure.mgmt.compute.operations import (
    AvailabilitySetsOperations,
    VirtualMachineExtensionImagesOperations,
    VirtualMachineExtensionsOperations,
    VirtualMachineImagesOperations,
    UsageOperations,
    VirtualMachineSizesOperations,
    VirtualMachinesOperations,
    VirtualMachineScaleSetsOperations,
    VirtualMachineScaleSetVMsOperations)
from azure.cli.commands import LongRunningOperation
from azure.cli.commands.command_types import cli_command
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.commands import CommandTable
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
from azure.cli.command_modules.vm.mgmt_acs.lib import (ACSCreationClient as ACSClient,
                                                       ACSCreationClientConfiguration
                                                       as ACSClientConfig)
from azure.cli.command_modules.vm.mgmt_acs.lib.operations import ACSOperations
from .custom import (
    list_vm, list_vm_images, list_vm_extension_images, list_ip_addresses, attach_new_disk,
    attach_existing_disk, detach_disk, list_disks, set_windows_user_password, set_linux_user,
    delete_linux_user, disable_boot_diagnostics, enable_boot_diagnostics, get_boot_log,
    list_extensions, set_extension, set_diagnostics_extension,
    show_default_diagnostics_configuration)

from ._factory import _compute_client_factory

command_table = CommandTable()

# pylint: disable=line-too-long

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        return result.properties.outputs

# VM
factory = lambda _: get_mgmt_service_client(VMClient, VMClientConfig).vm
cli_command(command_table, 'vm create', VMOperations.create_or_update, factory, return_type=DeploymentOutputLongRunningOperation('Starting vm create'))

factory = lambda _: _compute_client_factory().virtual_machines
cli_command(command_table, 'vm delete', VirtualMachinesOperations.delete, factory)
cli_command(command_table, 'vm deallocate', VirtualMachinesOperations.deallocate, factory)
cli_command(command_table, 'vm generalize', VirtualMachinesOperations.generalize, factory)
cli_command(command_table, 'vm show', VirtualMachinesOperations.get, factory)
cli_command(command_table, 'vm list-sizes', VirtualMachinesOperations.list_available_sizes, factory)
cli_command(command_table, 'vm power-off', VirtualMachinesOperations.power_off, factory)
cli_command(command_table, 'vm restart', VirtualMachinesOperations.restart, factory)
cli_command(command_table, 'vm start', VirtualMachinesOperations.start, factory)
cli_command(command_table, 'vm list-ip-addresses', list_ip_addresses, factory)
cli_command(command_table, 'vm list', list_vm)

# VM Access
cli_command(command_table, 'vm access set-linux-user', set_linux_user)
cli_command(command_table, 'vm access delete-linux-user', delete_linux_user)
cli_command(command_table, 'vm access set-windows-user-password', set_windows_user_password)

# VM Availability Set
factory = lambda _: get_mgmt_service_client(AvailSetClient, AvailSetClientConfig).avail_set
cli_command(command_table, 'vm availability-set create', AvailSetOperations.create_or_update, factory)

factory = lambda _: _compute_client_factory().availability_sets
cli_command(command_table, 'vm availability-set delete', AvailabilitySetsOperations.delete, factory)
cli_command(command_table, 'vm availability-set show', AvailabilitySetsOperations.get, factory)
cli_command(command_table, 'vm availability-set list', AvailabilitySetsOperations.list, factory)
cli_command(command_table, 'vm availability-set list-sizes', AvailabilitySetsOperations.list_available_sizes, factory)

# VM Boot Diagnostics
cli_command(command_table, 'vm boot-diagnostics disable', disable_boot_diagnostics)
cli_command(command_table, 'vm boot-diagnostics enable', enable_boot_diagnostics)
cli_command(command_table, 'vm boot-diagnostics get-boot-log', get_boot_log)

# VM Container (ACS)
factory = lambda _: get_mgmt_service_client(ACSClient, ACSClientConfig).acs
cli_command(command_table, 'vm container create', ACSOperations.create_or_update, factory, return_type=DeploymentOutputLongRunningOperation('Starting vm container create'))

# VM Diagnostics
cli_command(command_table, 'vm diagnostics set', set_diagnostics_extension)
cli_command(command_table, 'vm diagnostics get-default-config', show_default_diagnostics_configuration)

# VM Disk
cli_command(command_table, 'vm disk attach-new', attach_new_disk)
cli_command(command_table, 'vm disk attach-existing', attach_existing_disk)
cli_command(command_table, 'vm disk attach-detach', detach_disk)
cli_command(command_table, 'vm disk list', list_disks)

# VM Extension
factory = lambda _: _compute_client_factory().virtual_machine_extensions
cli_command(command_table, 'vm extension delete', VirtualMachineExtensionsOperations.delete, factory)
cli_command(command_table, 'vm extension show', VirtualMachineExtensionsOperations.get, factory)
cli_command(command_table, 'vm extension set', set_extension)
cli_command(command_table, 'vm extension list', list_extensions)

# VM Extension Image
factory = lambda _: _compute_client_factory().virtual_machine_extension_images
cli_command(command_table, 'vm extension image show', VirtualMachineExtensionImagesOperations.get, factory)
cli_command(command_table, 'vm extension image list-names', VirtualMachineExtensionImagesOperations.list_types, factory)
cli_command(command_table, 'vm extension image list-versions', VirtualMachineExtensionImagesOperations.list_versions, factory)
cli_command(command_table, 'vm extension image list', list_vm_extension_images)

# VM Image
factory = lambda _: _compute_client_factory().virtual_machine_images
cli_command(command_table, 'vm image show', VirtualMachineImagesOperations.get, factory)
cli_command(command_table, 'vm image list-offers', VirtualMachineImagesOperations.list_offers, factory)
cli_command(command_table, 'vm image list-publishers', VirtualMachineImagesOperations.list_publishers, factory)
cli_command(command_table, 'vm image list-skus', VirtualMachineImagesOperations.list_skus, factory)
cli_command(command_table, 'vm image list', list_vm_images)

# VM Usage
factory = lambda _: _compute_client_factory().usage
cli_command(command_table, 'vm usage list', UsageOperations.list, factory)

# VM ScaleSet
factory = lambda _: get_mgmt_service_client(VMSSClient, VMSSClientConfig).vmss
cli_command(command_table, 'vm scaleset create', VMSSOperations.create_or_update, factory, return_type=DeploymentOutputLongRunningOperation('Starting vm scaleset create'))

factory = lambda _: _compute_client_factory().virtual_machine_scale_sets
cli_command(command_table, 'vm scaleset deallocate', VirtualMachineScaleSetsOperations.deallocate, factory)
cli_command(command_table, 'vm scaleset delete', VirtualMachineScaleSetsOperations.delete, factory)
cli_command(command_table, 'vm scaleset show ', VirtualMachineScaleSetsOperations.get, factory)
cli_command(command_table, 'vm scaleset delete-instances', VirtualMachineScaleSetsOperations.delete_instances, factory)
cli_command(command_table, 'vm scaleset get-instance-view', VirtualMachineScaleSetsOperations.get_instance_view, factory)
cli_command(command_table, 'vm scaleset list', VirtualMachineScaleSetsOperations.list, factory)
cli_command(command_table, 'vm scaleset list-all', VirtualMachineScaleSetsOperations.list_all, factory)
cli_command(command_table, 'vm scaleset list-skus', VirtualMachineScaleSetsOperations.list_skus, factory)
cli_command(command_table, 'vm scaleset power-off', VirtualMachineScaleSetsOperations.power_off, factory)
cli_command(command_table, 'vm scaleset restart', VirtualMachineScaleSetsOperations.restart, factory)
cli_command(command_table, 'vm scaleset start', VirtualMachineScaleSetsOperations.start, factory)
cli_command(command_table, 'vm scaleset update-instances', VirtualMachineScaleSetsOperations.update_instances, factory)

# VM ScaleSet VMs
factory = lambda _: _compute_client_factory().virtual_machine_scale_set_vms
cli_command(command_table, 'vm scaleset-vm deallocate', VirtualMachineScaleSetVMsOperations.deallocate, factory)
cli_command(command_table, 'vm scaleset-vm delete', VirtualMachineScaleSetVMsOperations.delete, factory)
cli_command(command_table, 'vm scaleset-vm show', VirtualMachineScaleSetVMsOperations.get, factory)
cli_command(command_table, 'vm scaleset-vm get-instance-view', VirtualMachineScaleSetVMsOperations.get_instance_view, factory)
cli_command(command_table, 'vm scaleset-vm list', VirtualMachineScaleSetVMsOperations.list, factory)
cli_command(command_table, 'vm scaleset-vm power-off', VirtualMachineScaleSetVMsOperations.power_off, factory)
cli_command(command_table, 'vm scaleset-vm restart', VirtualMachineScaleSetVMsOperations.restart, factory)
cli_command(command_table, 'vm scaleset-vm start', VirtualMachineScaleSetVMsOperations.start, factory)

# VM Size
factory = lambda _: _compute_client_factory().virtual_machine_sizes
cli_command(command_table, 'vm size list', VirtualMachineSizesOperations.list, factory)
