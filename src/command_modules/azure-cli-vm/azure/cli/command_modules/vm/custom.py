# pylint: disable=no-self-use,too-many-arguments
import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse # pylint: disable=import-error
from six.moves.urllib.request import urlopen #pylint: disable=import-error,unused-import

from azure.mgmt.compute.models import DataDisk
from azure.mgmt.compute.models.compute_management_client_enums import DiskCreateOptionTypes
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli._util import CLIError
from ._vm_utils import read_content_if_is_file, load_json, get_default_linux_diag_config

from ._actions import (load_images_from_aliases_doc,
                       load_extension_images_thru_services,
                       load_images_thru_services)
from ._factory import _compute_client_factory

command_table = CommandTable()

def _vm_get(resource_group_name, vm_name, expand=None):
    '''Retrieves a VM'''
    client = _compute_client_factory()
    return client.virtual_machines.get(resource_group_name,
                                       vm_name,
                                       expand=expand)

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

def _get_access_extension_upgrade_info(extensions, is_linux=True):
    if is_linux:
        version = '1.4'
        name = 'VMAccessForLinux'
        publisher = 'Microsoft.OSTCExtensions'
    else:
        version = '2.0'
        name = 'VMAccessAgent'
        publisher = 'Microsoft.Compute'

    auto_upgrade = None

    if extensions:
        extension = next((e for e in extensions if e.name == name), None)
        #pylint: disable=no-name-in-module,import-error
        from distutils.version import LooseVersion
        if extension and LooseVersion(extension.type_handler_version) < LooseVersion(version):
            auto_upgrade = True
        elif extension and LooseVersion(extension.type_handler_version) > LooseVersion(version):
            version = extension.type_handler_version

    return publisher, name, version, auto_upgrade

def _get_storage_management_client():
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    return get_mgmt_service_client(StorageManagementClient,
                                   StorageManagementClientConfiguration)

def _trim_away_build_number(version):
    #workaround a known issue: the version must only contain "major.minor", even though
    #"extension image list" gives more detail
    return '.'.join(version.split('.')[0:2])

class ConvenienceVmCommands(object): # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        pass

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

    def list_vm_extension_images(self,
                                 image_location=None,
                                 publisher=None,
                                 name=None,
                                 version=None):
        '''vm extension image list
        :param str image_location:Image location
        :param str publisher:Image publisher name
        :param str name:Image name
        :param str version:Image version
        '''
        return load_extension_images_thru_services(publisher,
                                                   name,
                                                   version,
                                                   image_location)

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

    def attach_new_disk(self, resource_group_name, vm_name, lun, diskname, vhd, disksize=1023):
        ''' Attach a new disk to an existing Virtual Machine'''
        vm = _vm_get(resource_group_name, vm_name)
        disk = DataDisk(lun=lun, vhd=vhd, name=diskname,
                        create_option=DiskCreateOptionTypes.empty,
                        disk_size_gb=disksize)
        vm.storage_profile.data_disks.append(disk) # pylint: disable=no-member
        _vm_set(vm, 'Attaching disk', 'Disk attached')

    def attach_existing_disk(self, resource_group_name, vm_name, lun, diskname, vhd, disksize=1023):
        ''' Attach an existing disk to an existing Virtual Machine '''
        # TODO: figure out size of existing disk instead of making the default value 1023
        vm = _vm_get(resource_group_name, vm_name)
        disk = DataDisk(lun=lun, vhd=vhd, name=diskname,
                        create_option=DiskCreateOptionTypes.attach,
                        disk_size_gb=disksize)
        vm.storage_profile.data_disks.append(disk) # pylint: disable=no-member
        _vm_set(vm, 'Attaching disk', 'Disk attached')

    def detach_disk(self, resource_group_name, vm_name, diskname):
        ''' Detach a disk from a Virtual Machine '''
        vm = _vm_get(resource_group_name, vm_name)
        # Issue: https://github.com/Azure/autorest/issues/934
        vm.resources = None
        try:
            disk = next(d for d in vm.storage_profile.data_disks if d.name == diskname) # pylint: disable=no-member
            vm.storage_profile.data_disks.remove(disk) # pylint: disable=no-member
        except StopIteration:
            raise CLIError("No disk with the name '{}' found".format(diskname))
        _vm_set(vm, 'Detaching disk', 'Disk detached')

    def list_disks(self, resource_group_name, vm_name):
        ''' List disks for a Virtual Machine '''
        vm = _vm_get(resource_group_name, vm_name)
        return vm.storage_profile.data_disks # pylint: disable=no-member

    def set_windows_user_password(self,
                                  resource_group_name,
                                  vm_name,
                                  username,
                                  password):
        '''Update the password.
        You can only change the password. Adding a new user is not supported.
        '''
        vm = _vm_get(resource_group_name, vm_name, 'instanceView')

        client = _compute_client_factory()

        from azure.mgmt.compute.models import VirtualMachineExtension

        publisher, extension_name, version, auto_upgrade = _get_access_extension_upgrade_info(
            vm.resources, is_linux=False)

        ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                      publisher=publisher,
                                      virtual_machine_extension_type=extension_name,
                                      protected_settings={'Password': password},
                                      type_handler_version=version,
                                      settings={'UserName': username},
                                      auto_upgrade_minor_version=auto_upgrade)

        return client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                  vm_name,
                                                                  extension_name,
                                                                  ext)

    def set_linux_user(self,
                       resource_group_name,
                       vm_name,
                       username,
                       password=None,
                       ssh_key_value=None):
        '''craete or update a user credential
        :param ssh_key_value: SSH key file value or key file path
        '''
        vm = _vm_get(resource_group_name, vm_name, 'instanceView')
        client = _compute_client_factory()

        from azure.mgmt.compute.models import VirtualMachineExtension

        if password is None and ssh_key_value is None:
            raise CLIError('Please provide either password or ssh public key.')

        protected_settings = {}
        protected_settings['username'] = username
        if password:
            protected_settings['password'] = password

        if ssh_key_value:
            protected_settings['ssh_key'] = read_content_if_is_file(ssh_key_value)

        publisher, extension_name, version, auto_upgrade = _get_access_extension_upgrade_info(
            vm.resources, is_linux=True)

        ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                      publisher=publisher,
                                      virtual_machine_extension_type=extension_name,
                                      protected_settings=protected_settings,
                                      type_handler_version=version,
                                      settings={},
                                      auto_upgrade_minor_version=auto_upgrade)

        return client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                  vm_name,
                                                                  extension_name,
                                                                  ext)

    def delete_linux_user(self,
                          resource_group_name,
                          vm_name,
                          username):
        '''Remove the user '''
        vm = _vm_get(resource_group_name, vm_name, 'instanceView')
        client = _compute_client_factory()

        from azure.mgmt.compute.models import VirtualMachineExtension

        publisher, extension_name, version, auto_upgrade = _get_access_extension_upgrade_info(
            vm.resources, is_linux=True)

        ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                      publisher=publisher,
                                      virtual_machine_extension_type=extension_name,
                                      protected_settings={'remove_user':username},
                                      type_handler_version=version,
                                      settings={},
                                      auto_upgrade_minor_version=auto_upgrade)

        return client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                  vm_name,
                                                                  extension_name,
                                                                  ext)

    def disable_boot_diagnostics(self, resource_group_name, vm_name):
        vm = _vm_get(resource_group_name, vm_name)
        diag_profile = vm.diagnostics_profile
        if not (diag_profile and
                diag_profile.boot_diagnostics and
                diag_profile.boot_diagnostics.enabled):
            return

        # Issue: https://github.com/Azure/autorest/issues/934
        vm.resources = None
        diag_profile.boot_diagnostics.enabled = False
        diag_profile.boot_diagnostics.storage_uri = None
        _vm_set(vm, "Disabling boot diagnostics", "Done")

    def enable_boot_diagnostics(self, resource_group_name, vm_name, storage_uri):
        '''Enable boot diagnostics
        :param storage_uri:the storage account uri for boot diagnostics. A valid uri
           in format like https://your_stoage_account_name.blob.core.windows.net/
        '''
        vm = _vm_get(resource_group_name, vm_name)

        if (vm.diagnostics_profile and
                vm.diagnostics_profile.boot_diagnostics and
                vm.diagnostics_profile.boot_diagnostics.enabled and
                vm.diagnostics_profile.boot_diagnostics.storage_uri and
                vm.diagnostics_profile.boot_diagnostics.storage_uri.lower() == storage_uri.lower()):
            return

        from azure.mgmt.compute.models import DiagnosticsProfile, BootDiagnostics
        boot_diag = BootDiagnostics(True, storage_uri)
        if vm.diagnostics_profile is None:
            vm.diagnostics_profile = DiagnosticsProfile(boot_diag)
        else:
            vm.diagnostics_profile.boot_diagnostics = boot_diag

        # Issue: https://github.com/Azure/autorest/issues/934
        vm.resources = None
        _vm_set(vm, "Enabling boot diagnostics", "Done")

    def get_boot_log(self, resource_group_name, vm_name):
        import sys
        import io

        from azure.storage.blob import BlockBlobService

        client = _compute_client_factory()

        virtual_machine = client.virtual_machines.get(
            resource_group_name,
            vm_name,
            expand='instanceView')

        blob_uri = virtual_machine.instance_view.boot_diagnostics.serial_console_log_blob_uri # pylint: disable=no-member

        # Find storage account for diagnostics
        storage_mgmt_client = _get_storage_management_client()
        if not blob_uri:
            raise CLIError('No console log available')
        try:
            storage_accounts = storage_mgmt_client.storage_accounts.list()
            matching_storage_account = (a for a in list(storage_accounts)
                                        if blob_uri.startswith(a.primary_endpoints.blob))
            storage_account = next(matching_storage_account)
        except StopIteration:
            raise CLIError('Failed to find storage accont for console log file')

        regex = r'/subscriptions/[^/]+/resourceGroups/(?P<rg>[^/]+)/.+'
        match = re.search(regex, storage_account.id, re.I)
        rg = match.group('rg')
        # Get account key
        keys = storage_mgmt_client.storage_accounts.list_keys(rg,
                                                              storage_account.name)

        # Extract container and blob name from url...
        container, blob = urlparse(blob_uri).path.split('/')[-2:]

        storage_client = get_data_service_client(
            BlockBlobService,
            storage_account.name,
            keys.key1) # pylint: disable=no-member

        class StreamWriter(object): # pylint: disable=too-few-public-methods

            def __init__(self, out):
                self.out = out

            def write(self, str_or_bytes):
                if isinstance(str_or_bytes, bytes):
                    self.out.write(str_or_bytes.decode())
                else:
                    self.out.write(str_or_bytes)

        storage_client.get_blob_to_stream(container, blob, StreamWriter(sys.stdout))

    def list_extensions(self, resource_group_name, vm_name):
        vm = _vm_get(resource_group_name, vm_name)
        extension_type = 'Microsoft.Compute/virtualMachines/extensions'
        result = [r for r in vm.resources if r.type == extension_type]
        return result

    def set_extension(self,
                      resource_group_name,
                      vm_name,
                      vm_extension_name,
                      publisher,
                      version,
                      public_config=None,
                      private_config=None,
                      auto_upgrade_minor_version=False):
        '''create/update extensions for a VM in a resource group'
        :param vm_name: the name of virtual machine.
        :param vm_extension_name: the name of the extension
        :param publisher: the name of extension publisher
        :param version: the version of extension, must be in the format of "major.minor"
        :param public_config: public configuration content or a file path
        :param private_config: private configuration content or a file path
        :param auto_upgrade_minor_version: auto upgrade to the newer version if available
        '''
        vm = _vm_get(resource_group_name, vm_name)
        client = _compute_client_factory()

        from azure.mgmt.compute.models import VirtualMachineExtension

        protected_settings = load_json(private_config) if not private_config else {}
        settings = load_json(public_config) if not public_config else None

        version = _trim_away_build_number(version)

        ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                      publisher=publisher,
                                      virtual_machine_extension_type=vm_extension_name,
                                      protected_settings=protected_settings,
                                      type_handler_version=version,
                                      settings=settings,
                                      auto_upgrade_minor_version=auto_upgrade_minor_version)

        return client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                  vm_name,
                                                                  vm_extension_name,
                                                                  ext)

    def set_diagnostics_extension(self,
                                  resource_group_name,
                                  vm_name,
                                  storage_account,
                                  public_config=None,
                                  version=None):
        '''add/update diagnostics extensions'

        :param vm_name: the name of virtual machine
        :param storage_account: the storage account to upload diagnostics log
        :param public_config: the config file which defines data to be collected.
        Default will be provided if missing
        :param version: the version of LinuxDiagnostic extension
        '''
        vm = _vm_get(resource_group_name, vm_name)
        client = _compute_client_factory()

        from distutils.version import LooseVersion ##pylint: disable=no-name-in-module,import-error
        from azure.mgmt.compute.models import VirtualMachineExtension
        #pylint: disable=no-member
        if public_config:
            public_config = load_json(public_config)
        else:
            public_config = get_default_linux_diag_config(vm.id)

        storage_mgmt_client = _get_storage_management_client()
        keys = storage_mgmt_client.storage_accounts.list_keys(resource_group_name,
                                                              storage_account)

        private_config = {
            'storageAccountName': storage_account,
            'storageAccountKey': keys.key1
            }

        publisher = 'Microsoft.OSTCExtensions'
        vm_extension_name = 'LinuxDiagnostic'
        if version is None:
            result = load_extension_images_thru_services(publisher,
                                                         vm_extension_name, None, vm.location)
            if not result:
                raise CLIError('Can\'t find the image {} from publisher {}.'.format(
                    vm_extension_name, publisher))

            #look for the highest
            result.sort(key=lambda x: LooseVersion(x['version']), reverse=True)
            version = _trim_away_build_number(result[0]['version'])

        ext = VirtualMachineExtension(vm.location,
                                      publisher=publisher,
                                      virtual_machine_extension_type=vm_extension_name,
                                      protected_settings=private_config,
                                      type_handler_version=version,
                                      settings=public_config,
                                      auto_upgrade_minor_version=False)

        return client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                  vm_name,
                                                                  vm_extension_name,
                                                                  ext)

    def show_default_diagnostics_configuration(self):
        return get_default_linux_diag_config()
