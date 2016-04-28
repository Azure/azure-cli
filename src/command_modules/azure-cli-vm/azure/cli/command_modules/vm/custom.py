from azure.mgmt.compute.models import DataDisk
from azure.mgmt.compute.models.compute_management_client_enums import DiskCreateOptionTypes
from azure.cli._locale import L
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration

from ._params import PARAMETER_ALIASES

def _compute_client_factory(_):
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

command_table = CommandTable()

def vm_getter(args):
    ''' Retreive a VM based on the `args` passed in.
    '''
    client = _compute_client_factory(args)
    result = client.virtual_machines.get(args.get('resourcegroup'), args.get('vm_name'))
    return result

def vm_setter(args, instance, start_msg, end_msg):
    '''Update the given Virtual Machine instance
    '''
    instance.resources = None # Issue: https://github.com/Azure/autorest/issues/934
    client = _compute_client_factory(args)
    poller = client.virtual_machines.create_or_update(
        resource_group_name=args.get('resourcegroup'),
        vm_name=args.get('vm_name'),
        parameters=instance)
    return LongRunningOperation(start_msg, end_msg)(poller)

def patches_vm(start_msg, finish_msg):
    '''Decorator indicating that the decorated function modifies an existing Virtual Machine
    in Azure.
    It automatically adds arguments required to identify the Virtual Machine to be patched and
    handles the actual put call to the compute service, leaving the decorated function to only
    have to worry about the modifications it has to do.
    '''
    def wrapped(func):
        def invoke(args):
            instance = vm_getter(args)
            func(args, instance)
            vm_setter(args, instance, start_msg, finish_msg)

        # All Virtual Machines are identified with a resource group name/name pair, so
        # we add these parameters to all commands
        command_table[invoke]['arguments'].append(PARAMETER_ALIASES['resource_group_name'])
        command_table[invoke]['arguments'].append({
            'name': '--vm-name -n',
            'dest': 'vm_name',
            'help': 'Name of Virtual Machine to update',
            'required': True
            })
        return invoke
    return wrapped

@command_table.command('vm list', description=L('List Virtual Machines.'))
@command_table.option(**PARAMETER_ALIASES['optional_resource_group_name'])
def list_vm(args):
    ccf = _compute_client_factory(args)
    group = args.get('resourcegroup')
    vm_list = ccf.virtual_machines.list(resource_group_name=group) if group else \
              ccf.virtual_machines.list_all()
    return list(vm_list)

@command_table.command('vm disk attach-new',
                       help=L('Attach a new disk to an existing Virtual Machine'))
@command_table.option(**PARAMETER_ALIASES['lun'])
@command_table.option(**PARAMETER_ALIASES['diskname'])
@command_table.option(**PARAMETER_ALIASES['disksize'])
@command_table.option(**PARAMETER_ALIASES['vhd'])
@patches_vm('Attaching disk', 'Disk attached')
def _vm_disk_attach_new(args, instance):
    disk = DataDisk(lun=args.get('lun'),
                    vhd=args.get('vhd'),
                    name=args.get('name'),
                    create_option=DiskCreateOptionTypes.empty,
                    disk_size_gb=args.get('disksize'))
    instance.storage_profile.data_disks.append(disk)

@command_table.command('vm disk attach-existing',
                       help=L('Attach an existing disk to an existing Virtual Machine'))
@command_table.option(**PARAMETER_ALIASES['lun'])
@command_table.option(**PARAMETER_ALIASES['diskname'])
@command_table.option(**PARAMETER_ALIASES['disksize'])
@command_table.option(**PARAMETER_ALIASES['vhd'])
@patches_vm('Attaching disk', 'Disk attached')
def _vm_disk_attach_existing(args, instance):
    # TODO: figure out size of existing disk instead of making the default value 1023
    disk = DataDisk(lun=args.get('lun'),
                    vhd=args.get('vhd'),
                    name=args.get('name'),
                    create_option=DiskCreateOptionTypes.attach,
                    disk_size_gb=args.get('disksize'))
    instance.storage_profile.data_disks.append(disk)

@command_table.command('vm disk detach')
@command_table.option(**PARAMETER_ALIASES['diskname'])
@patches_vm('Detaching disk', 'Disk detached')
def _vm_disk_detach(args, instance):
    instance.resources = None # Issue: https://github.com/Azure/autorest/issues/934
    try:
        disk = next(d for d in instance.storage_profile.data_disks
                    if d.name == args.get('name'))
        instance.storage_profile.data_disks.remove(disk)
    except StopIteration:
        raise RuntimeError("No disk with the name '%s' found" % args.get('name'))

#
# Composite convenience commands for the CLI
#
def _parse_rg_name(strid):
    '''From an ID, extract the contained (resource group, name) tuple
    '''
    import re
    parts = re.split('/', strid)
    if parts[3] != 'resourceGroups':
        raise KeyError()

    return (parts[4], parts[8])

class ConvenienceVmCommands(object):

    def __init__(self, _):
        pass

    def list_ip_addresses(self, optional_resource_group_name=None, vm_name=None):
        '''
        Get IP addresses from one or more Virtual Machines

        :param str optional_resource_group_name:Name of resource group.
        :param str vm_name:Name of virtual machine.
        '''
        from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration

        # We start by getting NICs as they are the smack in the middle of all data that we
        # want to collect for a VM (as long as we don't need any info on the VM than what
        # is available in the Id, we don't need to make any calls to the compute RP)
        #
        # Since there is no guarantee that a NIC is in the same resource group as a given
        # Virtual Machine, we can't constrain the lookup to only a single group...
        network_client = get_mgmt_service_client(NetworkManagementClient,
                                                 NetworkManagementClientConfiguration)
        nics = network_client.network_interfaces.list_all()
        public_ip_addresses = network_client.public_ip_addresses.list_all()

        ip_address_lookup = {pip.id: pip for pip in list(public_ip_addresses)}

        result = []
        for nic in [n for n in list(nics) if n.virtual_machine]:
            nic_resource_group, nic_vm_name = _parse_rg_name(nic.virtual_machine.id)

            # If provided, make sure that resource group name and vm name match the NIC we are
            # looking at before adding it to the result...
            if (optional_resource_group_name in (None, nic_resource_group)
                and vm_name in (None, nic_vm_name )):

                network_info = {
                    'privateIpAddresses': [],
                    'publicIpAddresses': []
                }
                for ip_configuration in nic.ip_configurations:
                    network_info['privateIpAddresses'].append(ip_configuration.private_ip_address)
                    if ip_configuration.public_ip_address:
                        public_ip_address = ip_address_lookup[ip_configuration.public_ip_address.id]
                        network_info['publicIpAddresses'].append({
                            'id': public_ip_address.id,
                            'name': public_ip_address.name,
                            'ipAddress': public_ip_address.ip_address,
                            'ipAllocationMethod': public_ip_address.public_ip_allocation_method
                            })

                result.append({
                    'virtualMachine': {
                        'resourceGroup': nic_resource_group,
                        'name': nic_vm_name,
                        'network': network_info
                        }
                    })

        return result
