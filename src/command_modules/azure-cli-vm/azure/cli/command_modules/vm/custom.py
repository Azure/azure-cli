#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,too-many-lines
from __future__ import print_function
import json
import os
import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse # pylint: disable=import-error
from six.moves.urllib.request import urlopen #pylint: disable=import-error,unused-import

from azure.mgmt.compute.models import (DataDisk,
                                       VirtualMachineScaleSet,
                                       VirtualMachineCaptureParameters,
                                       VirtualMachineScaleSetExtension,
                                       VirtualMachineScaleSetExtensionProfile)
from azure.mgmt.compute.models.compute_management_client_enums import DiskCreateOptionTypes
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
from azure.cli.core._util import CLIError
import azure.cli.core._logging as _logging
from ._vm_utils import read_content_if_is_file, load_json
from ._vm_diagnostics_templates import get_default_diag_config

from ._actions import (load_images_from_aliases_doc,
                       load_extension_images_thru_services,
                       load_images_thru_services)
from ._factory import _compute_client_factory

logger = _logging.get_az_logger(__name__)

def _vm_get(resource_group_name, vm_name, expand=None):
    '''Retrieves a VM'''
    client = _compute_client_factory()
    return client.virtual_machines.get(resource_group_name,
                                       vm_name,
                                       expand=expand)

def _vm_set(instance, lro_operation=None):
    '''Update the given Virtual Machine instance'''
    instance.resources = None # Issue: https://github.com/Azure/autorest/issues/934
    client = _compute_client_factory()
    parsed_id = _parse_rg_name(instance.id)
    poller = client.virtual_machines.create_or_update(
        resource_group_name=parsed_id[0],
        vm_name=parsed_id[1],
        parameters=instance)
    if lro_operation:
        return lro_operation(poller)
    else:
        return LongRunningOperation()(poller)

def _parse_rg_name(strid):
    '''From an ID, extract the contained (resource group, name) tuple
    '''
    parts = re.split('/', strid)
    if parts[3] != 'resourceGroups':
        raise KeyError()

    return (parts[4], parts[8])

#Use the same name by portal, so people can update from both cli and portal
#(VM doesn't allow multiple handlers for the same extension)
_ACCESS_EXT_HANDLER_NAME = 'enablevmaccess'

_LINUX_ACCESS_EXT = 'VMAccessForLinux'
_WINDOWS_ACCESS_EXT = 'VMAccessAgent'
_LINUX_DIAG_EXT = 'LinuxDiagnostic'
_WINDOWS_DIAG_EXT = 'IaaSDiagnostics'
extension_mappings = {
    _LINUX_ACCESS_EXT: {
        'version': '1.4',
        'publisher': 'Microsoft.OSTCExtensions'
        },
    _WINDOWS_ACCESS_EXT: {
        'version': '2.0',
        'publisher': 'Microsoft.Compute'
        },
    _LINUX_DIAG_EXT:{
        'version': '2.3',
        'publisher': 'Microsoft.OSTCExtensions'
        },
    _WINDOWS_DIAG_EXT:{
        'version': '1.5',
        'publisher': 'Microsoft.Azure.Diagnostics'
        }
    }

def _get_access_extension_upgrade_info(extensions, name):
    version = extension_mappings[name]['version']
    publisher = extension_mappings[name]['publisher']

    auto_upgrade = None

    if extensions:
        extension = next((e for e in extensions if e.name == name), None)
        #pylint: disable=no-name-in-module,import-error
        from distutils.version import LooseVersion
        if extension and LooseVersion(extension.type_handler_version) < LooseVersion(version):
            auto_upgrade = True
        elif extension and LooseVersion(extension.type_handler_version) > LooseVersion(version):
            version = extension.type_handler_version

    return publisher, version, auto_upgrade


def _get_storage_management_client():
    from azure.mgmt.storage import StorageManagementClient
    return get_mgmt_service_client(StorageManagementClient)

def _trim_away_build_number(version):
    #workaround a known issue: the version must only contain "major.minor", even though
    #"extension image list" gives more detail
    return '.'.join(version.split('.')[0:2])

#Hide extension information from output as the info is not correct and unhelpful; also
#commands using it mean to hide the extension concept from users.
class ExtensionUpdateLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods
    def __call__(self, poller):
        super(ExtensionUpdateLongRunningOperation, self).__call__(poller)
        #That said, we surppress the output. Operation failures will still
        #be caught through the base class
        return None

def list_vm(resource_group_name=None):
    ''' List Virtual Machines. '''
    ccf = _compute_client_factory()
    vm_list = ccf.virtual_machines.list(resource_group_name=resource_group_name) \
        if resource_group_name else ccf.virtual_machines.list_all()
    return list(vm_list)

def list_vm_images(image_location=None, publisher=None, offer=None, sku=None, all=False): # pylint: disable=redefined-builtin
    '''vm image list
    :param str image_location:Image location
    :param str publisher:Image publisher name
    :param str offer:Image offer name
    :param str sku:Image sku name
    :param bool all:Retrieve all versions of images from all publishers
    '''
    load_thru_services = all

    if load_thru_services:
        all_images = load_images_thru_services(publisher, offer, sku, image_location)
    else:
        logger.warning(
            'You are viewing an offline list of images, use --all to retrieve an up-to-date list')
        all_images = load_images_from_aliases_doc(publisher, offer, sku)

    for i in all_images:
        i['urn'] = ':'.join([i['publisher'], i['offer'], i['sku'], i['version']])
    return all_images

def list_vm_extension_images(
        image_location=None, publisher=None, name=None, version=None, latest=False):
    '''vm extension image list
    :param str image_location:Image location
    :param str publisher:Image publisher name
    :param str name:Image name
    :param str version:Image version
    :param bool latest: Show the latest version only.
    '''
    return load_extension_images_thru_services(
        publisher, name, version, image_location, latest)

def list_ip_addresses(resource_group_name=None, vm_name=None):
    ''' Get IP addresses from one or more Virtual Machines
    :param str resource_group_name:Name of resource group.
    :param str vm_name:Name of virtual machine.
    '''
    from azure.mgmt.network import NetworkManagementClient

    # We start by getting NICs as they are the smack in the middle of all data that we
    # want to collect for a VM (as long as we don't need any info on the VM than what
    # is available in the Id, we don't need to make any calls to the compute RP)
    #
    # Since there is no guarantee that a NIC is in the same resource group as a given
    # Virtual Machine, we can't constrain the lookup to only a single group...
    network_client = get_mgmt_service_client(NetworkManagementClient)
    nics = network_client.network_interfaces.list_all()
    public_ip_addresses = network_client.public_ip_addresses.list_all()

    ip_address_lookup = {pip.id: pip for pip in list(public_ip_addresses)}

    result = []
    for nic in [n for n in list(nics) if n.virtual_machine]:
        nic_resource_group, nic_vm_name = _parse_rg_name(nic.virtual_machine.id)

        # If provided, make sure that resource group name and vm name match the NIC we are
        # looking at before adding it to the result...
        if ((resource_group_name is None or resource_group_name.lower() == nic_resource_group.lower()) and #pylint: disable=line-too-long
                (vm_name is None or vm_name.lower() == nic_vm_name.lower())):

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

def attach_new_disk(resource_group_name, vm_name, vhd, lun=None,
                    disk_name=None, disk_size=1023, caching=None):
    ''' Attach a new disk to an existing Virtual Machine'''
    return _attach_disk(resource_group_name, vm_name, vhd, DiskCreateOptionTypes.empty,
                        lun, disk_name, caching, disk_size)

def attach_existing_disk(resource_group_name, vm_name, vhd, lun=None, disk_name=None, caching=None):
    ''' Attach an existing disk to an existing Virtual Machine '''
    return _attach_disk(resource_group_name, vm_name, vhd, DiskCreateOptionTypes.attach,
                        lun, disk_name, caching)

def _attach_disk(resource_group_name, vm_name, vhd, create_option, lun=None,
                 disk_name=None, caching=None, disk_size=None):
    vm = _vm_get(resource_group_name, vm_name)
    if disk_name is None:
        file_name = vhd.uri.split('/')[-1]
        disk_name = os.path.splitext(file_name)[0]
    #pylint: disable=no-member
    if lun is None:
        lun = _get_disk_lun(vm.storage_profile.data_disks)
    disk = DataDisk(lun=lun, vhd=vhd, name=disk_name,
                    create_option=create_option,
                    caching=caching, disk_size_gb=disk_size)
    if  vm.storage_profile.data_disks is None:
        vm.storage_profile.data_disks = []
    vm.storage_profile.data_disks.append(disk) # pylint: disable=no-member
    return _vm_set(vm)

def detach_disk(resource_group_name, vm_name, disk_name):
    ''' Detach a disk from a Virtual Machine '''
    vm = _vm_get(resource_group_name, vm_name)
    # Issue: https://github.com/Azure/autorest/issues/934
    vm.resources = None
    try:
        disk = next(d for d in vm.storage_profile.data_disks if d.name.lower() == disk_name.lower()) # pylint: disable=no-member
        vm.storage_profile.data_disks.remove(disk) # pylint: disable=no-member
    except (StopIteration, AttributeError):
        raise CLIError("No disk with the name '{}' found".format(disk_name))
    return _vm_set(vm)

def _get_disk_lun(data_disks):
    #start from 0, search for unused int for lun
    if data_disks:
        existing_luns = sorted([d.lun for d in data_disks])
        for i in range(len(existing_luns)):#pylint: disable=consider-using-enumerate
            if existing_luns[i] != i:
                return i
        return len(existing_luns)
    else:
        return 0

def resize_vm(resource_group_name, vm_name, size):
    '''Update vm size
    :param str size: sizes such as Standard_A4, Standard_F4s, etc
    '''
    vm = _vm_get(resource_group_name, vm_name)
    vm.hardware_profile.vm_size = size #pylint: disable=no-member
    return _vm_set(vm)

def get_instance_view(resource_group_name, vm_name):
    return _vm_get(resource_group_name, vm_name, 'instanceView')

def list_disks(resource_group_name, vm_name):
    ''' List disks for a Virtual Machine '''
    vm = _vm_get(resource_group_name, vm_name)
    return vm.storage_profile.data_disks # pylint: disable=no-member

def capture_vm(resource_group_name, vm_name, vhd_name_prefix,
               storage_container='vhds', overwrite=True):
    '''Captures the VM by copying virtual hard disks of the VM and outputs a
    template that can be used to create similar VMs.
    :param str vhd_name_prefix: the VHD name prefix specify for the VM disks
    :param str storage_container: the storage account container name to save the disks
    :param str overwrite: overwrite the existing disk file
    '''
    client = _compute_client_factory()
    parameter = VirtualMachineCaptureParameters(vhd_name_prefix, storage_container, overwrite)
    poller = client.virtual_machines.capture(resource_group_name, vm_name, parameter)
    result = LongRunningOperation()(poller)
    print(json.dumps(result.output, indent=2)) # pylint: disable=no-member

def reset_windows_admin(
        resource_group_name, vm_name, username, password):
    '''Update the password.
    You can only change the password. Adding a new user is not supported.
    '''
    vm = _vm_get(resource_group_name, vm_name, 'instanceView')

    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    extension_name = _WINDOWS_ACCESS_EXT
    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm.resources, extension_name)

    ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                  publisher=publisher,
                                  virtual_machine_extension_type=extension_name,
                                  protected_settings={'Password': password},
                                  type_handler_version=version,
                                  settings={'UserName': username},
                                  auto_upgrade_minor_version=auto_upgrade)

    poller = client.virtual_machine_extensions.create_or_update(resource_group_name, vm_name,
                                                                _ACCESS_EXT_HANDLER_NAME, ext)
    return ExtensionUpdateLongRunningOperation('resetting admin', 'done')(poller)

def set_linux_user(
        resource_group_name, vm_name, username, password=None, ssh_key_value=None):
    '''create or update a user credential
    :param username: user name
    :param password: user password.
    :param ssh_key_value: SSH key file value or key file path
    '''
    vm = _vm_get(resource_group_name, vm_name, 'instanceView')
    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    protected_settings = {}

    protected_settings['username'] = username
    if password:
        protected_settings['password'] = password
    elif not ssh_key_value and not password: #default to ssh
        ssh_key_value = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')

    if ssh_key_value:
        protected_settings['ssh_key'] = read_content_if_is_file(ssh_key_value)

    extension_name = _LINUX_ACCESS_EXT
    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm.resources, extension_name)

    ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                  publisher=publisher,
                                  virtual_machine_extension_type=extension_name,
                                  protected_settings=protected_settings,
                                  type_handler_version=version,
                                  settings={},
                                  auto_upgrade_minor_version=auto_upgrade)

    poller = client.virtual_machine_extensions.create_or_update(
        resource_group_name, vm_name, _ACCESS_EXT_HANDLER_NAME, ext)
    return ExtensionUpdateLongRunningOperation('setting user', 'done')(poller)

def delete_linux_user(
        resource_group_name, vm_name, username):
    '''Remove the user '''
    vm = _vm_get(resource_group_name, vm_name, 'instanceView')
    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    extension_name = _LINUX_ACCESS_EXT
    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm.resources, extension_name)

    ext = VirtualMachineExtension(vm.location,#pylint: disable=no-member
                                  publisher=publisher,
                                  virtual_machine_extension_type=extension_name,
                                  protected_settings={'remove_user':username},
                                  type_handler_version=version,
                                  settings={},
                                  auto_upgrade_minor_version=auto_upgrade)

    poller = client.virtual_machine_extensions.create_or_update(resource_group_name, vm_name,
                                                                _ACCESS_EXT_HANDLER_NAME, ext)
    return ExtensionUpdateLongRunningOperation('deleting user', 'done')(poller)

def disable_boot_diagnostics(resource_group_name, vm_name):
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
    _vm_set(vm, ExtensionUpdateLongRunningOperation('disabling boot diagnostics', 'done'))

def enable_boot_diagnostics(resource_group_name, vm_name, storage):
    '''Enable boot diagnostics
    :param storage:a storage account name or a uri like
    https://your_stoage_account_name.blob.core.windows.net/
    '''
    vm = _vm_get(resource_group_name, vm_name)
    if urlparse(storage).scheme:
        storage_uri = storage
    else:
        storage_mgmt_client = _get_storage_management_client()
        storage_accounts = storage_mgmt_client.storage_accounts.list()
        storage_account = next((a for a in list(storage_accounts)
                                if a.name.lower() == storage.lower()), None)
        if storage_account is None:
            raise CLIError('{} does\'t exist.'.format(storage))
        storage_uri = storage_account.primary_endpoints.blob

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
    _vm_set(vm, ExtensionUpdateLongRunningOperation('enabling boot diagnostics', 'done'))

def get_boot_log(resource_group_name, vm_name):
    import sys
    import io
    from azure.cli.core.cloud import CloudSuffix
    from azure.cli.core._profile import CLOUD
    from azure.storage.blob import BlockBlobService

    client = _compute_client_factory()

    virtual_machine = client.virtual_machines.get(
        resource_group_name,
        vm_name,
        expand='instanceView')
    # pylint: disable=no-member
    if (not virtual_machine.instance_view.boot_diagnostics or
            not virtual_machine.instance_view.boot_diagnostics.serial_console_log_blob_uri):
        raise CLIError('Please enable boot diagnostics.')

    blob_uri = virtual_machine.instance_view.boot_diagnostics.serial_console_log_blob_uri

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
    keys = storage_mgmt_client.storage_accounts.list_keys(rg, storage_account.name)

    # Extract container and blob name from url...
    container, blob = urlparse(blob_uri).path.split('/')[-2:]

    storage_client = get_data_service_client(
        BlockBlobService,
        storage_account.name,
        keys.key1,
        endpoint_suffix=CLOUD.suffixes[CloudSuffix.STORAGE_ENDPOINT]) # pylint: disable=no-member

    class StreamWriter(object): # pylint: disable=too-few-public-methods

        def __init__(self, out):
            self.out = out

        def write(self, str_or_bytes):
            if isinstance(str_or_bytes, bytes):
                self.out.write(str_or_bytes.decode())
            else:
                self.out.write(str_or_bytes)

    #our streamwriter not seekable, so no parallel.
    storage_client.get_blob_to_stream(container, blob, StreamWriter(sys.stdout), max_connections=1)

def list_extensions(resource_group_name, vm_name):
    vm = _vm_get(resource_group_name, vm_name)
    extension_type = 'Microsoft.Compute/virtualMachines/extensions'
    result = [r for r in vm.resources if r.type == extension_type]
    return result

def set_extension(
        resource_group_name, vm_name, vm_extension_name, publisher,
        version=None, settings=None,
        protected_settings=None, no_auto_upgrade=False):
    '''create/update extensions for a VM in a resource group. You can use
    'extension image list' to get extension details
    :param vm_extension_name: the name of the extension
    :param publisher: the name of extension publisher
    :param version: the version of extension.
    :param settings: public settings or a file path with such contents
    :param protected_settings: protected settings or a file path with such contents
    :param no_auto_upgrade: by doing this, extension system will not pick the highest minor version
    for the specified version number, and will not auto update to the latest build/revision number
    on any VM updates in future.
    '''
    vm = _vm_get(resource_group_name, vm_name)
    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    protected_settings = load_json(protected_settings) if protected_settings else {}
    settings = load_json(settings) if settings else None

    #pylint: disable=no-member
    version = _normalize_extension_version(publisher, vm_extension_name, version, vm.location)

    ext = VirtualMachineExtension(vm.location,
                                  publisher=publisher,
                                  virtual_machine_extension_type=vm_extension_name,
                                  protected_settings=protected_settings,
                                  type_handler_version=version,
                                  settings=settings,
                                  auto_upgrade_minor_version=(not no_auto_upgrade))
    return client.virtual_machine_extensions.create_or_update(
        resource_group_name, vm_name, vm_extension_name, ext)

def set_vmss_extension(
        resource_group_name, vmss_name, extension_name, publisher,
        version=None, settings=None,
        protected_settings=None, no_auto_upgrade=False):
    '''create/update extensions for a VMSS in a resource group. You can use
    'extension image list' to get extension details
    :param vm_extension_name: the name of the extension
    :param publisher: the name of extension publisher
    :param version: the version of extension.
    :param settings: public settings or a file path with such contents
    :param protected_settings: protected settings or a file path with such contents
    :param no_auto_upgrade: by doing this, extension system will not pick the highest minor version
    for the specified version number, and will not auto update to the latest build/revision number
    on any scale set updates in future.
    '''
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)

    from azure.mgmt.compute.models import VirtualMachineExtension

    protected_settings = load_json(protected_settings) if protected_settings else {}
    settings = load_json(settings) if settings else None

    #pylint: disable=no-member
    version = _normalize_extension_version(publisher, extension_name, version, vmss.location)

    ext = VirtualMachineScaleSetExtension(name=extension_name,
                                          publisher=publisher,
                                          type=extension_name,
                                          protected_settings=protected_settings,
                                          type_handler_version=version,
                                          settings=settings,
                                          auto_upgrade_minor_version=(not no_auto_upgrade))

    if not vmss.virtual_machine_profile.extension_profile:
        vmss.virtual_machine_profile.extension_profile = VirtualMachineScaleSetExtensionProfile([])
    vmss.virtual_machine_profile.extension_profile.extensions.append(ext)

    return client.virtual_machine_scale_sets.create_or_update(resource_group_name,
                                                              vmss_name,
                                                              vmss)

def _normalize_extension_version(publisher, vm_extension_name, version, location):
    if not version:
        result = load_extension_images_thru_services(publisher, vm_extension_name,
                                                     None, location, show_latest=True)
        if not result:
            raise CLIError('Failed to find the latest version for the extension "{}"'
                           .format(vm_extension_name))

        #with 'show_latest' enabled, we will only get one result.
        version = result[0]['version']

    version = _trim_away_build_number(version)
    return version

def set_diagnostics_extension(
        resource_group_name, vm_name, settings, protected_settings=None, version=None,
        no_auto_upgrade=False):
    '''Enable diagnostics on a virtual machine
    '''
    vm = _vm_get(resource_group_name, vm_name)
    #pylint: disable=no-member
    is_linux_os = _detect_os_type_for_diagnostics_ext(vm.os_profile)
    vm_extension_name = _LINUX_DIAG_EXT if is_linux_os else _WINDOWS_DIAG_EXT
    return set_extension(resource_group_name, vm_name, vm_extension_name,
                         extension_mappings[vm_extension_name]['publisher'],
                         version or extension_mappings[vm_extension_name]['version'],
                         settings,
                         protected_settings,
                         no_auto_upgrade)

def set_vmss_diagnostics_extension(
        resource_group_name, vmss_name, settings, protected_settings=None, version=None,
        no_auto_upgrade=False):
    '''Enable diagnostics on a virtual machine scale set
    '''
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    #pylint: disable=no-member
    is_linux_os = _detect_os_type_for_diagnostics_ext(vmss.virtual_machine_profile.os_profile)
    vm_extension_name = _LINUX_DIAG_EXT if is_linux_os else _WINDOWS_DIAG_EXT
    return set_vmss_extension(resource_group_name, vmss_name, vm_extension_name,
                              extension_mappings[vm_extension_name]['publisher'],
                              version or extension_mappings[vm_extension_name]['version'],
                              settings,
                              protected_settings,
                              no_auto_upgrade)

#Same logic also applies on vmss
def _detect_os_type_for_diagnostics_ext(os_profile):
    is_linux_os = bool(os_profile.linux_configuration)
    is_windows_os = bool(os_profile.windows_configuration)
    if not is_linux_os and not is_windows_os:
        raise CLIError('Diagnostics extension can only be installed on Linux or Windows VM')
    return is_linux_os

def get_vmss_extension(resource_group_name, vmss_name, extension_name):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    #pylint: disable=no-member
    if not vmss.virtual_machine_profile.extension_profile:
        return
    return next((e for e in vmss.virtual_machine_profile.extension_profile.extensions
                 if e.name == extension_name), None)

def list_vmss_extensions(resource_group_name, vmss_name):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    #pylint: disable=no-member
    return None if not vmss.virtual_machine_profile.extension_profile \
        else vmss.virtual_machine_profile.extension_profile.extensions

def delete_vmss_extension(resource_group_name, vmss_name, extension_name):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    #pylint: disable=no-member
    if not vmss.virtual_machine_profile.extension_profile:
        raise CLIError('Scale set has no extensions to delete')

    keep_list = [e for e in vmss.virtual_machine_profile.extension_profile.extensions
                 if e.name != extension_name]
    if len(keep_list) == len(vmss.virtual_machine_profile.extension_profile.extensions):
        raise CLIError('Extension {} not found'.format(extension_name))

    vmss.virtual_machine_profile.extension_profile.extensions = keep_list

    return client.virtual_machine_scale_sets.create_or_update(resource_group_name,
                                                              vmss_name,
                                                              vmss)

def _get_private_config(resource_group_name, storage_account):
    storage_mgmt_client = _get_storage_management_client()
    #pylint: disable=no-member
    keys = storage_mgmt_client.storage_accounts.list_keys(resource_group_name, storage_account).keys

    private_config = {
        'storageAccountName': storage_account,
        'storageAccountKey': keys[0].value
        }
    return private_config

def show_default_diagnostics_configuration(is_windows_os=False):
    '''show the default config file which defines data to be collected'''
    return get_default_diag_config(is_windows_os)

def vm_add_nics(resource_group_name, vm_name, nic_ids=None, nic_names=None, primary_nic=None):
    '''add network interface configurations to the virtual machine
    :param str nic_ids: NIC resource IDs
    :param str nic_names: NIC names, assuming under the same resource group
    :param str primary_nic: name or id of the primary NIC. If missing, the first of the
    NIC list will be the primary
    '''
    vm = _vm_get(resource_group_name, vm_name)
    new_nics = _build_nic_list(resource_group_name, nic_ids or [], nic_names or [])
    existing_nics = _get_existing_nics(vm)
    return _update_vm_nics(vm, existing_nics + new_nics, primary_nic)

def vm_delete_nics(resource_group_name, vm_name, nic_ids=None, nic_names=None, primary_nic=None):
    '''remove network interface configurations from the virtual machine
    :param str nic_ids: NIC resource IDs
    :param str nic_names: NIC names, assuming under the same resource group
    :param str primary_nic: name or id of the primary NIC. If missing, the first of the
    NIC list will be the primary
    '''
    def to_delete(nic_id):
        return [n for n in nics_to_delete if n.id.lower() == nic_id.lower()]
    vm = _vm_get(resource_group_name, vm_name)
    nics_to_delete = _build_nic_list(resource_group_name, nic_ids or [], nic_names or [])
    existing_nics = _get_existing_nics(vm)
    survived = [x for x in existing_nics if not to_delete(x.id)]
    return _update_vm_nics(vm, survived, primary_nic)

def vm_update_nics(resource_group_name, vm_name, nic_ids=None, nic_names=None, primary_nic=None):
    '''update network interface configurations of the virtual machine
    :param str nic_ids: NIC resource IDs
    :param str nic_names: NIC names, assuming under the same resource group
    :param str primary_nic: name or id of the primary nic. If missing, the first element of
    nic list will be set to the primary
    '''
    vm = _vm_get(resource_group_name, vm_name)
    nics = _build_nic_list(resource_group_name, nic_ids or [], nic_names or [])
    return _update_vm_nics(vm, nics, primary_nic)

# pylint: disable=no-member
def vm_open_port(resource_group_name, vm_name, network_security_group_name=None,
                 apply_to_subnet=False):
    """ Opens a VM to all inbound traffic and protocols by adding a security rule to the network
    security group (NSG) that is attached to the VM's network interface (NIC) or subnet. The
    existing NSG will be used or a new one will be created. The rule name is 'open-port-cmd' and
    will overwrite an existing rule with this name. For multi-NIC VMs, or for more fine
    grained control, use the appropriate network commands directly (nsg rule create, etc).
    """
    from azure.mgmt.network import NetworkManagementClient
    network = get_mgmt_service_client(NetworkManagementClient)

    vm = _vm_get(resource_group_name, vm_name)
    location = vm.location
    nic_ids = list(vm.network_profile.network_interfaces)
    if len(nic_ids) > 1:
        raise CLIError('Multiple NICs is not supported for this command. Create rules on the NSG '
                       'directly.')
    elif not nic_ids:
        raise CLIError("No NIC associated with VM '{}'".format(vm_name))

    # get existing NSG or create a new one
    nic = network.network_interfaces.get(resource_group_name, os.path.split(nic_ids[0].id)[1])
    if not apply_to_subnet:
        nsg = nic.network_security_group
    else:
        from azure.cli.core.commands.arm import parse_resource_id
        subnet_id = parse_resource_id(nic.ip_configurations[0].subnet.id)
        subnet = network.subnets.get(resource_group_name,
                                     subnet_id['name'],
                                     subnet_id['child_name'])
        nsg = subnet.network_security_group

    if not nsg:
        from azure.mgmt.network.models import NetworkSecurityGroup
        nsg = LongRunningOperation('Creating network security group')(
            network.network_security_groups.create_or_update(
                resource_group_name=resource_group_name,
                network_security_group_name=network_security_group_name,
                parameters=NetworkSecurityGroup(location=location)
            )
        )

    # update the NSG with the new rule to allow inbound traffic
    from azure.mgmt.network.models import SecurityRule
    rule = SecurityRule(protocol='*', access='allow', direction='inbound', name='open-port-cmd',
                        source_port_range='*', destination_port_range='*', priority=900,
                        source_address_prefix='*', destination_address_prefix='*')
    nsg_name = nsg.name or os.path.split(nsg.id)[1]
    LongRunningOperation('Adding security rule')(
        network.security_rules.create_or_update(
            resource_group_name, nsg_name, 'open-port-cmd', rule)
    )

    # update the NIC or subnet
    if not apply_to_subnet:
        nic.network_security_group = nsg
        return LongRunningOperation('Updating NIC')(
            network.network_interfaces.create_or_update(
                resource_group_name, nic.name, nic)
        )
    else:
        from azure.mgmt.network.models import Subnet
        subnet.network_security_group = nsg
        return LongRunningOperation('Updating subnet')(
            network.subnets.create_or_update(
                resource_group_name=resource_group_name,
                virtual_network_name=subnet_id['name'],
                subnet_name=subnet_id['child_name'],
                subnet_parameters=subnet
            )
        )

def _build_nic_list(resource_group_name, nic_ids, nic_names):
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.compute.models import NetworkInterfaceReference
    nics = []
    if nic_names or nic_ids:
        #pylint: disable=no-member
        network_client = get_mgmt_service_client(NetworkManagementClient)
        for n in nic_names:
            nic = network_client.network_interfaces.get(resource_group_name, n)
            nics.append(NetworkInterfaceReference(nic.id, False))

        for n in nic_ids:
            rg, name = _parse_rg_name(n)
            nic = network_client.network_interfaces.get(rg, name)
            nics.append(NetworkInterfaceReference(nic.id, False))
    return nics

def _get_existing_nics(vm):
    network_profile = getattr(vm, 'network_profile', None)
    nics = []
    if network_profile is not None:
        nics = network_profile.network_interfaces or []
    return nics

def _update_vm_nics(vm, nics, primary_nic):
    from azure.mgmt.compute.models import NetworkProfile

    if primary_nic:
        try:
            _, primary_nic_name = _parse_rg_name(primary_nic)
        except IndexError:
            primary_nic_name = primary_nic

        matched = [n for n in nics if _parse_rg_name(n.id)[1].lower() == primary_nic_name.lower()]
        if not matched:
            raise CLIError('Primary Nic {} is not found'.format(primary_nic))
        if len(matched) > 1:
            raise CLIError('Duplicate Nic entries with name {}'.format(primary_nic))
        for n in nics:
            n.primary = False
        matched[0].primary = True
    elif nics:
        if not [n for n in nics if n.primary]:
            nics[0].primary = True

    network_profile = getattr(vm, 'network_profile', None)
    if network_profile is None:
        vm.network_profile = NetworkProfile(nics)
    else:
        network_profile.network_interfaces = nics

    return _vm_set(vm)

def vmss_scale(resource_group_name, vm_scale_set_name, new_capacity):
    '''change the number of VMs in an virtual machine scale set

    :param int new_capacity: number of virtual machines in a scale set
    '''
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vm_scale_set_name)
    #pylint: disable=no-member
    if vmss.sku.capacity == new_capacity:
        return
    else:
        vmss.sku.capacity = new_capacity
    vmss_new = VirtualMachineScaleSet(vmss.location, sku=vmss.sku)
    return client.virtual_machine_scale_sets.create_or_update(resource_group_name,
                                                              vm_scale_set_name,
                                                              vmss_new)

def vmss_update_instances(resource_group_name, vm_scale_set_name, instance_ids):
    '''upgrade virtual machines in a virtual machine scale set'''
    client = _compute_client_factory()
    return client.virtual_machine_scale_sets.update_instances(resource_group_name,
                                                              vm_scale_set_name,
                                                              instance_ids)

def vmss_get_instance_view(resource_group_name, vm_scale_set_name, instance_id=None):
    '''get instance view for a scale set or its VM instances

    :param str instance_id: an VM instance id, or use "*" to list instance view for
    all VMs in a scale set
    '''
    client = _compute_client_factory()
    if instance_id:
        if instance_id == '*':
            return client.virtual_machine_scale_set_vms.list(resource_group_name,
                                                             vm_scale_set_name)
        else:
            return client.virtual_machine_scale_set_vms.get_instance_view(resource_group_name,
                                                                          vm_scale_set_name,
                                                                          instance_id)
    else:
        return client.virtual_machine_scale_sets.get_instance_view(resource_group_name,
                                                                   vm_scale_set_name)

def vmss_show(resource_group_name, vm_scale_set_name, instance_id=None):
    '''show scale set or its VM instance

    :param str instance_id: VM instance id. If missing, show scale set
    '''
    client = _compute_client_factory()
    if instance_id:
        return client.virtual_machine_scale_set_vms.get(resource_group_name,
                                                        vm_scale_set_name,
                                                        instance_id)
    else:
        return client.virtual_machine_scale_sets.get(resource_group_name,
                                                     vm_scale_set_name)

def vmss_list(resource_group_name=None):
    '''list scale sets'''
    client = _compute_client_factory()
    if resource_group_name:
        return client.virtual_machine_scale_sets.list(resource_group_name)
    else:
        return client.virtual_machine_scale_sets.list_all()

def vmss_deallocate(resource_group_name, vm_scale_set_name, instance_ids=None):
    '''deallocate virtual machines in a scale set. '''
    client = _compute_client_factory()
    if  instance_ids and len(instance_ids) == 1:
        return client.virtual_machine_scale_set_vms.deallocate(resource_group_name,
                                                               vm_scale_set_name,
                                                               instance_ids[0])
    else:
        return client.virtual_machine_scale_sets.deallocate(resource_group_name,
                                                            vm_scale_set_name,
                                                            instance_ids=instance_ids)

def vmss_delete_instances(resource_group_name, vm_scale_set_name, instance_ids):
    '''delete virtual machines in a scale set.'''
    client = _compute_client_factory()
    if len(instance_ids) == 1:
        return client.virtual_machine_scale_set_vms.delete(resource_group_name,
                                                           vm_scale_set_name,
                                                           instance_ids[0])
    else:
        return client.virtual_machine_scale_sets.delete_instances(resource_group_name,
                                                                  vm_scale_set_name,
                                                                  instance_ids)

def vmss_stop(resource_group_name, vm_scale_set_name, instance_ids=None):
    '''power off (stop) virtual machines in a virtual machine scale set.'''
    client = _compute_client_factory()
    if instance_ids and len(instance_ids) == 1:
        return client.virtual_machine_scale_set_vms.power_off(resource_group_name,
                                                              vm_scale_set_name,
                                                              instance_ids[0])
    else:
        return client.virtual_machine_scale_sets.power_off(resource_group_name,
                                                           vm_scale_set_name,
                                                           instance_ids=instance_ids)

def vmss_reimage(resource_group_name, vm_scale_set_name, instance_id=None):
    '''reimage virtual machines in a virtual machine scale set.

    :param str instance_id: VM instance id. If missing, reimage all instances
    '''
    client = _compute_client_factory()
    if instance_id:
        return client.virtual_machine_scale_set_vms.reimage(resource_group_name,
                                                            vm_scale_set_name,
                                                            instance_id)
    else:
        return client.virtual_machine_scale_sets.reimage(resource_group_name,
                                                         vm_scale_set_name)

def vmss_restart(resource_group_name, vm_scale_set_name, instance_ids=None):
    '''restart virtual machines in a scale set.'''
    client = _compute_client_factory()
    if instance_ids and len(instance_ids) == 1:
        return client.virtual_machine_scale_set_vms.restart(resource_group_name,
                                                            vm_scale_set_name,
                                                            instance_ids[0])
    else:
        return client.virtual_machine_scale_sets.restart(resource_group_name,
                                                         vm_scale_set_name,
                                                         instance_ids=instance_ids)

def vmss_start(resource_group_name, vm_scale_set_name, instance_ids=None):
    '''start virtual machines in a virtual machine scale set.'''
    client = _compute_client_factory()
    if instance_ids and len(instance_ids) == 1:
        return client.virtual_machine_scale_set_vms.start(resource_group_name,
                                                          vm_scale_set_name,
                                                          instance_ids[0])
    else:
        return client.virtual_machine_scale_sets.start(resource_group_name,
                                                       vm_scale_set_name,
                                                       instance_ids=instance_ids)

def availset_get(resource_group_name, name):
    return _compute_client_factory().availability_sets.get(resource_group_name, name)

def availset_set(**kwargs):
    return _compute_client_factory().availability_sets.create_or_update(**kwargs)

cli_generic_update_command('vm availability-set update', availset_get, availset_set)

def vmss_get(resource_group_name, name):
    return _compute_client_factory().virtual_machine_scale_sets.get(resource_group_name, name)

def vmss_set(**kwargs):
    return _compute_client_factory().virtual_machine_scale_sets.create_or_update(**kwargs)

cli_generic_update_command('vmss update', vmss_get, vmss_set)

def update_acs(instance, agent_count):
    instance.agent_pool_profiles[0].count = agent_count
    return instance
