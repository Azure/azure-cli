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
cli_command(command_table, 'vm create', VMOperations.create_or_update, DeploymentOutputLongRunningOperation('Creating virtual machine'), factory)

factory = lambda _: _compute_client_factory().virtual_machines
cli_command(command_table, 'vm delete', VirtualMachinesOperations.delete, LongRunningOperation('Deleting VM'), factory)
cli_command(command_table, 'vm deallocate', VirtualMachinesOperations.deallocate, LongRunningOperation('Deallocating VM'), factory)
cli_command(command_table, 'vm generalize', VirtualMachinesOperations.generalize, None, factory)
cli_command(command_table, 'vm show', VirtualMachinesOperations.get, 'VirtualMachine', factory)
cli_command(command_table, 'vm list-sizes', VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]', factory)
cli_command(command_table, 'vm power-off', VirtualMachinesOperations.power_off, LongRunningOperation('Powering off VM'), factory)
cli_command(command_table, 'vm restart', VirtualMachinesOperations.restart, LongRunningOperation('Restarting VM'), factory)
cli_command(command_table, 'vm start', VirtualMachinesOperations.start, LongRunningOperation('Starting VM'), factory)
cli_command(command_table, 'vm list-ip-addresses', list_ip_addresses, 'object', factory)
cli_command(command_table, 'vm list', list_vm, '[VirtualMachine]')

# VM Access
cli_command(command_table, 'vm access set-linux-user', set_linux_user, LongRunningOperation('Setting Linux user'))
cli_command(command_table, 'vm access delete-linux-user', delete_linux_user, LongRunningOperation('Deleting Linux user'))
cli_command(command_table, 'vm access set-windows-user-password', set_windows_user_password, LongRunningOperation('Setting Windows user password'))

# VM Availability Set
factory = lambda _: get_mgmt_service_client(AvailSetClient, AvailSetClientConfig).avail_set
cli_command(command_table, 'vm availability-set create', AvailSetOperations.create_or_update, LongRunningOperation('Creating availability set'), factory)

factory = lambda _: _compute_client_factory().availability_sets
cli_command(command_table, 'vm availability-set delete', AvailabilitySetsOperations.delete, None, factory)
cli_command(command_table, 'vm availability-set show', AvailabilitySetsOperations.get, 'AvailabilitySet', factory)
cli_command(command_table, 'vm availability-set list', AvailabilitySetsOperations.list, '[AvailabilitySet]', factory)
cli_command(command_table, 'vm availability-set list-sizes', AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]', factory)

# VM Boot Diagnostics
cli_command(command_table, 'vm boot-diagnostics disable', disable_boot_diagnostics, None)
cli_command(command_table, 'vm boot-diagnostics enable', enable_boot_diagnostics, None)
cli_command(command_table, 'vm boot-diagnostics get-boot-log', get_boot_log, None)

# VM Container (ACS)
factory = lambda _: get_mgmt_service_client(ACSClient, ACSClientConfig).acs
cli_command(command_table, 'vm container create', ACSOperations.create_or_update, DeploymentOutputLongRunningOperation('Creating container'), factory)

# VM Diagnostics
cli_command(command_table, 'vm diagnostics set', set_diagnostics_extension, LongRunningOperation('Setting VM diagnostics extension'))
cli_command(command_table, 'vm diagnostics get-default-config', show_default_diagnostics_configuration, 'Object')

# VM Disk
cli_command(command_table, 'vm disk attach-new', attach_new_disk, 'object')
cli_command(command_table, 'vm disk attach-existing', attach_existing_disk, 'object')
cli_command(command_table, 'vm disk attach-detach', detach_disk, 'object')
cli_command(command_table, 'vm disk list', list_disks, '[VMDisk]')

# VM Extension
factory = lambda _: _compute_client_factory().virtual_machine_extensions
cli_command(command_table, 'vm extension delete', VirtualMachineExtensionsOperations.delete, LongRunningOperation('Deleting VM extension'), factory)
cli_command(command_table, 'vm extension show', VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension', factory)
cli_command(command_table, 'vm extension set', set_extension, LongRunningOperation('Setting VM extension'))
cli_command(command_table, 'vm extension list', list_extensions, '[Extensions]')

# VM Extension Image
factory = lambda _: _compute_client_factory().virtual_machine_extension_images
cli_command(command_table, 'vm extension image show', VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage', factory)
cli_command(command_table, 'vm extension image list-names', VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]', factory)
cli_command(command_table, 'vm extension image list-versions', VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]', factory)
cli_command(command_table, 'vm extension image list', list_vm_extension_images, '[VirtualMachineExtensionImage]')

# VM Image
factory = lambda _: _compute_client_factory().virtual_machine_images
cli_command(command_table, 'vm image show', VirtualMachineImagesOperations.get, 'VirtualMachineImage', factory)
cli_command(command_table, 'vm image list-offers', VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]', factory)
cli_command(command_table, 'vm image list-publishers', VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]', factory)
cli_command(command_table, 'vm image list-skus', VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]', factory)
cli_command(command_table, 'vm image list', list_vm_images, 'object')

# VM Usage
factory = lambda _: _compute_client_factory().usage
cli_command(command_table, 'vm usage list', UsageOperations.list, '[Usage]', factory)

# VM ScaleSet
factory = lambda _: get_mgmt_service_client(VMSSClient, VMSSClientConfig).vmss
cli_command(command_table, 'vm scaleset create', VMSSOperations.create_or_update, DeploymentOutputLongRunningOperation('Creating VM scaleset'), factory)

factory = lambda _: _compute_client_factory().virtual_machine_scale_sets
cli_command(command_table, 'vm scaleset deallocate', VirtualMachineScaleSetsOperations.deallocate, LongRunningOperation('Deallocating VM scaleset'), factory)
cli_command(command_table, 'vm scaleset delete', VirtualMachineScaleSetsOperations.delete, LongRunningOperation('Deleting VM scaleset'), factory)
cli_command(command_table, 'vm scaleset show ', VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet', factory)
cli_command(command_table, 'vm scaleset delete-instances', VirtualMachineScaleSetsOperations.delete_instances, LongRunningOperation('Deleting VM scaleset instances'), factory)
cli_command(command_table, 'vm scaleset get-instance-view', VirtualMachineScaleSetsOperations.get_instance_view, 'VirtualMachineScaleSetInstanceView', factory)
cli_command(command_table, 'vm scaleset list', VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]', factory)
cli_command(command_table, 'vm scaleset list-all', VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]', factory)
cli_command(command_table, 'vm scaleset list-skus', VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]', factory)
cli_command(command_table, 'vm scaleset power-off', VirtualMachineScaleSetsOperations.power_off, LongRunningOperation('Powering off VM scaleset'), factory)
cli_command(command_table, 'vm scaleset restart', VirtualMachineScaleSetsOperations.restart, LongRunningOperation('Restarting VM scaleset'), factory)
cli_command(command_table, 'vm scaleset start', VirtualMachineScaleSetsOperations.start, LongRunningOperation('Starting VM scaleset'), factory)
cli_command(command_table, 'vm scaleset update-instances', VirtualMachineScaleSetsOperations.update_instances, LongRunningOperation('Updating instances in VM scaleset'), factory)

# VM ScaleSet VMs
factory = lambda _: _compute_client_factory().virtual_machine_scale_set_vms
cli_command(command_table, 'vm scaleset-vm deallocate', VirtualMachineScaleSetVMsOperations.deallocate, LongRunningOperation('Deallocating scaleset VM'), factory)
cli_command(command_table, 'vm scaleset-vm delete', VirtualMachineScaleSetVMsOperations.delete, LongRunningOperation('Deleting scaleset VM'), factory)
cli_command(command_table, 'vm scaleset-vm show', VirtualMachineScaleSetVMsOperations.get, 'VirtualMachineScaleSetVM', factory)
cli_command(command_table, 'vm scaleset-vm get-instance-view', VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView', factory)
cli_command(command_table, 'vm scaleset-vm list', VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]', factory)
cli_command(command_table, 'vm scaleset-vm power-off', VirtualMachineScaleSetVMsOperations.power_off, LongRunningOperation('Powering off scaleset VM'), factory)
cli_command(command_table, 'vm scaleset-vm restart', VirtualMachineScaleSetVMsOperations.restart, LongRunningOperation('Restarting scaleset VM'), factory)
cli_command(command_table, 'vm scaleset-vm start', VirtualMachineScaleSetVMsOperations.start, LongRunningOperation('Starting scaleset VM'), factory)

# VM Size
factory = lambda _: _compute_client_factory().virtual_machine_sizes
cli_command(command_table, 'vm size list', VirtualMachineSizesOperations.list, '[VirtualMachineSize]', factory)
