from azure.mgmt.compute.operations import (AvailabilitySetsOperations,
                                           VirtualMachineExtensionImagesOperations,
                                           VirtualMachineExtensionsOperations,
                                           VirtualMachineImagesOperations,
                                           UsageOperations,
                                           VirtualMachineSizesOperations,
                                           VirtualMachinesOperations,
                                           VirtualMachineScaleSetsOperations,
                                           VirtualMachineScaleSetVMsOperations)
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L

from ._params import PARAMETER_ALIASES
from .custom import ConvenienceVmCommands, _compute_client_factory

command_table = CommandTable()

def _patch_aliases(alias_items):
    aliases = PARAMETER_ALIASES.copy()
    aliases.update(alias_items)
    return aliases

# pylint: disable=line-too-long
build_operation("vm availset",
                "availability_sets",
                _compute_client_factory,
                [
                    AutoCommandDefinition(AvailabilitySetsOperations.delete, None),
                    AutoCommandDefinition(AvailabilitySetsOperations.get, 'AvailabilitySet', command_alias='show'),
                    AutoCommandDefinition(AvailabilitySetsOperations.list, '[AvailabilitySet]'),
                    AutoCommandDefinition(AvailabilitySetsOperations.list_available_sizes, '[VirtualMachineSize]', 'list-sizes')
                ],
                command_table,
                _patch_aliases({
                    'availability_set_name': {'name': '--name -n'}
                }))

build_operation("vm machine-extension-image",
                "virtual_machine_extension_images",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineExtensionImagesOperations.get, 'VirtualMachineExtensionImage', command_alias='show'),
                    AutoCommandDefinition(VirtualMachineExtensionImagesOperations.list_types, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineExtensionImagesOperations.list_versions, '[VirtualMachineImageResource]'),
                ],
                command_table, PARAMETER_ALIASES)

build_operation("vm extension",
                "virtual_machine_extensions",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineExtensionsOperations.delete, LongRunningOperation(L('Deleting VM extension'), L('VM extension deleted'))),
                    AutoCommandDefinition(VirtualMachineExtensionsOperations.get, 'VirtualMachineExtension', command_alias='show'),
                ],
                command_table,
                _patch_aliases({
                    'vm_extension_name': {'name': '--name -n'}
                }))

build_operation("vm image",
                "virtual_machine_images",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineImagesOperations.get, 'VirtualMachineImage', command_alias='show'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list_offers, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list_publishers, '[VirtualMachineImageResource]'),
                    AutoCommandDefinition(VirtualMachineImagesOperations.list_skus, '[VirtualMachineImageResource]'),
                ],
                command_table, PARAMETER_ALIASES)

build_operation("vm usage",
                "usage",
                _compute_client_factory,
                [
                    AutoCommandDefinition(UsageOperations.list, '[Usage]'),
                ],
                command_table, PARAMETER_ALIASES)

build_operation("vm size",
                "virtual_machine_sizes",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineSizesOperations.list, '[VirtualMachineSize]'),
                ],
                command_table, PARAMETER_ALIASES)

build_operation("vm",
                "virtual_machines",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachinesOperations.delete, LongRunningOperation(L('Deleting VM'), L('VM Deleted'))),
                    AutoCommandDefinition(VirtualMachinesOperations.deallocate, LongRunningOperation(L('Deallocating VM'), L('VM Deallocated'))),
                    AutoCommandDefinition(VirtualMachinesOperations.generalize, None),
                    AutoCommandDefinition(VirtualMachinesOperations.get, 'VirtualMachine', command_alias='show'),
                    AutoCommandDefinition(VirtualMachinesOperations.list_available_sizes, '[VirtualMachineSize]', 'list-sizes'),
                    AutoCommandDefinition(VirtualMachinesOperations.power_off, LongRunningOperation(L('Powering off VM'), L('VM powered off'))),
                    AutoCommandDefinition(VirtualMachinesOperations.restart, LongRunningOperation(L('Restarting VM'), L('VM Restarted'))),
                    AutoCommandDefinition(VirtualMachinesOperations.start, LongRunningOperation(L('Starting VM'), L('VM Started'))),
                ],
                command_table,
                _patch_aliases({
                    'vm_name': {'name': '--name -n'}
                }))

build_operation("vm scaleset",
                "virtual_machine_scale_sets",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.deallocate, LongRunningOperation(L('Deallocating VM scale set'), L('VM scale set deallocated'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.delete, LongRunningOperation(L('Deleting VM scale set'), L('VM scale set deleted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetsOperations.get, 'VirtualMachineScaleSet', command_alias='show'),
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
                command_table,
                _patch_aliases({
                    'vm_scale_set_name': {'name': '--name -n'}
                }))

build_operation("vm scaleset-vm",
                "virtual_machine_scale_set_vms",
                _compute_client_factory,
                [
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.deallocate, LongRunningOperation(L('Deallocating VM scale set VMs'), L('VM scale set VMs deallocated'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.delete, LongRunningOperation(L('Deleting VM scale set VMs'), L('VM scale set VMs deleted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.get, 'VirtualMachineScaleSetVM', command_alias='show'),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.get_instance_view, 'VirtualMachineScaleSetVMInstanceView'),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.list, '[VirtualMachineScaleSetVM]'),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.power_off, LongRunningOperation(L('Powering off VM scale set VMs'), L('VM scale set VMs powered off'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.restart, LongRunningOperation(L('Restarting VM scale set VMs'), L('VM scale set VMs restarted'))),
                    AutoCommandDefinition(VirtualMachineScaleSetVMsOperations.start, LongRunningOperation(L('Starting VM scale set VMs'), L('VM scale set VMs started'))),
                ],
                command_table,
                _patch_aliases({
                    'vm_scale_set_name': {'name': '--name -n'}
                }))

build_operation("vm",
                None,
                ConvenienceVmCommands,
                [
                    AutoCommandDefinition(ConvenienceVmCommands.list_ip_addresses, 'object'),
                ],
                command_table, PARAMETER_ALIASES)
