# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,too-many-lines
from __future__ import print_function
import getpass
import json
import os
import re

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

from six.moves.urllib.request import urlopen  # noqa, pylint: disable=import-error,unused-import

from azure.mgmt.compute.models import (VirtualHardDisk,
                                       VirtualMachineScaleSet,
                                       VirtualMachineCaptureParameters,
                                       VirtualMachineScaleSetExtension,
                                       VirtualMachineScaleSetExtensionProfile)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import parse_resource_id, resource_id
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
from azure.cli.core._util import CLIError
import azure.cli.core.azlogging as azlogging
from ._vm_utils import read_content_if_is_file, load_json
from ._vm_diagnostics_templates import get_default_diag_config

from ._actions import (load_images_from_aliases_doc,
                       load_extension_images_thru_services,
                       load_images_thru_services)
from ._client_factory import _compute_client_factory

logger = azlogging.get_az_logger(__name__)


def get_resource_group_location(resource_group_name):
    from azure.mgmt.resource.resources import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location


def get_vm(resource_group_name, vm_name, expand=None):
    '''Retrieves a VM'''
    client = _compute_client_factory()
    return client.virtual_machines.get(resource_group_name,
                                       vm_name,
                                       expand=expand)


def set_vm(instance, lro_operation=None):
    '''Update the given Virtual Machine instance'''
    instance.resources = None  # Issue: https://github.com/Azure/autorest/issues/934
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
    parts = parse_resource_id(strid)
    return (parts['resource_group'], parts['name'])


# Use the same name by portal, so people can update from both cli and portal
# (VM doesn't allow multiple handlers for the same extension)
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
    _LINUX_DIAG_EXT: {
        'version': '2.3',
        'publisher': 'Microsoft.OSTCExtensions'
    },
    _WINDOWS_DIAG_EXT: {
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
        # pylint: disable=no-name-in-module,import-error
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
    # workaround a known issue: the version must only contain "major.minor", even though
    # "extension image list" gives more detail
    return '.'.join(version.split('.')[0:2])


# Hide extension information from output as the info is not correct and unhelpful; also
# commands using it mean to hide the extension concept from users.


class ExtensionUpdateLongRunningOperation(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        super(ExtensionUpdateLongRunningOperation, self).__call__(poller)
        # That said, we surppress the output. Operation failures will still
        # be caught through the base class
        return None


def list_vm(resource_group_name=None, show_details=False):
    ''' List Virtual Machines. '''
    ccf = _compute_client_factory()
    vm_list = ccf.virtual_machines.list(resource_group_name=resource_group_name) \
        if resource_group_name else ccf.virtual_machines.list_all()
    if show_details:
        return [get_vm_details(_parse_rg_name(v.id)[0], v.name) for v in vm_list]
    else:
        return list(vm_list)


def show_vm(resource_group_name, vm_name, show_details=False):
    if show_details:
        return get_vm_details(resource_group_name, vm_name)
    else:
        return get_vm(resource_group_name, vm_name)


def get_vm_details(resource_group_name, vm_name):
    from azure.mgmt.network import NetworkManagementClient
    result = get_instance_view(resource_group_name, vm_name)
    network_client = get_mgmt_service_client(NetworkManagementClient)
    public_ips = []
    fqdns = []
    private_ips = []
    mac_addresses = []
    # pylint: disable=line-too-long,no-member
    for nic_ref in result.network_profile.network_interfaces:
        nic = network_client.network_interfaces.get(resource_group_name, nic_ref.id.split('/')[-1])
        mac_addresses.append(nic.mac_address)
        for ip_configuration in nic.ip_configurations:
            private_ips.append(ip_configuration.private_ip_address)
            if ip_configuration.public_ip_address:
                res = parse_resource_id(ip_configuration.public_ip_address.id)
                public_ip_info = network_client.public_ip_addresses.get(res['resource_group'],
                                                                        res['name'])
                if public_ip_info.ip_address:
                    public_ips.append(public_ip_info.ip_address)
                if public_ip_info.dns_settings:
                    fqdns.append(public_ip_info.dns_settings.fqdn)

    setattr(result, 'power_state', ','.join([s.display_status for s in result.instance_view.statuses if s.code.startswith('PowerState/')]))
    setattr(result, 'public_ips', ','.join(public_ips))
    setattr(result, 'fqdns', ','.join(fqdns))
    setattr(result, 'private_ips', ','.join(private_ips))
    setattr(result, 'mac_addresses', ','.join(mac_addresses))
    del result.instance_view  # we don't need other instance_view info as people won't care
    return result


def list_vm_images(image_location=None, publisher_name=None, offer=None, sku=None,
                   all=False):  # pylint: disable=redefined-builtin
    '''vm image list
    :param str image_location:Image location
    :param str publisher_name:Image publisher name
    :param str offer:Image offer name
    :param str sku:Image sku name
    :param bool all:Retrieve image list from live Azure service rather using an offline image list
    '''
    load_thru_services = all

    if load_thru_services:
        all_images = load_images_thru_services(publisher_name, offer, sku, image_location)
    else:
        logger.warning(
            'You are viewing an offline list of images, use --all to retrieve an up-to-date list')
        all_images = load_images_from_aliases_doc(publisher_name, offer, sku)

    for i in all_images:
        i['urn'] = ':'.join([i['publisher'], i['offer'], i['sku'], i['version']])
    return all_images


def list_vm_extension_images(
        image_location=None, publisher_name=None, name=None, version=None, latest=False):
    '''vm extension image list
    :param str image_location:Image location
    :param str publisher_name:Image publisher name
    :param str name:Image name
    :param str version:Image version
    :param bool latest: Show the latest version only.
    '''
    return load_extension_images_thru_services(
        publisher_name, name, version, image_location, latest)


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
        same_resource_group_name = resource_group_name is None or \
            resource_group_name.lower() == nic_resource_group.lower()
        same_vm_name = vm_name is None or \
            vm_name.lower() == nic_vm_name.lower()
        if same_resource_group_name and same_vm_name:
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


def create_managed_disk(resource_group_name, disk_name, location=None,
                        size_gb=None, sku=None,
                        source=None,  # pylint: disable=unused-argument
                        # below are generated internally from 'source'
                        source_blob_uri=None, source_disk=None, source_snapshot=None):
    from azure.mgmt.compute.models import Disk, CreationData, DiskCreateOption, ImageDiskReference
    location = location or get_resource_group_location(resource_group_name)
    if source_blob_uri:
        option = DiskCreateOption.import_enum
    elif source_disk or source_snapshot:
        option = DiskCreateOption.copy  # pylint: disable=redefined-variable-type
    else:
        option = DiskCreateOption.empty

    creation_data = CreationData(option, source_uri=source_blob_uri,
                                 image_reference=None,
                                 source_resource_id=source_disk or source_snapshot)

    if size_gb is None and option == DiskCreateOption.empty:
        raise CLIError('usage error: --size-gb required to create an empty disk')

    disk = Disk(location, disk_size_gb=size_gb, creation_data=creation_data,
                account_type=sku)
    client = _compute_client_factory()
    return client.disks.create_or_update(resource_group_name, disk_name, disk)


def update_managed_disk(instance, size_gb=None, sku=None):
    if size_gb is not None:
        instance.disk_size_gb = size_gb
    if sku is not None:
        instance.account_type = sku
    return instance


def attach_managed_data_disk(resource_group_name, vm_name, disk,
                             new=False, sku=None, size_gb=None):
    '''attach a managed disk'''
    vm = get_vm(resource_group_name, vm_name)
    from azure.mgmt.compute.models import (CreationData, DiskCreateOptionTypes,
                                           ManagedDiskParameters, DataDisk)
    # pylint: disable=no-member
    luns = [d.lun for d in vm.storage_profile.data_disks] if vm.storage_profile.data_disks else []
    lun = max(luns) + 1 if luns else 1
    if new:
        if not size_gb:
            raise CLIError('usage error: --size-gb required to create an empty disk for attach')
        data_disk = DataDisk(lun, DiskCreateOptionTypes.empty,
                             name=parse_resource_id(disk)['name'],
                             disk_size_gb=size_gb)
    else:
        params = ManagedDiskParameters(id=disk,
                                       storage_account_type=sku)
        data_disk = DataDisk(lun, DiskCreateOptionTypes.attach, managed_disk=params)

    vm.storage_profile.data_disks.append(data_disk)
    set_vm(vm)


def detach_managed_data_disk(resource_group_name, vm_name, disk_name):
    '''detach a managed disk'''
    vm = get_vm(resource_group_name, vm_name)
    # pylint: disable=no-member
    matched = [d for d in vm.storage_profile.data_disks if d.name.lower() == disk_name.lower()]
    if not matched:
        raise CLIError('disk to remove is not found')
    for d in matched:
        vm.storage_profile.data_disks.remove(d)
    set_vm(vm)


def attach_managed_data_disk_to_vmss(resource_group_name, vmss_name, size_gb, lun=None):
    from azure.mgmt.compute.models import (DiskCreateOptionTypes,
                                           VirtualMachineScaleSetDataDisk)
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    # pylint: disable=no-member
    data_disks = vmss.virtual_machine_profile.storage_profile.data_disks or []
    if lun is None:
        luns = [d.lun for d in data_disks]
        lun = max(luns) + 1 if luns else 1
    data_disk = VirtualMachineScaleSetDataDisk(lun, DiskCreateOptionTypes.empty,
                                               disk_size_gb=size_gb)
    data_disks.append(data_disk)
    vmss.virtual_machine_profile.storage_profile.data_disks = data_disks
    return client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss_name, vmss)


def detach_disk_from_vmss(resource_group_name, vmss_name, lun):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    # pylint: disable=no-member
    data_disks = vmss.virtual_machine_profile.storage_profile.data_disks
    to_delete = [d for d in data_disks if d.lun == lun]
    if not to_delete:
        raise CLIError("Could not find the data disk with lun '{}'".format(lun))
    data_disks.remove(to_delete[0])
    return client.virtual_machine_scale_sets.create_or_update(resource_group_name,
                                                              vmss_name, vmss)


def grant_disk_access(resource_group_name, disk_name, duration_in_seconds):
    return _grant_access(resource_group_name, disk_name, duration_in_seconds, True)


def create_snapshot(resource_group_name, snapshot_name, location=None,
                    size_gb=None, sku=None,
                    source=None,  # pylint: disable=unused-argument
                    # below are generated internally from 'source'
                    source_blob_uri=None, source_disk=None, source_snapshot=None):
    from azure.mgmt.compute.models import (Snapshot, CreationData, DiskCreateOption,
                                           ImageDiskReference)
    location = location or get_resource_group_location(resource_group_name)
    if source_blob_uri:
        option = DiskCreateOption.import_enum
    elif source_disk or source_snapshot:
        option = DiskCreateOption.copy  # pylint: disable=redefined-variable-type
    else:
        option = DiskCreateOption.empty

    creation_data = CreationData(option, source_uri=source_blob_uri,
                                 image_reference=None,
                                 source_resource_id=source_disk or source_snapshot)

    if size_gb is None and option == DiskCreateOption.empty:
        raise CLIError('Please supply size for the snapshots')

    snapshot = Snapshot(location, disk_size_gb=size_gb, creation_data=creation_data,
                        account_type=sku)
    client = _compute_client_factory()
    return client.snapshots.create_or_update(resource_group_name, snapshot_name, snapshot)


def update_snapshot(instance, sku=None):
    if sku is not None:
        instance.account_type = sku
    return instance


def list_managed_disks(resource_group_name=None):
    client = _compute_client_factory()
    if resource_group_name:
        return client.disks.list_by_resource_group(resource_group_name)
    else:
        return client.disks.list()


def list_snapshots(resource_group_name=None):
    client = _compute_client_factory()
    if resource_group_name:
        return client.snapshots.list_by_resource_group(resource_group_name)
    else:
        return client.snapshots.list()


def grant_snapshot_access(resource_group_name, snapshot_name, duration_in_seconds):
    return _grant_access(resource_group_name, snapshot_name, duration_in_seconds, False)


def _grant_access(resource_group_name, name, duration_in_seconds, is_disk):
    from azure.mgmt.compute.models import AccessLevel
    client = _compute_client_factory()
    op = client.disks if is_disk else client.snapshots
    return op.grant_access(resource_group_name, name, AccessLevel.read, duration_in_seconds)


def list_images(resource_group_name=None):
    client = _compute_client_factory()
    if resource_group_name:
        return client.images.list_by_resource_group(resource_group_name)
    else:
        return client.images.list()


def create_image(resource_group_name, name, os_type=None, location=None,  # pylint: disable=too-many-locals,line-too-long
                 source=None, data_disk_sources=None,  # pylint: disable=unused-argument
                 # below are generated internally from 'source' and 'data_disk_sources'
                 source_virtual_machine=None,
                 os_blob_uri=None, data_blob_uris=None,
                 os_snapshot=None, data_snapshots=None,
                 os_disk=None, data_disks=None):
    from azure.mgmt.compute.models import (ImageOSDisk, ImageDataDisk, ImageStorageProfile, Image,
                                           OperatingSystemTypes, SubResource,
                                           OperatingSystemStateTypes)
    # pylint: disable=line-too-long
    if source_virtual_machine:
        location = location or get_resource_group_location(resource_group_name)
        image = Image(location, source_virtual_machine=SubResource(source_virtual_machine))
    else:
        os_disk = ImageOSDisk(os_type=os_type,
                              os_state=OperatingSystemStateTypes.generalized,
                              snapshot=SubResource(os_snapshot) if os_snapshot else None,
                              managed_disk=SubResource(os_disk) if os_disk else None,
                              blob_uri=os_blob_uri)
        all_data_disks = []
        lun = 1
        if data_blob_uris:
            for d in data_blob_uris:
                all_data_disks.append(ImageDataDisk(lun, blob_uri=d))
                lun += 1
        if data_snapshots:
            for d in data_snapshots:
                all_data_disks.append(ImageDataDisk(lun, snapshot=SubResource(d)))
                lun += 1
        if data_disks:
            for d in data_disks:
                all_data_disks.append(ImageDataDisk(lun, managed_disk=SubResource(d)))
                lun += 1

        image_storage_profile = image_storage_profile = ImageStorageProfile(os_disk=os_disk, data_disks=all_data_disks)
        location = location or get_resource_group_location(resource_group_name)
        # pylint disable=no-member
        image = Image(location, storage_profile=image_storage_profile)

    client = _compute_client_factory()
    return client.images.create_or_update(resource_group_name, name, image)


def attach_unmanaged_data_disk(resource_group_name, vm_name, new=False, vhd_uri=None, lun=None,
                               disk_name=None, size_gb=1023, caching=None):
    ''' Attach an unmanaged disk'''
    from azure.mgmt.compute.models.compute_management_client_enums import DiskCreateOptionTypes
    from azure.mgmt.compute.models import DataDisk
    if not new and not disk_name:
        raise CLIError('Pleae provide the name of the existing disk to attach')
    create_option = DiskCreateOptionTypes.empty if new else DiskCreateOptionTypes.attach

    vm = get_vm(resource_group_name, vm_name)
    if disk_name is None:
        import datetime
        disk_name = vm_name + '-' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # pylint: disable=no-member
    if vhd_uri is None:
        if not hasattr(vm.storage_profile.os_disk, 'vhd'):
            raise CLIError('Adding unmanaged disks to a VM with managed disks is not supported')
        blob_uri = vm.storage_profile.os_disk.vhd.uri
        vhd_uri = blob_uri[0:blob_uri.rindex('/') + 1] + disk_name + '.vhd'

    if lun is None:
        lun = _get_disk_lun(vm.storage_profile.data_disks)
    disk = DataDisk(lun=lun, vhd=VirtualHardDisk(vhd_uri), name=disk_name,
                    create_option=create_option,
                    caching=caching, disk_size_gb=size_gb if new else None)
    if vm.storage_profile.data_disks is None:
        vm.storage_profile.data_disks = []
    vm.storage_profile.data_disks.append(disk)
    return set_vm(vm)


def detach_unmanaged_data_disk(resource_group_name, vm_name, disk_name):
    ''' Detach a disk from a Virtual Machine '''
    vm = get_vm(resource_group_name, vm_name)
    # Issue: https://github.com/Azure/autorest/issues/934
    vm.resources = None
    try:
        # pylint: disable=no-member
        disk = next(d for d in vm.storage_profile.data_disks if
                    d.name.lower() == disk_name.lower())
        vm.storage_profile.data_disks.remove(disk)
    except (StopIteration, AttributeError):
        raise CLIError("No disk with the name '{}' found".format(disk_name))
    return set_vm(vm)


def _get_disk_lun(data_disks):
    # start from 0, search for unused int for lun
    if data_disks:
        existing_luns = sorted([d.lun for d in data_disks])
        for i in range(len(existing_luns)):  # pylint: disable=consider-using-enumerate
            if existing_luns[i] != i:
                return i
        return len(existing_luns)
    else:
        return 0


def resize_vm(resource_group_name, vm_name, size):
    '''Update vm size
    :param str size: sizes such as Standard_A4, Standard_F4s, etc
    '''
    vm = get_vm(resource_group_name, vm_name)
    vm.hardware_profile.vm_size = size  # pylint: disable=no-member
    return set_vm(vm)


def get_instance_view(resource_group_name, vm_name):
    return get_vm(resource_group_name, vm_name, 'instanceView')


def list_unmanaged_disks(resource_group_name, vm_name):
    ''' List disks for a Virtual Machine '''
    vm = get_vm(resource_group_name, vm_name)
    return vm.storage_profile.data_disks  # pylint: disable=no-member


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
    print(json.dumps(result.output, indent=2))  # pylint: disable=no-member


def reset_windows_admin(
        resource_group_name, vm_name, username, password):
    '''Update the password.
    You can only change the password. Adding a new user is not supported.
    '''
    vm = get_vm(resource_group_name, vm_name, 'instanceView')

    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    extension_name = _WINDOWS_ACCESS_EXT
    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm.resources, extension_name)

    ext = VirtualMachineExtension(vm.location,  # pylint: disable=no-member
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
    protected_settings = {}
    protected_settings['username'] = username
    if password:
        protected_settings['password'] = password
    elif not ssh_key_value and not password:  # default to ssh
        ssh_key_value = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')

    if ssh_key_value:
        protected_settings['ssh_key'] = read_content_if_is_file(ssh_key_value)

    poller = _update_linux_access_extension(resource_group_name, vm_name,
                                            protected_settings)
    return ExtensionUpdateLongRunningOperation('setting user', 'done')(poller)


def delete_linux_user(
        resource_group_name, vm_name, username):
    '''Remove the user '''
    poller = _update_linux_access_extension(resource_group_name, vm_name,
                                            {'remove_user': username})
    return ExtensionUpdateLongRunningOperation('deleting user', 'done')(poller)


def reset_linux_ssh(resource_group_name, vm_name):
    '''Reset the SSH configuration'''
    poller = _update_linux_access_extension(resource_group_name, vm_name,
                                            {'reset_ssh': True})
    return ExtensionUpdateLongRunningOperation('resetting SSH', 'done')(poller)


def _update_linux_access_extension(resource_group_name, vm_name, protected_settings):
    vm = get_vm(resource_group_name, vm_name, 'instanceView')
    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    extension_name = _LINUX_ACCESS_EXT
    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm.resources, extension_name)

    ext = VirtualMachineExtension(vm.location,  # pylint: disable=no-member
                                  publisher=publisher,
                                  virtual_machine_extension_type=extension_name,
                                  protected_settings=protected_settings,
                                  type_handler_version=version,
                                  settings={},
                                  auto_upgrade_minor_version=auto_upgrade)

    poller = client.virtual_machine_extensions.create_or_update(resource_group_name, vm_name,
                                                                _ACCESS_EXT_HANDLER_NAME, ext)
    return poller


def disable_boot_diagnostics(resource_group_name, vm_name):
    vm = get_vm(resource_group_name, vm_name)
    diag_profile = vm.diagnostics_profile
    if not (diag_profile and
            diag_profile.boot_diagnostics and
            diag_profile.boot_diagnostics.enabled):
        return

    # Issue: https://github.com/Azure/autorest/issues/934
    vm.resources = None
    diag_profile.boot_diagnostics.enabled = False
    diag_profile.boot_diagnostics.storage_uri = None
    set_vm(vm, ExtensionUpdateLongRunningOperation('disabling boot diagnostics', 'done'))


def enable_boot_diagnostics(resource_group_name, vm_name, storage):
    '''Enable boot diagnostics
    :param storage:a storage account name or a uri like
    https://your_stoage_account_name.blob.core.windows.net/
    '''
    vm = get_vm(resource_group_name, vm_name)
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
    set_vm(vm, ExtensionUpdateLongRunningOperation('enabling boot diagnostics', 'done'))


def get_boot_log(resource_group_name, vm_name):
    import sys
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
        keys.keys[0].value,
        endpoint_suffix=CLOUD.suffixes.storage_endpoint)  # pylint: disable=no-member

    class StreamWriter(object):  # pylint: disable=too-few-public-methods

        def __init__(self, out):
            self.out = out

        def write(self, str_or_bytes):
            if isinstance(str_or_bytes, bytes):
                self.out.write(str_or_bytes.decode())
            else:
                self.out.write(str_or_bytes)

    # our streamwriter not seekable, so no parallel.
    storage_client.get_blob_to_stream(container, blob, StreamWriter(sys.stdout), max_connections=1)


def list_extensions(resource_group_name, vm_name):
    vm = get_vm(resource_group_name, vm_name)
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
    :param settings: extension settings in json format. A json file path is also eccepted
    :param protected_settings: protected settings in json format for sensitive information like
    credentials. A json file path is also accepted.
    :param no_auto_upgrade: by doing this, extension system will not pick the highest minor version
    for the specified version number, and will not auto update to the latest build/revision number
    on any VM updates in future.
    '''
    vm = get_vm(resource_group_name, vm_name)
    client = _compute_client_factory()

    from azure.mgmt.compute.models import VirtualMachineExtension

    protected_settings = load_json(protected_settings) if protected_settings else {}
    settings = load_json(settings) if settings else None

    # pylint: disable=no-member
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

    protected_settings = load_json(protected_settings) if protected_settings else {}
    settings = load_json(settings) if settings else None

    # pylint: disable=no-member
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

        # with 'show_latest' enabled, we will only get one result.
        version = result[0]['version']

    version = _trim_away_build_number(version)
    return version


def set_diagnostics_extension(
        resource_group_name, vm_name, settings, protected_settings=None, version=None,
        no_auto_upgrade=False):
    '''Enable diagnostics on a virtual machine
    '''
    vm = get_vm(resource_group_name, vm_name)
    # pylint: disable=no-member
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
    # pylint: disable=no-member
    is_linux_os = _detect_os_type_for_diagnostics_ext(vmss.virtual_machine_profile.os_profile)
    vm_extension_name = _LINUX_DIAG_EXT if is_linux_os else _WINDOWS_DIAG_EXT
    return set_vmss_extension(resource_group_name, vmss_name, vm_extension_name,
                              extension_mappings[vm_extension_name]['publisher'],
                              version or extension_mappings[vm_extension_name]['version'],
                              settings,
                              protected_settings,
                              no_auto_upgrade)


# Same logic also applies on vmss


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
    # pylint: disable=no-member
    if not vmss.virtual_machine_profile.extension_profile:
        return
    return next((e for e in vmss.virtual_machine_profile.extension_profile.extensions
                 if e.name == extension_name), None)


def list_vmss_extensions(resource_group_name, vmss_name):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    # pylint: disable=no-member
    return None if not vmss.virtual_machine_profile.extension_profile \
        else vmss.virtual_machine_profile.extension_profile.extensions


def delete_vmss_extension(resource_group_name, vmss_name, extension_name):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vmss_name)
    # pylint: disable=no-member
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
    # pylint: disable=no-member
    keys = storage_mgmt_client.storage_accounts.list_keys(resource_group_name, storage_account).keys

    private_config = {
        'storageAccountName': storage_account,
        'storageAccountKey': keys[0].value
    }
    return private_config


def show_default_diagnostics_configuration(is_windows_os=False):
    '''show the default config file which defines data to be collected'''
    return get_default_diag_config(is_windows_os)


def vm_show_nic(resource_group_name, vm_name, nic):
    ''' Show details of a network interface configuration attached to a virtual machine '''
    vm = get_vm(resource_group_name, vm_name)
    found = next(
        (n for n in vm.network_profile.network_interfaces if nic.lower() == n.id.lower()), None  # pylint: disable=no-member
    )
    if found:
        from azure.mgmt.network import NetworkManagementClient
        network_client = get_mgmt_service_client(NetworkManagementClient)
        nic_name = parse_resource_id(found.id)['name']
        return network_client.network_interfaces.get(resource_group_name, nic_name)
    else:
        raise CLIError("NIC '{}' not found on VM '{}'".format(nic, vm_name))


def vm_list_nics(resource_group_name, vm_name):
    ''' List network interface configurations attached to a virtual machine '''
    vm = get_vm(resource_group_name, vm_name)
    return vm.network_profile.network_interfaces  # pylint: disable=no-member


def vm_add_nics(resource_group_name, vm_name, nics, primary_nic=None):
    ''' Add network interface configurations to the virtual machine
    :param str nic_ids: NIC resource IDs
    :param str nic_names: NIC names, assuming under the same resource group
    :param str primary_nic: name or id of the primary NIC. If missing, the first of the
    NIC list will be the primary
    '''
    vm = get_vm(resource_group_name, vm_name)
    new_nics = _build_nic_list(nics)
    existing_nics = _get_existing_nics(vm)
    return _update_vm_nics(vm, existing_nics + new_nics, primary_nic)


def vm_remove_nics(resource_group_name, vm_name, nics, primary_nic=None):
    ''' Remove network interface configurations from the virtual machine
    :param str nic_ids: NIC resource IDs
    :param str nic_names: NIC names, assuming under the same resource group
    :param str primary_nic: name or id of the primary NIC. If missing, the first of the
    NIC list will be the primary
    '''

    def to_delete(nic_id):
        return [n for n in nics_to_delete if n.id.lower() == nic_id.lower()]

    vm = get_vm(resource_group_name, vm_name)
    nics_to_delete = _build_nic_list(nics)
    existing_nics = _get_existing_nics(vm)
    survived = [x for x in existing_nics if not to_delete(x.id)]
    return _update_vm_nics(vm, survived, primary_nic)


def vm_set_nics(resource_group_name, vm_name, nics, primary_nic=None):
    ''' Replace existing network interface configurations on the virtual machine
    :param str nic_ids: NIC resource IDs
    :param str nic_names: NIC names, assuming under the same resource group
    :param str primary_nic: name or id of the primary nic. If missing, the first element of
    nic list will be set to the primary
    '''
    vm = get_vm(resource_group_name, vm_name)
    nics = _build_nic_list(nics)
    return _update_vm_nics(vm, nics, primary_nic)


# pylint: disable=no-member


def vm_open_port(resource_group_name, vm_name, port, priority=900, network_security_group_name=None,
                 apply_to_subnet=False):
    """ Opens a VM to inbound traffic on specified ports by adding a security rule to the network
    security group (NSG) that is attached to the VM's network interface (NIC) or subnet. The
    existing NSG will be used or a new one will be created. The rule name is 'open-port-{port}' and
    will overwrite an existing rule with this name. For multi-NIC VMs, or for more fine
    grained control, use the appropriate network commands directly (nsg rule create, etc).
    """
    from azure.mgmt.network import NetworkManagementClient
    network = get_mgmt_service_client(NetworkManagementClient)

    vm = get_vm(resource_group_name, vm_name)
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
    rule_name = 'open-port-all' if port == '*' else 'open-port-{}'.format(port)
    rule = SecurityRule(protocol='*', access='allow', direction='inbound', name=rule_name,
                        source_port_range='*', destination_port_range=port, priority=priority,
                        source_address_prefix='*', destination_address_prefix='*')
    nsg_name = nsg.name or os.path.split(nsg.id)[1]
    LongRunningOperation('Adding security rule')(
        network.security_rules.create_or_update(
            resource_group_name, nsg_name, rule_name, rule)
    )

    # update the NIC or subnet
    if not apply_to_subnet:
        nic.network_security_group = nsg
        return LongRunningOperation('Updating NIC')(
            network.network_interfaces.create_or_update(
                resource_group_name, nic.name, nic)
        )
    else:
        subnet.network_security_group = nsg
        return LongRunningOperation('Updating subnet')(
            network.subnets.create_or_update(
                resource_group_name=resource_group_name,
                virtual_network_name=subnet_id['name'],
                subnet_name=subnet_id['child_name'],
                subnet_parameters=subnet
            )
        )


def _build_nic_list(nic_ids):
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.compute.models import NetworkInterfaceReference
    nic_list = []
    if nic_ids:
        # pylint: disable=no-member
        network_client = get_mgmt_service_client(NetworkManagementClient)
        for nic_id in nic_ids:
            rg, name = _parse_rg_name(nic_id)
            nic = network_client.network_interfaces.get(rg, name)
            nic_list.append(NetworkInterfaceReference(nic.id, False))
    return nic_list


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

    return set_vm(vm).network_profile.network_interfaces


def scale_vmss(resource_group_name, vm_scale_set_name, new_capacity):
    '''change the number of VMs in an virtual machine scale set

    :param int new_capacity: number of virtual machines in a scale set
    '''
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vm_scale_set_name)
    # pylint: disable=no-member
    if vmss.sku.capacity == new_capacity:
        return
    else:
        vmss.sku.capacity = new_capacity
    vmss_new = VirtualMachineScaleSet(vmss.location, sku=vmss.sku)
    return client.virtual_machine_scale_sets.create_or_update(resource_group_name,
                                                              vm_scale_set_name,
                                                              vmss_new)


def update_vmss_instances(resource_group_name, vm_scale_set_name, instance_ids):
    '''upgrade virtual machines in a virtual machine scale set'''
    client = _compute_client_factory()
    return client.virtual_machine_scale_sets.update_instances(resource_group_name,
                                                              vm_scale_set_name,
                                                              instance_ids)


def get_vmss_instance_view(resource_group_name, vm_scale_set_name, instance_id=None):
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


def show_vmss(resource_group_name, vm_scale_set_name, instance_id=None):
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


def list_vmss(resource_group_name=None):
    '''list scale sets'''
    client = _compute_client_factory()
    if resource_group_name:
        return client.virtual_machine_scale_sets.list(resource_group_name)
    else:
        return client.virtual_machine_scale_sets.list_all()


def deallocate_vmss(resource_group_name, vm_scale_set_name, instance_ids=None):
    '''deallocate virtual machines in a scale set. '''
    client = _compute_client_factory()
    if instance_ids and len(instance_ids) == 1:
        return client.virtual_machine_scale_set_vms.deallocate(resource_group_name,
                                                               vm_scale_set_name,
                                                               instance_ids[0])
    else:
        return client.virtual_machine_scale_sets.deallocate(resource_group_name,
                                                            vm_scale_set_name,
                                                            instance_ids=instance_ids)


def delete_vmss_instances(resource_group_name, vm_scale_set_name, instance_ids):
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


def stop_vmss(resource_group_name, vm_scale_set_name, instance_ids=None):
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


def reimage_vmss(resource_group_name, vm_scale_set_name, instance_id=None):
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


def restart_vmss(resource_group_name, vm_scale_set_name, instance_ids=None):
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


def start_vmss(resource_group_name, vm_scale_set_name, instance_ids=None):
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


def list_vmss_instance_connection_info(resource_group_name, vm_scale_set_name):
    client = _compute_client_factory()
    vmss = client.virtual_machine_scale_sets.get(resource_group_name,
                                                 vm_scale_set_name)
    # find the load balancer
    nic_configs = vmss.virtual_machine_profile.network_profile.network_interface_configurations
    primary_nic_config = next(n for n in nic_configs if n.primary)
    if primary_nic_config is None:
        raise CLIError('could not find a primary nic which is needed to search to load balancer')
    ip_configs = primary_nic_config.ip_configurations
    ip_config = next((ip for ip in ip_configs if ip.load_balancer_inbound_nat_pools), None)
    if not ip_config:
        raise CLIError('No load-balancer exist to retrieve public ip address')
    res_id = ip_config.load_balancer_inbound_nat_pools[0].id
    lb_info = parse_resource_id(res_id)
    lb_name = lb_info['name']
    lb_rg = lb_info['resource_group']

    # get public ip
    from azure.mgmt.network import NetworkManagementClient
    network_client = get_mgmt_service_client(NetworkManagementClient)
    lb = network_client.load_balancers.get(lb_rg, lb_name)
    res_id = lb.frontend_ip_configurations[0].public_ip_address.id  # TODO: will this always work?
    public_ip_info = parse_resource_id(res_id)
    public_ip_name = public_ip_info['name']
    public_ip_rg = public_ip_info['resource_group']
    public_ip = network_client.public_ip_addresses.get(public_ip_rg, public_ip_name)
    public_ip_address = public_ip.ip_address

    # loop around inboundnatrule
    instance_addresses = []
    for rule in lb.inbound_nat_rules:
        instance_addresses.append('{}:{}'.format(public_ip_address, rule.frontend_port))

    return instance_addresses


def availset_get(resource_group_name, name):
    return _compute_client_factory().availability_sets.get(resource_group_name, name)


def availset_set(**kwargs):
    return _compute_client_factory().availability_sets.create_or_update(**kwargs)


def vmss_get(resource_group_name, name):
    return _compute_client_factory().virtual_machine_scale_sets.get(resource_group_name, name)


def vmss_set(**kwargs):
    return _compute_client_factory().virtual_machine_scale_sets.create_or_update(**kwargs)


def convert_av_set_to_managed_disk(resource_group_name, availability_set_name):
    av_set = availset_get(resource_group_name, availability_set_name)
    if av_set.sku.name != 'Aligned':
        av_set.sku.name = 'Aligned'
        return availset_set(resource_group_name=resource_group_name, name=availability_set_name,
                            parameters=av_set)


def update_acs(resource_group_name, container_service_name, new_agent_count):
    client = _compute_client_factory()
    instance = client.container_services.get(resource_group_name, container_service_name)
    instance.agent_pool_profiles[0].count = new_agent_count
    return client.container_services.create_or_update(resource_group_name,
                                                      container_service_name, instance)


def list_container_services(client, resource_group_name=None):
    ''' List Container Services. '''
    svc_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(svc_list)


# pylint: disable=too-many-locals, unused-argument, too-many-statements
def create_vm(vm_name, resource_group_name, image=None,
              size='Standard_DS1', location=None, tags=None, no_wait=False,
              authentication_type=None, admin_password=None, admin_username=getpass.getuser(),
              ssh_dest_key_path=None, ssh_key_value=None, generate_ssh_keys=False,
              availability_set=None,
              nics=None, nsg=None, nsg_rule=None,
              private_ip_address=None,
              public_ip_address=None, public_ip_address_allocation='dynamic',
              public_ip_address_dns_name=None,
              os_disk_name=None, os_type=None, storage_account=None,
              storage_caching='ReadWrite', storage_container_name='vhds',
              storage_sku='Standard_LRS', use_unmanaged_disk=False,
              managed_os_disk=None, data_disk_sizes_gb=None, image_data_disks=None,
              vnet_name=None, vnet_address_prefix='10.0.0.0/16',
              subnet=None, subnet_address_prefix='10.0.0.0/24', storage_profile=None,
              os_publisher=None, os_offer=None, os_sku=None, os_version=None,
              storage_account_type=None, vnet_type=None, nsg_type=None, public_ip_type=None,
              nic_type=None, validate=False):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.command_modules.vm._vm_utils import random_string
    from azure.cli.command_modules.vm._template_builder import (
        ArmTemplateBuilder, build_vm_resource, build_storage_account_resource, build_nic_resource,
        build_vnet_resource, build_nsg_resource, build_public_ip_resource,
        build_output_deployment_resource, build_deployment_resource, StorageProfile)

    from azure.cli.core._profile import CLOUD
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.resources.models import DeploymentProperties, TemplateLink

    network_id_template = resource_id(
        subscription=get_subscription_id(), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    # determine final defaults and calculated values
    tags = tags or {}
    os_disk_name = os_disk_name or 'osdisk_{}'.format(random_string(10))

    # Build up the ARM template
    master_template = ArmTemplateBuilder()

    vm_dependencies = []
    if storage_account_type == 'new':
        storage_account = storage_account or 'vhdstorage{}'.format(
            random_string(14, force_lower=True))
        vm_dependencies.append('Microsoft.Storage/storageAccounts/{}'.format(storage_account))
        master_template.add_resource(build_storage_account_resource(storage_account, location,
                                                                    tags, storage_sku))

    nic_name = None
    if nic_type == 'new':
        nic_name = '{}VMNic'.format(vm_name)
        vm_dependencies.append('Microsoft.Network/networkInterfaces/{}'.format(nic_name))

        nic_dependencies = []
        if vnet_type == 'new':
            vnet_name = vnet_name or '{}VNET'.format(vm_name)
            subnet = subnet or '{}Subnet'.format(vm_name)
            nic_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(vnet_name))
            master_template.add_resource(build_vnet_resource(
                vnet_name, location, tags, vnet_address_prefix, subnet, subnet_address_prefix))

        if nsg_type == 'new':
            nsg_rule_type = 'rdp' if os_type.lower() == 'windows' else 'ssh'
            nsg = nsg or '{}NSG'.format(vm_name)
            nic_dependencies.append('Microsoft.Network/networkSecurityGroups/{}'.format(nsg))
            master_template.add_resource(build_nsg_resource(nsg, location, tags, nsg_rule_type))

        if public_ip_type == 'new':
            public_ip_address = public_ip_address or '{}PublicIP'.format(vm_name)
            nic_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(
                public_ip_address))
            master_template.add_resource(build_public_ip_resource(public_ip_address, location,
                                                                  tags,
                                                                  public_ip_address_allocation,
                                                                  public_ip_address_dns_name))

        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(
            network_id_template, vnet_name, subnet)
        nsg_id = '{}/networkSecurityGroups/{}'.format(network_id_template, nsg) if nsg else None
        public_ip_address_id = \
            '{}/publicIPAddresses/{}'.format(network_id_template, public_ip_address) \
            if public_ip_address else None
        nics = [
            {'id': '{}/networkInterfaces/{}'.format(network_id_template, nic_name)}
        ]
        nic_resource = build_nic_resource(
            nic_name, location, tags, vm_name, subnet_id, private_ip_address, nsg_id,
            public_ip_address_id)
        nic_resource['dependsOn'] = nic_dependencies
        master_template.add_resource(nic_resource)
    else:
        # Using an existing NIC
        invalid_parameters = [nsg, public_ip_address, subnet, vnet_name]
        if any(invalid_parameters):
            raise CLIError('When specifying an existing NIC, do not specify NSG, '
                           'public IP, VNet or subnet.')

    os_vhd_uri = None
    if storage_profile in [StorageProfile.SACustomImage, StorageProfile.SAPirImage]:
        storage_account_name = storage_account.rsplit('/', 1)
        storage_account_name = storage_account_name[1] if \
            len(storage_account_name) > 1 else storage_account_name[0]
        os_vhd_uri = 'https://{}.blob.{}/{}/{}.vhd'.format(
            storage_account_name, CLOUD.suffixes.storage_endpoint, storage_container_name,
            os_disk_name)

    vm_resource = build_vm_resource(
        vm_name, location, tags, size, storage_profile, nics, admin_username, availability_set,
        admin_password, ssh_key_value, ssh_dest_key_path, image, os_disk_name,
        os_type, storage_caching, storage_sku, os_publisher, os_offer, os_sku, os_version,
        os_vhd_uri, managed_os_disk, data_disk_sizes_gb, image_data_disks)
    vm_resource['dependsOn'] = vm_dependencies

    master_template.add_resource(vm_resource)

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'vm_deploy_' + random_string(32)
    client = get_mgmt_service_client(ResourceManagementClient).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    if validate:
        return client.validate(resource_group_name, deployment_name, properties, raw=no_wait)

    # creates the VM deployment
    if no_wait:
        return client.create_or_update(
            resource_group_name, deployment_name, properties, raw=no_wait)
    else:
        LongRunningOperation()(client.create_or_update(
            resource_group_name, deployment_name, properties, raw=no_wait))
    return get_vm_details(resource_group_name, vm_name)


# pylint: disable=too-many-locals, too-many-statements
def create_vmss(vmss_name, resource_group_name, image,
                disable_overprovision=False, instance_count=2,
                location=None, tags=None, upgrade_policy_mode='manual', validate=False,
                admin_username=getpass.getuser(), admin_password=None, authentication_type=None,
                vm_sku="Standard_D1_v2", no_wait=False,
                ssh_dest_key_path=None, ssh_key_value=None, generate_ssh_keys=False,
                load_balancer=None, backend_pool_name=None, nat_pool_name=None, backend_port=None,
                public_ip_address=None, public_ip_address_allocation='dynamic',
                public_ip_address_dns_name=None,
                storage_caching='ReadOnly',
                storage_container_name='vhds', storage_sku='Standard_LRS',
                os_type=None, os_disk_name=None,
                use_unmanaged_disk=False, data_disk_sizes_gb=None, image_data_disks=None,
                vnet_name=None, vnet_address_prefix='10.0.0.0/16',
                subnet=None, subnet_address_prefix=None,
                os_offer=None, os_publisher=None, os_sku=None, os_version=None,
                load_balancer_type=None, vnet_type=None, public_ip_type=None, storage_profile=None,
                single_placement_group=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.command_modules.vm._vm_utils import random_string
    from azure.cli.command_modules.vm._template_builder import (
        ArmTemplateBuilder, StorageProfile, build_vmss_resource, build_storage_account_resource,
        build_vnet_resource, build_public_ip_resource, build_load_balancer_resource,
        build_output_deployment_resource, build_deployment_resource,
        build_vmss_storage_account_pool_resource)

    from azure.cli.core._profile import CLOUD
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.resources.models import DeploymentProperties, TemplateLink

    network_id_template = resource_id(
        subscription=get_subscription_id(), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    # determine final defaults and calculated values
    tags = tags or {}
    os_disk_name = os_disk_name or 'osdisk_{}'.format(random_string(10))

    # Build up the ARM template
    master_template = ArmTemplateBuilder()

    vmss_dependencies = []
    if vnet_type == 'new':
        vnet_name = vnet_name or '{}VNET'.format(vmss_name)
        subnet = subnet or '{}Subnet'.format(vmss_name)
        vmss_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(vnet_name))
        master_template.add_resource(build_vnet_resource(
            vnet_name, location, tags, vnet_address_prefix, subnet, subnet_address_prefix))
    subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template, vnet_name, subnet)

    if load_balancer_type == 'new':
        load_balancer = load_balancer or '{}LB'.format(vmss_name)
        vmss_dependencies.append('Microsoft.Network/loadBalancers/{}'.format(load_balancer))

        lb_dependencies = []
        if public_ip_type == 'new':
            public_ip_address = public_ip_address or '{}PublicIP'.format(load_balancer)
            lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))  # pylint: disable=line-too-long
            master_template.add_resource(build_public_ip_resource(public_ip_address, location,
                                                                  tags,
                                                                  public_ip_address_allocation,
                                                                  public_ip_address_dns_name))
        public_ip_address_id = '{}/publicIPAddresses/{}'.format(network_id_template, public_ip_address) if public_ip_address else None  # pylint: disable=line-too-long

        # calculate default names if not provided
        backend_pool_name = backend_pool_name or '{}BEPool'.format(load_balancer)
        nat_pool_name = nat_pool_name or '{}NatPool'.format(load_balancer)
        if not backend_port:
            backend_port = 3389 if os_type == 'windows' else 22

        lb_resource = build_load_balancer_resource(
            load_balancer, location, tags, backend_pool_name, nat_pool_name, backend_port,
            'loadBalancerFrontEnd', public_ip_address_id, subnet_id)
        lb_resource['dependsOn'] = lb_dependencies
        master_template.add_resource(lb_resource)

    if storage_profile in [StorageProfile.SACustomImage, StorageProfile.SAPirImage]:
        master_template.add_resource(build_vmss_storage_account_pool_resource(
            'storageLoop', location, tags, storage_sku))
        vmss_dependencies.append('storageLoop')

    scrubbed_name = vmss_name.replace('-', '').lower()[:5]
    naming_prefix = '{}{}'.format(scrubbed_name,
                                  random_string(9 - len(scrubbed_name), force_lower=True))
    backend_address_pool_id = '{}/loadBalancers/{}/backendAddressPools/{}'.format(
        network_id_template, load_balancer, backend_pool_name) if load_balancer_type else None
    inbound_nat_pool_id = '{}/loadBalancers/{}/inboundNatPools/{}'.format(
        network_id_template, load_balancer, nat_pool_name) if load_balancer_type == 'new' else None
    ip_config_name = '{}IPConfig'.format(naming_prefix)
    nic_name = '{}Nic'.format(naming_prefix)

    vmss_resource = build_vmss_resource(vmss_name, naming_prefix, location, tags,
                                        not disable_overprovision, upgrade_policy_mode,
                                        vm_sku, instance_count,
                                        ip_config_name, nic_name, subnet_id, admin_username,
                                        authentication_type, storage_profile,
                                        os_disk_name, storage_caching,
                                        storage_sku, data_disk_sizes_gb, image_data_disks,
                                        os_type, image, admin_password,
                                        ssh_key_value, ssh_dest_key_path,
                                        os_publisher, os_offer, os_sku, os_version,
                                        backend_address_pool_id, inbound_nat_pool_id,
                                        single_placement_group=single_placement_group)
    vmss_resource['dependsOn'] = vmss_dependencies

    master_template.add_resource(vmss_resource)
    master_template.add_variable('storageAccountNames', [
        '{}{}'.format(naming_prefix, x) for x in range(5)
    ])
    master_template.add_variable('vhdContainers', [
        "[concat('https://', variables('storageAccountNames')[{}], '.blob.{}/{}')]".format(
            x, CLOUD.suffixes.storage_endpoint, storage_container_name) for x in range(5)
    ])
    master_template.add_output('VMSS', vmss_name, 'Microsoft.Compute', 'virtualMachineScaleSets',
                               output_type='object')
    template = master_template.build()

    # deploy ARM template
    deployment_name = 'vmss_deploy_' + random_string(32)
    client = get_mgmt_service_client(ResourceManagementClient).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    if validate:
        return client.validate(resource_group_name, deployment_name, properties, raw=no_wait)

    # creates the VMSS deployment
    return client.create_or_update(resource_group_name, deployment_name, properties, raw=no_wait)


def create_av_set(availability_set_name, resource_group_name, location=None, no_wait=False,
                  platform_update_domain_count=5, platform_fault_domain_count=5,
                  unmanaged=False, tags=None, validate=False):
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.resources.models import DeploymentProperties, TemplateLink
    from azure.cli.command_modules.vm._vm_utils import random_string
    from azure.cli.command_modules.vm._template_builder import (ArmTemplateBuilder,
                                                                build_av_set_resource)

    tags = tags or {}

    # Build up the ARM template
    master_template = ArmTemplateBuilder()

    av_set_resource = build_av_set_resource(availability_set_name, location, tags,
                                            platform_update_domain_count,
                                            platform_fault_domain_count, unmanaged)
    master_template.add_resource(av_set_resource)

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'av_set_deploy_' + random_string(32)
    client = get_mgmt_service_client(ResourceManagementClient).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    if validate:
        return client.validate(resource_group_name, deployment_name, properties)

    LongRunningOperation()(client.create_or_update(
        resource_group_name, deployment_name, properties, raw=no_wait))
    compute_client = _compute_client_factory()
    return compute_client.availability_sets.get(resource_group_name, availability_set_name)
