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

from azure.cli.commands._auto_command import build_operation, CommandDefinition
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
from azure.cli.command_modules.vm.mgmt_acs.lib import (ACSCreationClient as ACSClient,
                                                       ACSCreationClientConfiguration
                                                       as ACSClientConfig)
from azure.cli.command_modules.vm.mgmt_acs.lib.operations import ACSOperations

from ._params import (PARAMETER_ALIASES, VM_CREATE_EXTRA_PARAMETERS, VM_CREATE_PARAMETER_ALIASES,
                      VM_PATCH_EXTRA_PARAMETERS, ACS_CREATE_PARAMETER_ALIASES)
from ._factory import _compute_client_factory
from ._help import helps # pylint: disable=unused-import
from .custom import ConvenienceVmCommands, ConvinienceVmSSCommands

command_table = CommandTable()

# pylint: disable=line-too-long
build_operation(
    'vm availability-set', 'availability_sets', _compute_client_factory,
    [
        CommandDefinition(AvailabilitySetsOperations.delete, None),
        CommandDefinition(AvailabilitySetsOperations.get, 'AvailabilitySet', command_alias='show'),
        CommandDefinition(AvailabilitySetsOperations.list, '[AvailabilitySet]'),
        CommandDefinition(AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]', 'list-sizes')
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'availability_set_name': {'name': '--name -n'}
        }))

build_operation(
    'vm extension image', 'virtual_machine_extension_images', _compute_client_factory,
    [
        CommandDefinition(VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage', command_alias='show'),
        CommandDefinition(VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]', command_alias='list-names'),
        CommandDefinition(VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]'),
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'publisher_name': {'name': '--publisher'},
        'type': {'name': '--name -n'},
        'latest': {'action': 'store_true'}
        }))

build_operation(
    'vm disk', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.attach_new_disk, 'Object', 'attach-new'),
        CommandDefinition(ConvenienceVmCommands.attach_existing_disk, 'Object', 'attach-existing'),
        CommandDefinition(ConvenienceVmCommands.detach_disk, 'Object', 'detach'),
        CommandDefinition(ConvenienceVmCommands.list_disks, '[VMDisk]', 'list'),
    ],
    command_table, PARAMETER_ALIASES, VM_PATCH_EXTRA_PARAMETERS)

build_operation(
    'vm boot-diagnostics', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.disable_boot_diagnostics, None, 'disable'),
        CommandDefinition(ConvenienceVmCommands.enable_boot_diagnostics, None, 'enable'),
        CommandDefinition(ConvenienceVmCommands.get_boot_log, None)
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'vm_name': {'name': '--name -n'}
        }))

build_operation(
    'vm diagnostics', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.set_diagnostics_extension, LongRunningOperation(L('Setting extension'), L('Extension was set')), command_alias='set'),
        CommandDefinition(ConvenienceVmCommands.show_default_diagnostics_configuration, 'Object', command_alias='get-default-config'),
    ],
    command_table, PARAMETER_ALIASES)

build_operation(
    'vm extension', 'virtual_machine_extensions', _compute_client_factory,
    [
        CommandDefinition(VirtualMachineExtensionsOperations.delete, LongRunningOperation(L('Deleting VM extension'), L('VM extension deleted'))),
        CommandDefinition(VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension', command_alias='show'),
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'vm_extension_name': {'name': '--name -n'}
        }))

build_operation(
    'vm extension', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.set_extension, LongRunningOperation(L('Setting extension'), L('Extension was set')), command_alias='set'),
        CommandDefinition(ConvenienceVmCommands.list_extensions, '[Extensions]', command_alias='list')
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'vm_extension_name': {'name': '--name -n'},
        'auto_upgrade_minor_version': {'action': 'store_true'}
        }))

build_operation(
    'vm image', 'virtual_machine_images', _compute_client_factory,
    [
        CommandDefinition(VirtualMachineImagesOperations.get, 'VirtualMachineImage', command_alias='show'),
        CommandDefinition(VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]'),
        CommandDefinition(VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]'),
        CommandDefinition(VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]'),
    ],
    command_table, PARAMETER_ALIASES)

build_operation(
    'vm usage', 'usage', _compute_client_factory,
    [
        CommandDefinition(UsageOperations.list, '[Usage]'),
    ],
    command_table, PARAMETER_ALIASES)

build_operation(
    'vm size', 'virtual_machine_sizes', _compute_client_factory,
    [
        CommandDefinition(VirtualMachineSizesOperations.list, '[VirtualMachineSize]'),
    ],
    command_table, PARAMETER_ALIASES)

build_operation(
    'vm', 'virtual_machines', _compute_client_factory,
    [
        CommandDefinition(VirtualMachinesOperations.delete, LongRunningOperation(L('Deleting VM'), L('VM Deleted'))),
        CommandDefinition(VirtualMachinesOperations.deallocate, LongRunningOperation(L('Deallocating VM'), L('VM Deallocated'))),
        CommandDefinition(VirtualMachinesOperations.generalize, None),
        CommandDefinition(VirtualMachinesOperations.get, 'VirtualMachine', command_alias='show'),
        CommandDefinition(VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]', 'list-sizes'),
        CommandDefinition(VirtualMachinesOperations.power_off, LongRunningOperation(L('Powering off VM'), L('VM powered off'))),
        CommandDefinition(VirtualMachinesOperations.restart, LongRunningOperation(L('Restarting VM'), L('VM Restarted'))),
        CommandDefinition(VirtualMachinesOperations.start, LongRunningOperation(L('Starting VM'), L('VM Started'))),
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'vm_name': {'name': '--name -n'}
        }))

build_operation(
    'vm', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.list_ip_addresses, 'object'),
        CommandDefinition(ConvenienceVmCommands.list, '[VirtualMachine]')
    ],
    command_table, PARAMETER_ALIASES)

class DeploymentOutputLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(DeploymentOutputLongRunningOperation, self).__call__(poller)
        return result.properties.outputs

build_operation(
    'vm', 'vm', lambda **_: get_mgmt_service_client(VMClient, VMClientConfig),
    [
        CommandDefinition(
            VMOperations.create_or_update,
            DeploymentOutputLongRunningOperation(L('Creating virtual machine'),
                                                 L('Virtual machine created')),
            'create')
    ],
    command_table, VM_CREATE_PARAMETER_ALIASES, VM_CREATE_EXTRA_PARAMETERS)

build_operation(
    'vm scaleset', None, lambda **_: get_mgmt_service_client(VMSSClient, VMSSClientConfig),
    [
        CommandDefinition(
            VMSSOperations.create_or_update,
            DeploymentOutputLongRunningOperation(L('Creating virtual machine scale set'),
                                                 L('Virtual machine scale set created')),
            'create')
    ],
    command_table, VM_CREATE_PARAMETER_ALIASES, VM_CREATE_EXTRA_PARAMETERS)

build_operation(
    'vm scaleset', 'virtual_machine_scale_sets', _compute_client_factory,
    [
        CommandDefinition(VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet', command_alias='show'),
        CommandDefinition(VirtualMachineScaleSetsOperations.delete, LongRunningOperation(L('Deleting VM scale set'), L('VM scale set deleted'))),
        CommandDefinition(VirtualMachineScaleSetsOperations.list, '[VirtualMachineScaleSet]'),
        CommandDefinition(VirtualMachineScaleSetsOperations.list_all, '[VirtualMachineScaleSet]'),
        CommandDefinition(VirtualMachineScaleSetsOperations.list_skus, '[VirtualMachineScaleSet]'),
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'virtual_machine_scale_set_name': {'name': '--name -n'},
        'vm_scale_set_name': {'name': '--name -n'},
        }))

build_operation(
    'vm scaleset', 'virtual_machine_scale_set_vms', _compute_client_factory,
    [
        CommandDefinition(VirtualMachineScaleSetVMsOperations.get, '[VirtualMachineScaleSetVM]', 'show-instance'),
        CommandDefinition(VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]', 'list-instances'),
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'virtual_machine_scale_set_name': {'name': '--name -n'},
        'vm_scale_set_name': {'name': '--name -n'},
        }))

build_operation(
    'vm scaleset', None, ConvinienceVmSSCommands,
    [
        CommandDefinition(ConvinienceVmSSCommands.deallocate, LongRunningOperation(L('Deallocating'), L('Deallocated'))),
        CommandDefinition(ConvinienceVmSSCommands.delete_instances, LongRunningOperation(L('Deleting VM instances'), L('VM instances deleted'))),
        CommandDefinition(ConvinienceVmSSCommands.get_instance_view, 'VirtualMachineScaleSetVMInstanceView'),
        CommandDefinition(ConvinienceVmSSCommands.power_off, LongRunningOperation(L('Powering off VM instances'), L('VM instances powered off'))),
        CommandDefinition(ConvinienceVmSSCommands.restart, LongRunningOperation(L('Restarting VM instances'), L('VM instances restarted'))),
        CommandDefinition(ConvinienceVmSSCommands.start, LongRunningOperation(L('Starting VM instances'), L('VM instances started'))),
        CommandDefinition(ConvinienceVmSSCommands.update_instances, LongRunningOperation(L('Updating VM scale set instances'), L('VM scale set instances updated'))),
        CommandDefinition(ConvinienceVmSSCommands.reimage, LongRunningOperation(L('Re-imaging VM scale set instances'), L('VM scale set instances re-imaged'))),
        CommandDefinition(ConvinienceVmSSCommands.scale, LongRunningOperation(L('Updating instance count'), L('Instance count was updated')))
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'virtual_machine_scale_set_name': {'name': '--name -n'},
        'vm_scale_set_name': {'name': '--name -n'},
        }))

build_operation(
    'vm image', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.list_vm_images, 'object', 'list')
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'image_location': {'name': '--location -l'}
        }))

build_operation(
    'vm extension image', None, ConvenienceVmCommands,
    [
        CommandDefinition(ConvenienceVmCommands.list_vm_extension_images, '[VirtualMachineExtensionImage]', 'list')
    ],
    command_table, patch_aliases(PARAMETER_ALIASES, {
        'image_location': {'name': '--location -l'}
        }))

build_operation("vm availability-set",
                'avail_set',
                lambda **_: get_mgmt_service_client(AvailSetClient, AvailSetClientConfig),
                [
                    CommandDefinition(AvailSetOperations.create_or_update,
                                      LongRunningOperation(L('Creating availability set'), L('Availability set created')),
                                      'create')
                ],
                command_table, patch_aliases(PARAMETER_ALIASES, {
                    'name': {'name': '--name -n'}
                    }))

build_operation('vm access',
                None,
                ConvenienceVmCommands,
                [
                    CommandDefinition(ConvenienceVmCommands.set_linux_user, LongRunningOperation(L('Setting Linux user'), L('Linux User was set'))),
                    CommandDefinition(ConvenienceVmCommands.delete_linux_user, LongRunningOperation(L('Deleting Linux user'), L('Linux User was deleted'))),
                    CommandDefinition(ConvenienceVmCommands.set_windows_user_password, LongRunningOperation(L('Setting Windows user password'), L('Password was resetted')))
                ],
                command_table,
                patch_aliases(PARAMETER_ALIASES, {
                    'username': {
                        'help': 'The user name',
                        'name': '--username -u'
                        },
                    'password': {
                        'help': 'The user password',
                        'name': '--password -p'
                        },
                    'vm_name': {
                        'name' : '--name -n'
                    }
                })
               )

build_operation(
    'vm container', 'acs', lambda **_: get_mgmt_service_client(ACSClient, ACSClientConfig),
    [
        CommandDefinition(
            ACSOperations.create_or_update,
            DeploymentOutputLongRunningOperation(L('Creating container service'),
                                                 L('Container service created')),
            'create')
    ],
    command_table, ACS_CREATE_PARAMETER_ALIASES)
