# pylint: disable=no-self-use,too-many-arguments
import re

from azure.mgmt.compute.models import DataDisk
from azure.mgmt.compute.models.compute_management_client_enums import DiskCreateOptionTypes
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli._util import CLIError

from ._actions import load_images_from_aliases_doc, load_images_thru_services
from ._factory import _compute_client_factory

from six.moves.urllib.request import urlopen #pylint: disable=import-error,unused-import

command_table = CommandTable()

def _vm_get(**kwargs):
    '''Retrieves a VM if a resource group and vm name are supplied.'''
    vm_name = kwargs.get('vm_name')
    resource_group_name = kwargs.get('resource_group_name')
    result = None
    if resource_group_name and vm_name:
        client = _compute_client_factory()
        result = client.virtual_machines.get(resource_group_name, vm_name)
    return result

def _vm_set(instance, start_msg, end_msg):
    '''Update the given Virtual Machine instance'''
    instance.resources = None # Issue: https://github.com/Azure/autorest/issues/934
    client = _compute_client_factory()
    parsed_id = _parse_rg_name(instance.id)
    poller = client.virtual_machines.create_or_update(
        resource_group_name=parsed_id[0],
        vm_name=parsed_id[1],
        parameters=instance)
    return LongRunningOperation(start_msg, end_msg)(poller)

def _parse_rg_name(strid):
    '''From an ID, extract the contained (resource group, name) tuple
    '''
    parts = re.split('/', strid)
    if parts[3] != 'resourceGroups':
        raise KeyError()

    return (parts[4], parts[8])

class ConvenienceVmCommands(object): # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        self.vm = _vm_get(**kwargs)

    def list(self, resource_group_name=None):
        ''' List Virtual Machines. '''
        ccf = _compute_client_factory()
        vm_list = ccf.virtual_machines.list(resource_group_name=resource_group_name) \
            if resource_group_name else ccf.virtual_machines.list_all()
        return list(vm_list)

    def list_vm_images(self, image_location=None, publisher=None, offer=None, sku=None, all=False): # pylint: disable=redefined-builtin
        '''vm image list
        :param str image_location:Image location
        :param str publisher:Image publisher name
        :param str offer:Image offer name
        :param str sku:Image sku name
        :param bool all:Retrieve all versions of images from all publishers
        '''
        load_thru_services = all

        if load_thru_services:
            all_images = load_images_thru_services(publisher,
                                                   offer,
                                                   sku,
                                                   image_location)
        else:
            all_images = load_images_from_aliases_doc(publisher, offer, sku)

        for i in all_images:
            i['urn'] = ':'.join([i['publisher'], i['offer'], i['sku'], i['version']])
        return all_images


    def list_ip_addresses(self, resource_group_name=None, vm_name=None):
        ''' Get IP addresses from one or more Virtual Machines
        :param str resource_group_name:Name of resource group.
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
            if (resource_group_name in (None, nic_resource_group)
                    and vm_name in (None, nic_vm_name)):

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

    def attach_new_disk(self, lun, diskname, vhd, disksize=1023):
        ''' Attach a new disk to an existing Virtual Machine'''
        disk = DataDisk(lun=lun, vhd=vhd, name=diskname,
                        create_option=DiskCreateOptionTypes.empty,
                        disk_size_gb=disksize)
        self.vm.storage_profile.data_disks.append(disk) # pylint: disable=no-member
        _vm_set(self.vm, 'Attaching disk', 'Disk attached')

    def attach_existing_disk(self, lun, diskname, vhd, disksize=1023):
        ''' Attach an existing disk to an existing Virtual Machine '''
        # TODO: figure out size of existing disk instead of making the default value 1023
        disk = DataDisk(lun=lun, vhd=vhd, name=diskname,
                        create_option=DiskCreateOptionTypes.attach,
                        disk_size_gb=disksize)
        self.vm.storage_profile.data_disks.append(disk) # pylint: disable=no-member
        _vm_set(self.vm, 'Attaching disk', 'Disk attached')

    def detach_disk(self, diskname):
        ''' Detach a disk from a Virtual Machine '''
        # Issue: https://github.com/Azure/autorest/issues/934
        self.vm.resources = None
        try:
            disk = next(d for d in self.vm.storage_profile.data_disks if d.name == diskname) # pylint: disable=no-member
            self.vm.storage_profile.data_disks.remove(disk) # pylint: disable=no-member
        except StopIteration:
            raise CLIError("No disk with the name '{}' found".format(diskname))
        _vm_set(self.vm, 'Detaching disk', 'Disk detached')

    def list_disks(self):
        ''' List disks for a Virtual Machine '''
        return self.vm.storage_profile.data_disks # pylint: disable=no-member
