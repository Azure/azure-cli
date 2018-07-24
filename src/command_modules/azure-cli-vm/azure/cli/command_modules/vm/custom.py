# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-lines
from __future__ import print_function
import getpass
import json
import os

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

# the urlopen is imported for automation purpose
from six.moves.urllib.request import urlopen  # noqa, pylint: disable=import-error,unused-import,ungrouped-imports

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.command_modules.vm._validators import _get_resource_group_from_vault_name
from azure.cli.core.commands.validators import validate_file_or_dict

from azure.cli.core.commands import LongRunningOperation, DeploymentOutputLongRunningOperation
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_data_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait

from ._vm_utils import read_content_if_is_file
from ._vm_diagnostics_templates import get_default_diag_config

from ._actions import (load_images_from_aliases_doc, load_extension_images_thru_services,
                       load_images_thru_services, _get_latest_image_version)
from ._client_factory import _compute_client_factory, cf_public_ip_addresses

logger = get_logger(__name__)


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
        'version': '3.0',
        'publisher': 'Microsoft.Azure.Diagnostics'
    },
    _WINDOWS_DIAG_EXT: {
        'version': '1.5',
        'publisher': 'Microsoft.Azure.Diagnostics'
    }
}


def _construct_identity_info(identity_scope, identity_role, implicit_identity, external_identities):
    info = {}
    if identity_scope:
        info['scope'] = identity_scope
        info['role'] = str(identity_role)  # could be DefaultStr, so convert to string
    info['userAssignedIdentities'] = external_identities or {}
    info['systemAssignedIdentity'] = implicit_identity or ''
    return info


# for injecting test seams to produce predicatable role assignment id for playback
def _gen_guid():
    import uuid
    return uuid.uuid4()


def _get_access_extension_upgrade_info(extensions, name):
    version = extension_mappings[name]['version']
    publisher = extension_mappings[name]['publisher']

    auto_upgrade = None

    if extensions:
        extension = next((e for e in extensions if e.name == name), None)
        from distutils.version import LooseVersion  # pylint: disable=no-name-in-module,import-error
        if extension and LooseVersion(extension.type_handler_version) < LooseVersion(version):
            auto_upgrade = True
        elif extension and LooseVersion(extension.type_handler_version) > LooseVersion(version):
            version = extension.type_handler_version

    return publisher, version, auto_upgrade


def _get_extension_instance_name(instance_view, publisher, extension_type_name,
                                 suggested_name=None):
    extension_instance_name = suggested_name or extension_type_name
    full_type_name = '.'.join([publisher, extension_type_name])
    if instance_view.extensions:
        ext = next((x for x in instance_view.extensions
                    if x.type and (x.type.lower() == full_type_name.lower())), None)
        if ext:
            extension_instance_name = ext.name
    return extension_instance_name


def _get_storage_management_client(cli_ctx):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)


def _get_disk_lun(data_disks):
    # start from 0, search for unused int for lun
    if not data_disks:
        return 0

    existing_luns = sorted([d.lun for d in data_disks])
    for i, current in enumerate(existing_luns):
        if current != i:
            return i
    return len(existing_luns)


def _get_private_config(cli_ctx, resource_group_name, storage_account):
    storage_mgmt_client = _get_storage_management_client(cli_ctx)
    # pylint: disable=no-member
    keys = storage_mgmt_client.storage_accounts.list_keys(resource_group_name, storage_account).keys

    private_config = {
        'storageAccountName': storage_account,
        'storageAccountKey': keys[0].value
    }
    return private_config


def _get_resource_group_location(cli_ctx, resource_group_name):
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location


def _get_sku_object(cmd, sku):
    if cmd.supported_api_version(min_api='2017-03-30'):
        DiskSku = cmd.get_models('DiskSku')
        return DiskSku(name=sku)
    return sku


def _grant_access(cmd, resource_group_name, name, duration_in_seconds, is_disk):
    AccessLevel = cmd.get_models('AccessLevel')
    client = _compute_client_factory(cmd.cli_ctx)
    op = client.disks if is_disk else client.snapshots
    return op.grant_access(resource_group_name, name, AccessLevel.read, duration_in_seconds)


def _is_linux_os(vm):
    os_type = vm.storage_profile.os_disk.os_type.value if vm.storage_profile.os_disk.os_type else None
    if os_type:
        return os_type.lower() == 'linux'
    # the os_type could be None for VM scaleset, let us check out os configurations
    if vm.os_profile.linux_configuration:
        return bool(vm.os_profile.linux_configuration)
    return False


def _merge_secrets(secrets):
    """
    Merge a list of secrets. Each secret should be a dict fitting the following JSON structure:
    [{ "sourceVault": { "id": "value" },
        "vaultCertificates": [{ "certificateUrl": "value",
        "certificateStore": "cert store name (only on windows)"}] }]
    The array of secrets is merged on sourceVault.id.
    :param secrets:
    :return:
    """
    merged = {}
    vc_name = 'vaultCertificates'
    for outer in secrets:
        for secret in outer:
            if secret['sourceVault']['id'] not in merged:
                merged[secret['sourceVault']['id']] = []
            merged[secret['sourceVault']['id']] = \
                secret[vc_name] + merged[secret['sourceVault']['id']]

    # transform the reduced map to vm format
    formatted = [{'sourceVault': {'id': source_id},
                  'vaultCertificates': value}
                 for source_id, value in list(merged.items())]
    return formatted


def _normalize_extension_version(cli_ctx, publisher, vm_extension_name, version, location):

    def _trim_away_build_number(version):
        # workaround a known issue: the version must only contain "major.minor", even though
        # "extension image list" gives more detail
        return '.'.join(version.split('.')[0:2])

    if not version:
        result = load_extension_images_thru_services(cli_ctx, publisher, vm_extension_name, None, location,
                                                     show_latest=True, partial_match=False)
        if not result:
            raise CLIError('Failed to find the latest version for the extension "{}"'.format(vm_extension_name))
        # with 'show_latest' enabled, we will only get one result.
        version = result[0]['version']

    version = _trim_away_build_number(version)
    return version


def _parse_rg_name(strid):
    '''From an ID, extract the contained (resource group, name) tuple.'''
    from msrestazure.tools import parse_resource_id
    parts = parse_resource_id(strid)
    return (parts['resource_group'], parts['name'])


def _set_sku(cmd, instance, sku):
    if cmd.supported_api_version(min_api='2017-03-30'):
        instance.sku = cmd.get_models('DiskSku')(name=sku)
    else:
        instance.account_type = sku


def _show_missing_access_warning(resource_group, name, command):
    warn = ("No access was given yet to the '{1}', because '--scope' was not provided. "
            "You should setup by creating a role assignment, e.g. "
            "'az role assignment create --assignee <principal-id> --role contributor -g {0}' "
            "would let it access the current resource group. To get the pricipal id, run "
            "'az {2} show -g {0} -n {1} --query \"identity.principalId\" -otsv'".format(resource_group, name, command))
    logger.warning(warn)


# Hide extension information from output as the info is not correct and unhelpful; also
# commands using it mean to hide the extension concept from users.


class ExtensionUpdateLongRunningOperation(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        super(ExtensionUpdateLongRunningOperation, self).__call__(poller)
        # That said, we suppress the output. Operation failures will still
        # be caught through the base class
        return None


# region Disks (Managed)
def create_managed_disk(cmd, resource_group_name, disk_name, location=None,
                        size_gb=None, sku='Premium_LRS',
                        source=None,  # pylint: disable=unused-argument
                        # below are generated internally from 'source'
                        source_blob_uri=None, source_disk=None, source_snapshot=None,
                        source_storage_account_id=None, no_wait=False, tags=None, zone=None):
    Disk, CreationData, DiskCreateOption = cmd.get_models('Disk', 'CreationData', 'DiskCreateOption')

    location = location or _get_resource_group_location(cmd.cli_ctx, resource_group_name)
    if source_blob_uri:
        option = DiskCreateOption.import_enum
    elif source_disk or source_snapshot:
        option = DiskCreateOption.copy
    else:
        option = DiskCreateOption.empty

    creation_data = CreationData(create_option=option, source_uri=source_blob_uri,
                                 image_reference=None,
                                 source_resource_id=source_disk or source_snapshot,
                                 storage_account_id=source_storage_account_id)

    if size_gb is None and option == DiskCreateOption.empty:
        raise CLIError('usage error: --size-gb required to create an empty disk')
    disk = Disk(location=location, creation_data=creation_data, tags=(tags or {}),
                sku=_get_sku_object(cmd, sku), disk_size_gb=size_gb)
    if zone:
        disk.zones = zone

    client = _compute_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.disks.create_or_update, resource_group_name, disk_name, disk)


def grant_disk_access(cmd, resource_group_name, disk_name, duration_in_seconds):
    return _grant_access(cmd, resource_group_name, disk_name, duration_in_seconds, True)


def list_managed_disks(cmd, resource_group_name=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.disks.list_by_resource_group(resource_group_name)
    return client.disks.list()


def update_managed_disk(cmd, instance, size_gb=None, sku=None):
    if size_gb is not None:
        instance.disk_size_gb = size_gb
    if sku is not None:
        _set_sku(cmd, instance, sku)
    return instance
# endregion


# region Images (Managed)
def create_image(cmd, resource_group_name, name, source, os_type=None, data_disk_sources=None, location=None,  # pylint: disable=too-many-locals,unused-argument
                 # below are generated internally from 'source' and 'data_disk_sources'
                 source_virtual_machine=None,
                 os_blob_uri=None, data_blob_uris=None,
                 os_snapshot=None, data_snapshots=None,
                 os_disk=None, data_disks=None, tags=None, zone_resilient=None):
    ImageOSDisk, ImageDataDisk, ImageStorageProfile, Image, SubResource, OperatingSystemStateTypes = cmd.get_models(
        'ImageOSDisk', 'ImageDataDisk', 'ImageStorageProfile', 'Image', 'SubResource', 'OperatingSystemStateTypes')

    if source_virtual_machine:
        location = location or _get_resource_group_location(cmd.cli_ctx, resource_group_name)
        image_storage_profile = None if zone_resilient is None else ImageStorageProfile(zone_resilient=zone_resilient)
        image = Image(location=location, source_virtual_machine=SubResource(id=source_virtual_machine),
                      storage_profile=image_storage_profile, tags=(tags or {}))
    else:
        os_disk = ImageOSDisk(os_type=os_type,
                              os_state=OperatingSystemStateTypes.generalized,
                              snapshot=SubResource(id=os_snapshot) if os_snapshot else None,
                              managed_disk=SubResource(id=os_disk) if os_disk else None,
                              blob_uri=os_blob_uri)
        all_data_disks = []
        lun = 0
        if data_blob_uris:
            for d in data_blob_uris:
                all_data_disks.append(ImageDataDisk(lun=lun, blob_uri=d))
                lun += 1
        if data_snapshots:
            for d in data_snapshots:
                all_data_disks.append(ImageDataDisk(lun=lun, snapshot=SubResource(id=d)))
                lun += 1
        if data_disks:
            for d in data_disks:
                all_data_disks.append(ImageDataDisk(lun=lun, managed_disk=SubResource(id=d)))
                lun += 1

        image_storage_profile = ImageStorageProfile(os_disk=os_disk, data_disks=all_data_disks)
        if zone_resilient is not None:
            image_storage_profile.zone_resilient = zone_resilient
        location = location or _get_resource_group_location(cmd.cli_ctx, resource_group_name)
        # pylint disable=no-member
        image = Image(location=location, storage_profile=image_storage_profile, tags=(tags or {}))

    client = _compute_client_factory(cmd.cli_ctx)
    return client.images.create_or_update(resource_group_name, name, image)


def list_images(cmd, resource_group_name=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.images.list_by_resource_group(resource_group_name)
    return client.images.list()
# endregion


# region Snapshots
def create_snapshot(cmd, resource_group_name, snapshot_name, location=None, size_gb=None, sku='Standard_LRS',
                    source=None,  # pylint: disable=unused-argument
                    # below are generated internally from 'source'
                    source_blob_uri=None, source_disk=None, source_snapshot=None, source_storage_account_id=None,
                    tags=None):
    Snapshot, CreationData, DiskCreateOption = cmd.get_models('Snapshot', 'CreationData', 'DiskCreateOption')

    location = location or _get_resource_group_location(cmd.cli_ctx, resource_group_name)
    if source_blob_uri:
        option = DiskCreateOption.import_enum
    elif source_disk or source_snapshot:
        option = DiskCreateOption.copy
    else:
        option = DiskCreateOption.empty

    creation_data = CreationData(create_option=option, source_uri=source_blob_uri,
                                 image_reference=None,
                                 source_resource_id=source_disk or source_snapshot,
                                 storage_account_id=source_storage_account_id)

    if size_gb is None and option == DiskCreateOption.empty:
        raise CLIError('Please supply size for the snapshots')

    snapshot = Snapshot(location=location, creation_data=creation_data, tags=(tags or {}),
                        sku=_get_sku_object(cmd, sku), disk_size_gb=size_gb)
    client = _compute_client_factory(cmd.cli_ctx)
    return client.snapshots.create_or_update(resource_group_name, snapshot_name, snapshot)


def grant_snapshot_access(cmd, resource_group_name, snapshot_name, duration_in_seconds):
    return _grant_access(cmd, resource_group_name, snapshot_name, duration_in_seconds, False)


def list_snapshots(cmd, resource_group_name=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.snapshots.list_by_resource_group(resource_group_name)
    return client.snapshots.list()


def update_snapshot(cmd, instance, sku=None):
    if sku is not None:
        _set_sku(cmd, instance, sku)
    return instance
# endregion


# region VirtualMachines Identity
def show_vm_identity(cmd, resource_group_name, vm_name):
    client = _compute_client_factory(cmd.cli_ctx)
    return client.virtual_machines.get(resource_group_name, vm_name).identity


def show_vmss_identity(cmd, resource_group_name, vm_name):
    client = _compute_client_factory(cmd.cli_ctx)
    return client.virtual_machine_scale_sets.get(resource_group_name, vm_name).identity


def assign_vm_identity(cmd, resource_group_name, vm_name, assign_identity=None, identity_role='Contributor',
                       identity_role_id=None, identity_scope=None):
    VirtualMachineIdentity, ResourceIdentityType, VirtualMachineUpdate = cmd.get_models('VirtualMachineIdentity',
                                                                                        'ResourceIdentityType',
                                                                                        'VirtualMachineUpdate')
    VirtualMachineIdentityUserAssignedIdentitiesValue = cmd.get_models(
        'VirtualMachineIdentityUserAssignedIdentitiesValue')
    from azure.cli.core.commands.arm import assign_identity as assign_identity_helper
    client = _compute_client_factory(cmd.cli_ctx)
    _, _, external_identities, enable_local_identity = _build_identities_info(assign_identity)

    def getter():
        return client.virtual_machines.get(resource_group_name, vm_name)

    def setter(vm, external_identities=external_identities):
        if vm.identity and vm.identity.type == ResourceIdentityType.system_assigned_user_assigned:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif vm.identity and vm.identity.type == ResourceIdentityType.system_assigned and external_identities:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif vm.identity and vm.identity.type == ResourceIdentityType.user_assigned and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities:
            identity_types = ResourceIdentityType.user_assigned
        else:
            identity_types = ResourceIdentityType.system_assigned

        vm.identity = VirtualMachineIdentity(type=identity_types)
        if external_identities:
            vm.identity.user_assigned_identities = {}
            for identity in external_identities:
                vm.identity.user_assigned_identities[identity] = VirtualMachineIdentityUserAssignedIdentitiesValue()

        vm_patch = VirtualMachineUpdate()
        vm_patch.identity = vm.identity
        return patch_vm(cmd, resource_group_name, vm_name, vm_patch)

    assign_identity_helper(cmd.cli_ctx, getter, setter, identity_role=identity_role_id, identity_scope=identity_scope)
    vm = client.virtual_machines.get(resource_group_name, vm_name)
    return _construct_identity_info(identity_scope, identity_role, vm.identity.principal_id,
                                    vm.identity.user_assigned_identities)


def list_user_assigned_identities(cmd, resource_group_name=None):
    from azure.cli.command_modules.vm._client_factory import msi_client_factory
    client = msi_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.user_assigned_identities.list_by_resource_group(resource_group_name)
    return client.user_assigned_identities.list_by_subscription()
# endregion


def capture_vm(cmd, resource_group_name, vm_name, vhd_name_prefix,
               storage_container='vhds', overwrite=True):
    VirtualMachineCaptureParameters = cmd.get_models('VirtualMachineCaptureParameters')
    client = _compute_client_factory(cmd.cli_ctx)
    parameter = VirtualMachineCaptureParameters(vhd_prefix=vhd_name_prefix,
                                                destination_container_name=storage_container,
                                                overwrite_vhds=overwrite)
    poller = client.virtual_machines.capture(resource_group_name, vm_name, parameter)
    result = LongRunningOperation(cmd.cli_ctx)(poller)
    output = getattr(result, 'output', None) or result.resources[0]
    print(json.dumps(output, indent=2))  # pylint: disable=no-member


# pylint: disable=too-many-locals, unused-argument, too-many-statements, too-many-branches
def create_vm(cmd, vm_name, resource_group_name, image=None, size='Standard_DS1_v2', location=None, tags=None,
              no_wait=False, authentication_type=None, admin_password=None,
              admin_username=getpass.getuser(), ssh_dest_key_path=None, ssh_key_value=None, generate_ssh_keys=False,
              availability_set=None, nics=None, nsg=None, nsg_rule=None, accelerated_networking=None,
              private_ip_address=None, public_ip_address=None, public_ip_address_allocation='dynamic',
              public_ip_address_dns_name=None, public_ip_sku=None, os_disk_name=None, os_type=None,
              storage_account=None, os_caching=None, data_caching=None, storage_container_name=None, storage_sku=None,
              use_unmanaged_disk=False, attach_os_disk=None, os_disk_size_gb=None, attach_data_disks=None,
              data_disk_sizes_gb=None, disk_info=None,
              vnet_name=None, vnet_address_prefix='10.0.0.0/16', subnet=None, subnet_address_prefix='10.0.0.0/24',
              storage_profile=None, os_publisher=None, os_offer=None, os_sku=None, os_version=None,
              storage_account_type=None, vnet_type=None, nsg_type=None, public_ip_address_type=None, nic_type=None,
              validate=False, custom_data=None, secrets=None, plan_name=None, plan_product=None, plan_publisher=None,
              plan_promotion_code=None, license_type=None, assign_identity=None, identity_scope=None,
              identity_role='Contributor', identity_role_id=None, application_security_groups=None, zone=None,
              boot_diagnostics_storage=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.core.util import random_string, hash_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.vm._template_builder import (build_vm_resource,
                                                                build_storage_account_resource, build_nic_resource,
                                                                build_vnet_resource, build_nsg_resource,
                                                                build_public_ip_resource, StorageProfile,
                                                                build_msi_role_assignment)
    from msrestazure.tools import resource_id, is_valid_resource_id

    subscription_id = get_subscription_id(cmd.cli_ctx)
    network_id_template = resource_id(
        subscription=subscription_id, resource_group=resource_group_name,
        namespace='Microsoft.Network')

    vm_id = resource_id(
        subscription=subscription_id, resource_group=resource_group_name,
        namespace='Microsoft.Compute', type='virtualMachines', name=vm_name)

    # determine final defaults and calculated values
    tags = tags or {}
    os_disk_name = os_disk_name or ('osdisk_{}'.format(hash_string(vm_id, length=10)) if use_unmanaged_disk else None)
    storage_container_name = storage_container_name or 'vhds'

    # Build up the ARM template
    master_template = ArmTemplateBuilder()

    vm_dependencies = []
    if storage_account_type == 'new':
        storage_account = storage_account or 'vhdstorage{}'.format(
            hash_string(vm_id, length=14, force_lower=True))
        vm_dependencies.append('Microsoft.Storage/storageAccounts/{}'.format(storage_account))
        master_template.add_resource(build_storage_account_resource(cmd, storage_account, location,
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
                cmd, vnet_name, location, tags, vnet_address_prefix, subnet, subnet_address_prefix))

        if nsg_type == 'new':
            nsg_rule_type = 'rdp' if os_type.lower() == 'windows' else 'ssh'
            nsg = nsg or '{}NSG'.format(vm_name)
            nic_dependencies.append('Microsoft.Network/networkSecurityGroups/{}'.format(nsg))
            master_template.add_resource(build_nsg_resource(cmd, nsg, location, tags, nsg_rule_type))

        if public_ip_address_type == 'new':
            public_ip_address = public_ip_address or '{}PublicIP'.format(vm_name)
            nic_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(
                public_ip_address))
            master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location, tags,
                                                                  public_ip_address_allocation,
                                                                  public_ip_address_dns_name,
                                                                  public_ip_sku, zone))

        subnet_id = subnet if is_valid_resource_id(subnet) else \
            '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template, vnet_name, subnet)

        nsg_id = None
        if nsg:
            nsg_id = nsg if is_valid_resource_id(nsg) else \
                '{}/networkSecurityGroups/{}'.format(network_id_template, nsg)

        public_ip_address_id = None
        if public_ip_address:
            public_ip_address_id = public_ip_address if is_valid_resource_id(public_ip_address) \
                else '{}/publicIPAddresses/{}'.format(network_id_template, public_ip_address)

        nics = [
            {'id': '{}/networkInterfaces/{}'.format(network_id_template, nic_name)}
        ]
        nic_resource = build_nic_resource(
            cmd, nic_name, location, tags, vm_name, subnet_id, private_ip_address, nsg_id,
            public_ip_address_id, application_security_groups, accelerated_networking=accelerated_networking)
        nic_resource['dependsOn'] = nic_dependencies
        master_template.add_resource(nic_resource)
    else:
        # Using an existing NIC
        invalid_parameters = [nsg, public_ip_address, subnet, vnet_name, application_security_groups]
        if any(invalid_parameters):
            raise CLIError('When specifying an existing NIC, do not specify NSG, '
                           'public IP, ASGs, VNet or subnet.')

    os_vhd_uri = None
    if storage_profile in [StorageProfile.SACustomImage, StorageProfile.SAPirImage]:
        storage_account_name = storage_account.rsplit('/', 1)
        storage_account_name = storage_account_name[1] if \
            len(storage_account_name) > 1 else storage_account_name[0]
        os_vhd_uri = 'https://{}.blob.{}/{}/{}.vhd'.format(
            storage_account_name, cmd.cli_ctx.cloud.suffixes.storage_endpoint, storage_container_name, os_disk_name)
    elif storage_profile == StorageProfile.SASpecializedOSDisk:
        os_vhd_uri = attach_os_disk
        os_disk_name = attach_os_disk.rsplit('/', 1)[1][:-4]

    if custom_data:
        custom_data = read_content_if_is_file(custom_data)

    if secrets:
        secrets = _merge_secrets([validate_file_or_dict(secret) for secret in secrets])

    vm_resource = build_vm_resource(
        cmd=cmd, name=vm_name, location=location, tags=tags, size=size, storage_profile=storage_profile, nics=nics,
        admin_username=admin_username, availability_set_id=availability_set, admin_password=admin_password,
        ssh_key_value=ssh_key_value, ssh_key_path=ssh_dest_key_path, image_reference=image,
        os_disk_name=os_disk_name, custom_image_os_type=os_type, storage_sku=storage_sku,
        os_publisher=os_publisher, os_offer=os_offer, os_sku=os_sku, os_version=os_version, os_vhd_uri=os_vhd_uri,
        attach_os_disk=attach_os_disk, os_disk_size_gb=os_disk_size_gb, custom_data=custom_data, secrets=secrets,
        license_type=license_type, zone=zone, disk_info=disk_info,
        boot_diagnostics_storage_uri=boot_diagnostics_storage)
    vm_resource['dependsOn'] = vm_dependencies

    if plan_name:
        vm_resource['plan'] = {
            'name': plan_name,
            'publisher': plan_publisher,
            'product': plan_product,
            'promotionCode': plan_promotion_code
        }

    enable_local_identity = None
    if assign_identity is not None:
        vm_resource['identity'], _, _, enable_local_identity = _build_identities_info(assign_identity)
        role_assignment_guid = None
        if identity_scope:
            role_assignment_guid = str(_gen_guid())
            master_template.add_resource(build_msi_role_assignment(vm_name, vm_id, identity_role_id,
                                                                   role_assignment_guid, identity_scope))

    master_template.add_resource(vm_resource)

    if admin_password:
        master_template.add_secure_parameter('adminPassword', admin_password)

    template = master_template.build()
    parameters = master_template.build_parameters()

    # deploy ARM template
    deployment_name = 'vm_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    if validate:
        from azure.cli.command_modules.vm._vm_utils import log_pprint_template
        log_pprint_template(template)
        log_pprint_template(parameters)
        return client.validate(resource_group_name, deployment_name, properties)

    # creates the VM deployment
    if no_wait:
        return sdk_no_wait(no_wait, client.create_or_update,
                           resource_group_name, deployment_name, properties)
    else:
        LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(no_wait, client.create_or_update,
                                                      resource_group_name, deployment_name, properties))
    vm = get_vm_details(cmd, resource_group_name, vm_name)
    if assign_identity is not None:
        if enable_local_identity and not identity_scope:
            _show_missing_access_warning(resource_group_name, vm_name, 'vm')
        setattr(vm, 'identity', _construct_identity_info(identity_scope, identity_role, vm.identity.principal_id,
                                                         vm.identity.user_assigned_identities))
    return vm


def get_instance_view(cmd, resource_group_name, vm_name):
    return get_vm(cmd, resource_group_name, vm_name, 'instanceView')


def get_vm(cmd, resource_group_name, vm_name, expand=None):
    client = _compute_client_factory(cmd.cli_ctx)
    return client.virtual_machines.get(resource_group_name, vm_name, expand=expand)


def get_vm_details(cmd, resource_group_name, vm_name):
    from msrestazure.tools import parse_resource_id
    from azure.cli.command_modules.vm._vm_utils import get_target_network_api
    result = get_instance_view(cmd, resource_group_name, vm_name)
    network_client = get_mgmt_service_client(
        cmd.cli_ctx, ResourceType.MGMT_NETWORK, api_version=get_target_network_api(cmd.cli_ctx))
    public_ips = []
    fqdns = []
    private_ips = []
    mac_addresses = []
    # pylint: disable=line-too-long,no-member
    for nic_ref in result.network_profile.network_interfaces:
        nic_parts = parse_resource_id(nic_ref.id)
        nic = network_client.network_interfaces.get(nic_parts['resource_group'], nic_parts['name'])
        if nic.mac_address:
            mac_addresses.append(nic.mac_address)
        for ip_configuration in nic.ip_configurations:
            if ip_configuration.private_ip_address:
                private_ips.append(ip_configuration.private_ip_address)
            if ip_configuration.public_ip_address:
                res = parse_resource_id(ip_configuration.public_ip_address.id)
                public_ip_info = network_client.public_ip_addresses.get(res['resource_group'],
                                                                        res['name'])
                if public_ip_info.ip_address:
                    public_ips.append(public_ip_info.ip_address)
                if public_ip_info.dns_settings:
                    fqdns.append(public_ip_info.dns_settings.fqdn)

    setattr(result, 'power_state',
            ','.join([s.display_status for s in result.instance_view.statuses if s.code.startswith('PowerState/')]))
    setattr(result, 'public_ips', ','.join(public_ips))
    setattr(result, 'fqdns', ','.join(fqdns))
    setattr(result, 'private_ips', ','.join(private_ips))
    setattr(result, 'mac_addresses', ','.join(mac_addresses))
    del result.instance_view  # we don't need other instance_view info as people won't care
    return result


def list_skus(cmd, location=None):
    from ._vm_utils import list_sku_info
    return list_sku_info(cmd.cli_ctx, location)


def list_vm(cmd, resource_group_name=None, show_details=False):
    ccf = _compute_client_factory(cmd.cli_ctx)
    vm_list = ccf.virtual_machines.list(resource_group_name=resource_group_name) \
        if resource_group_name else ccf.virtual_machines.list_all()
    if show_details:
        return [get_vm_details(cmd, _parse_rg_name(v.id)[0], v.name) for v in vm_list]

    return list(vm_list)


def list_vm_ip_addresses(cmd, resource_group_name=None, vm_name=None):
    # We start by getting NICs as they are the smack in the middle of all data that we
    # want to collect for a VM (as long as we don't need any info on the VM than what
    # is available in the Id, we don't need to make any calls to the compute RP)
    #
    # Since there is no guarantee that a NIC is in the same resource group as a given
    # Virtual Machine, we can't constrain the lookup to only a single group...
    network_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK)
    nics = network_client.network_interfaces.list_all()
    public_ip_addresses = network_client.public_ip_addresses.list_all()

    ip_address_lookup = {pip.id: pip for pip in list(public_ip_addresses)}

    result = []
    for nic in [n for n in list(nics) if n.virtual_machine]:
        nic_resource_group, nic_vm_name = _parse_rg_name(nic.virtual_machine.id)

        # If provided, make sure that resource group name and vm name match the NIC we are
        # looking at before adding it to the result...
        same_resource_group_name = (resource_group_name is None or
                                    resource_group_name.lower() == nic_resource_group.lower())
        same_vm_name = (vm_name is None or
                        vm_name.lower() == nic_vm_name.lower())
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


def open_vm_port(cmd, resource_group_name, vm_name, port, priority=900, network_security_group_name=None,
                 apply_to_subnet=False):
    from msrestazure.tools import parse_resource_id

    network = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK)

    vm = get_vm(cmd, resource_group_name, vm_name)
    location = vm.location
    nic_ids = list(vm.network_profile.network_interfaces)
    if len(nic_ids) > 1:
        raise CLIError('Multiple NICs is not supported for this command. Create rules on the NSG '
                       'directly.')
    elif not nic_ids:
        raise CLIError("No NIC associated with VM '{}'".format(vm_name))

    # get existing NSG or create a new one
    created_nsg = False
    nic = network.network_interfaces.get(resource_group_name, os.path.split(nic_ids[0].id)[1])
    if not apply_to_subnet:
        nsg = nic.network_security_group
    else:
        subnet_id = parse_resource_id(nic.ip_configurations[0].subnet.id)
        subnet = network.subnets.get(resource_group_name, subnet_id['name'], subnet_id['child_name_1'])
        nsg = subnet.network_security_group

    if not nsg:
        NetworkSecurityGroup = \
            cmd.get_models('NetworkSecurityGroup', resource_type=ResourceType.MGMT_NETWORK)
        nsg = LongRunningOperation(cmd.cli_ctx, 'Creating network security group')(
            network.network_security_groups.create_or_update(
                resource_group_name=resource_group_name,
                network_security_group_name=network_security_group_name,
                parameters=NetworkSecurityGroup(location=location)
            )
        )
        created_nsg = True

    # update the NSG with the new rule to allow inbound traffic
    SecurityRule = cmd.get_models('SecurityRule', resource_type=ResourceType.MGMT_NETWORK)
    rule_name = 'open-port-all' if port == '*' else 'open-port-{}'.format(port)
    rule = SecurityRule(protocol='*', access='allow', direction='inbound', name=rule_name,
                        source_port_range='*', destination_port_range=port, priority=priority,
                        source_address_prefix='*', destination_address_prefix='*')
    nsg_name = nsg.name or os.path.split(nsg.id)[1]
    LongRunningOperation(cmd.cli_ctx, 'Adding security rule')(
        network.security_rules.create_or_update(
            resource_group_name, nsg_name, rule_name, rule)
    )

    # update the NIC or subnet if a new NSG was created
    if created_nsg and not apply_to_subnet:
        nic.network_security_group = nsg
        LongRunningOperation(cmd.cli_ctx, 'Updating NIC')(network.network_interfaces.create_or_update(
            resource_group_name, nic.name, nic))
    elif created_nsg and apply_to_subnet:
        subnet.network_security_group = nsg
        LongRunningOperation(cmd.cli_ctx, 'Updating subnet')(network.subnets.create_or_update(
            resource_group_name=resource_group_name,
            virtual_network_name=subnet_id['name'],
            subnet_name=subnet_id['child_name_1'],
            subnet_parameters=subnet
        ))

    return network.network_security_groups.get(resource_group_name, nsg_name)


def resize_vm(cmd, resource_group_name, vm_name, size, no_wait=False):
    vm = get_vm(cmd, resource_group_name, vm_name)
    if vm.hardware_profile.vm_size == size:
        logger.warning("VM is already %s", size)
        return None

    vm.hardware_profile.vm_size = size  # pylint: disable=no-member
    return set_vm(cmd, vm, no_wait)


def set_vm(cmd, instance, lro_operation=None, no_wait=False):
    instance.resources = None  # Issue: https://github.com/Azure/autorest/issues/934
    client = _compute_client_factory(cmd.cli_ctx)
    parsed_id = _parse_rg_name(instance.id)
    poller = sdk_no_wait(no_wait, client.virtual_machines.create_or_update,
                         resource_group_name=parsed_id[0],
                         vm_name=parsed_id[1],
                         parameters=instance)
    if lro_operation:
        return lro_operation(poller)

    return LongRunningOperation(cmd.cli_ctx)(poller)


def patch_vm(cmd, resource_group_name, vm_name, vm):
    client = _compute_client_factory(cmd.cli_ctx)
    poller = client.virtual_machines.update(resource_group_name, vm_name, vm)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def show_vm(cmd, resource_group_name, vm_name, show_details=False):
    return get_vm_details(cmd, resource_group_name, vm_name) if show_details \
        else get_vm(cmd, resource_group_name, vm_name)


def update_vm(cmd, resource_group_name, vm_name, os_disk=None, disk_caching=None,
              write_accelerator=None, license_type=None, no_wait=False, **kwargs):
    from msrestazure.tools import parse_resource_id, resource_id, is_valid_resource_id
    from ._vm_utils import update_write_accelerator_settings, update_disk_caching
    vm = kwargs['parameters']
    if os_disk is not None:
        if is_valid_resource_id(os_disk):
            disk_id, disk_name = os_disk, parse_resource_id(os_disk)['name']
        else:
            res = parse_resource_id(vm.id)
            disk_id = resource_id(subscription=res['subscription'], resource_group=res['resource_group'],
                                  namespace='Microsoft.Compute', type='disks', name=os_disk)
            disk_name = os_disk
        vm.storage_profile.os_disk.managed_disk.id = disk_id
        vm.storage_profile.os_disk.name = disk_name

    if write_accelerator is not None:
        update_write_accelerator_settings(vm.storage_profile, write_accelerator)

    if disk_caching is not None:
        update_disk_caching(vm.storage_profile, disk_caching)

    if license_type is not None:
        vm.license_type = license_type

    return sdk_no_wait(no_wait, _compute_client_factory(cmd.cli_ctx).virtual_machines.create_or_update,
                       resource_group_name, vm_name, **kwargs)

# endregion


# region VirtualMachines AvailabilitySets
def _get_availset(cmd, resource_group_name, name):
    return _compute_client_factory(cmd.cli_ctx).availability_sets.get(resource_group_name, name)


def _set_availset(cmd, resource_group_name, name, **kwargs):
    return _compute_client_factory(cmd.cli_ctx).availability_sets.create_or_update(resource_group_name, name, **kwargs)


# pylint: disable=inconsistent-return-statements
def convert_av_set_to_managed_disk(cmd, resource_group_name, availability_set_name):
    av_set = _get_availset(cmd, resource_group_name, availability_set_name)
    if av_set.sku.name != 'Aligned':
        av_set.sku.name = 'Aligned'

        # let us double check whether the existing FD number is supported
        skus = list_skus(cmd, av_set.location)
        av_sku = next((s for s in skus if s.resource_type == 'availabilitySets' and s.name == 'Aligned'), None)
        if av_sku and av_sku.capabilities:
            max_fd = int(next((c.value for c in av_sku.capabilities if c.name == 'MaximumPlatformFaultDomainCount'),
                              '0'))
            if max_fd and max_fd < av_set.platform_fault_domain_count:
                logger.warning("The fault domain count will be adjusted from %s to %s so to stay within region's "
                               "limitation", av_set.platform_fault_domain_count, max_fd)
                av_set.platform_fault_domain_count = max_fd

        return _set_availset(cmd, resource_group_name=resource_group_name, name=availability_set_name,
                             parameters=av_set)
    else:
        logger.warning('Availability set %s is already configured for managed disks.', availability_set_name)


def create_av_set(cmd, availability_set_name, resource_group_name,
                  platform_fault_domain_count=2, platform_update_domain_count=None,
                  location=None, no_wait=False,
                  unmanaged=False, tags=None, validate=False):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.vm._template_builder import build_av_set_resource

    tags = tags or {}

    # Build up the ARM template
    master_template = ArmTemplateBuilder()

    av_set_resource = build_av_set_resource(cmd, availability_set_name, location, tags,
                                            platform_update_domain_count,
                                            platform_fault_domain_count, unmanaged)
    master_template.add_resource(av_set_resource)

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'av_set_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    if validate:
        return client.validate(resource_group_name, deployment_name, properties)

    if no_wait:
        return sdk_no_wait(no_wait, client.create_or_update,
                           resource_group_name, deployment_name, properties)

    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(no_wait, client.create_or_update,
                                                  resource_group_name, deployment_name, properties))
    compute_client = _compute_client_factory(cmd.cli_ctx)
    return compute_client.availability_sets.get(resource_group_name, availability_set_name)


def list_av_sets(cmd, resource_group_name=None):
    op_group = _compute_client_factory(cmd.cli_ctx).availability_sets
    if resource_group_name:
        return op_group.list(resource_group_name)
    return op_group.list_by_subscription()
# endregion


# region VirtualMachines BootDiagnostics
def disable_boot_diagnostics(cmd, resource_group_name, vm_name):
    vm = get_vm(cmd, resource_group_name, vm_name)
    diag_profile = vm.diagnostics_profile
    if not (diag_profile and diag_profile.boot_diagnostics and diag_profile.boot_diagnostics.enabled):
        return

    diag_profile.boot_diagnostics.enabled = False
    diag_profile.boot_diagnostics.storage_uri = None
    set_vm(cmd, vm, ExtensionUpdateLongRunningOperation(cmd.cli_ctx, 'disabling boot diagnostics', 'done'))


def enable_boot_diagnostics(cmd, resource_group_name, vm_name, storage):
    from azure.cli.command_modules.vm._vm_utils import get_storage_blob_uri
    vm = get_vm(cmd, resource_group_name, vm_name)
    storage_uri = get_storage_blob_uri(cmd.cli_ctx, storage)

    if (vm.diagnostics_profile and
            vm.diagnostics_profile.boot_diagnostics and
            vm.diagnostics_profile.boot_diagnostics.enabled and
            vm.diagnostics_profile.boot_diagnostics.storage_uri and
            vm.diagnostics_profile.boot_diagnostics.storage_uri.lower() == storage_uri.lower()):
        return

    DiagnosticsProfile, BootDiagnostics = cmd.get_models('DiagnosticsProfile', 'BootDiagnostics')

    boot_diag = BootDiagnostics(enabled=True, storage_uri=storage_uri)
    if vm.diagnostics_profile is None:
        vm.diagnostics_profile = DiagnosticsProfile(boot_diagnostics=boot_diag)
    else:
        vm.diagnostics_profile.boot_diagnostics = boot_diag

    set_vm(cmd, vm, ExtensionUpdateLongRunningOperation(cmd.cli_ctx, 'enabling boot diagnostics', 'done'))


class BootLogStreamWriter(object):  # pylint: disable=too-few-public-methods

    def __init__(self, out):
        self.out = out

    def write(self, str_or_bytes):
        content = str_or_bytes
        if isinstance(str_or_bytes, bytes):
            content = str_or_bytes.decode('utf8')
        try:
            self.out.write(content)
        except UnicodeEncodeError:
            # e.g. 'charmap' codec can't encode characters in position 258829-258830: character maps to <undefined>
            import unicodedata
            ascii_content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore')
            self.out.write(ascii_content.decode())
            logger.warning("A few unicode characters have been ignored because the shell is not able to display. "
                           "To see the full log, use a shell with unicode capacity")


def get_boot_log(cmd, resource_group_name, vm_name):
    import re
    import sys
    from azure.cli.core.profiles import get_sdk
    BlockBlobService = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE, 'blob.blockblobservice#BlockBlobService')

    client = _compute_client_factory(cmd.cli_ctx)

    virtual_machine = client.virtual_machines.get(resource_group_name, vm_name, expand='instanceView')
    # pylint: disable=no-member
    if (not virtual_machine.instance_view.boot_diagnostics or
            not virtual_machine.instance_view.boot_diagnostics.serial_console_log_blob_uri):
        raise CLIError('Please enable boot diagnostics.')

    blob_uri = virtual_machine.instance_view.boot_diagnostics.serial_console_log_blob_uri

    # Find storage account for diagnostics
    storage_mgmt_client = _get_storage_management_client(cmd.cli_ctx)
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
        cmd.cli_ctx,
        BlockBlobService,
        storage_account.name,
        keys.keys[0].value,
        endpoint_suffix=cmd.cli_ctx.cloud.suffixes.storage_endpoint)  # pylint: disable=no-member

    # our streamwriter not seekable, so no parallel.
    storage_client.get_blob_to_stream(container, blob, BootLogStreamWriter(sys.stdout), max_connections=1)
# endregion


# region VirtualMachines Diagnostics
def set_diagnostics_extension(
        cmd, resource_group_name, vm_name, settings, protected_settings=None, version=None,
        no_auto_upgrade=False):
    client = _compute_client_factory(cmd.cli_ctx)
    vm = client.virtual_machines.get(resource_group_name, vm_name, 'instanceView')
    # pylint: disable=no-member
    is_linux_os = _is_linux_os(vm)
    vm_extension_name = _LINUX_DIAG_EXT if is_linux_os else _WINDOWS_DIAG_EXT
    if is_linux_os:  # check incompatible version
        exts = vm.instance_view.extensions or []
        major_ver = extension_mappings[_LINUX_DIAG_EXT]['version'].split('.')[0]
        if next((e for e in exts if e.name == vm_extension_name and
                 not e.type_handler_version.startswith(major_ver + '.')), None):
            logger.warning('There is an incompatible version of diagnostics extension installed. '
                           'We will update it with a new version')
            poller = client.virtual_machine_extensions.delete(resource_group_name, vm_name,
                                                              vm_extension_name)
            LongRunningOperation(cmd.cli_ctx)(poller)

    return set_extension(cmd, resource_group_name, vm_name, vm_extension_name,
                         extension_mappings[vm_extension_name]['publisher'],
                         version or extension_mappings[vm_extension_name]['version'],
                         settings,
                         protected_settings,
                         no_auto_upgrade)


def show_default_diagnostics_configuration(is_windows_os=False):
    public_settings = get_default_diag_config(is_windows_os)
    # pylint: disable=line-too-long
    protected_settings_info = json.dumps({
        'storageAccountName': "__STORAGE_ACCOUNT_NAME__",
        # LAD and WAD are not consistent on sas token format. Call it out here
        "storageAccountSasToken": "__SAS_TOKEN_{}__".format("WITH_LEADING_QUESTION_MARK" if is_windows_os else "WITHOUT_LEADING_QUESTION_MARK")
    }, indent=2)
    logger.warning('Protected settings with storage account info is required to work with the default configurations, e.g. \n%s', protected_settings_info)
    return public_settings
# endregion


# region VirtualMachines Disks (Managed)
def attach_managed_data_disk(cmd, resource_group_name, vm_name, disk, new=False, sku=None,
                             size_gb=None, lun=None, caching=None, enable_write_accelerator=False):
    '''attach a managed disk'''
    from msrestazure.tools import parse_resource_id
    vm = get_vm(cmd, resource_group_name, vm_name)
    DataDisk, ManagedDiskParameters, DiskCreateOption = cmd.get_models(
        'DataDisk', 'ManagedDiskParameters', 'DiskCreateOptionTypes')

    # pylint: disable=no-member
    if lun is None:
        luns = ([d.lun for d in vm.storage_profile.data_disks]
                if vm.storage_profile.data_disks else [])
        lun = max(luns) + 1 if luns else 0
    if new:
        if not size_gb:
            raise CLIError('usage error: --size-gb required to create an empty disk for attach')
        data_disk = DataDisk(lun=lun, create_option=DiskCreateOption.empty,
                             name=parse_resource_id(disk)['name'],
                             disk_size_gb=size_gb, caching=caching,
                             managed_disk=ManagedDiskParameters(storage_account_type=sku))
    else:
        params = ManagedDiskParameters(id=disk, storage_account_type=sku)
        data_disk = DataDisk(lun=lun, create_option=DiskCreateOption.attach, managed_disk=params, caching=caching)

    if enable_write_accelerator:
        data_disk.write_accelerator_enabled = enable_write_accelerator

    vm.storage_profile.data_disks.append(data_disk)
    set_vm(cmd, vm)


def detach_data_disk(cmd, resource_group_name, vm_name, disk_name):
    # here we handle both unmanaged or managed disk
    vm = get_vm(cmd, resource_group_name, vm_name)
    # pylint: disable=no-member
    leftovers = [d for d in vm.storage_profile.data_disks if d.name.lower() != disk_name.lower()]
    if len(vm.storage_profile.data_disks) == len(leftovers):
        raise CLIError("No disk with the name '{}' was found".format(disk_name))
    vm.storage_profile.data_disks = leftovers
    set_vm(cmd, vm)
# endregion


# region VirtualMachines Extensions
def list_extensions(cmd, resource_group_name, vm_name):
    vm = get_vm(cmd, resource_group_name, vm_name)
    extension_type = 'Microsoft.Compute/virtualMachines/extensions'
    result = [r for r in (vm.resources or []) if r.type == extension_type]
    return result


def set_extension(cmd, resource_group_name, vm_name, vm_extension_name, publisher, version=None, settings=None,
                  protected_settings=None, no_auto_upgrade=False, force_update=False, no_wait=False):
    vm = get_vm(cmd, resource_group_name, vm_name, 'instanceView')
    client = _compute_client_factory(cmd.cli_ctx)

    VirtualMachineExtension = cmd.get_models('VirtualMachineExtension')
    instance_name = _get_extension_instance_name(vm.instance_view, publisher, vm_extension_name)
    version = _normalize_extension_version(cmd.cli_ctx, publisher, vm_extension_name, version, vm.location)
    ext = VirtualMachineExtension(location=vm.location,
                                  publisher=publisher,
                                  virtual_machine_extension_type=vm_extension_name,
                                  protected_settings=protected_settings,
                                  type_handler_version=version,
                                  settings=settings,
                                  auto_upgrade_minor_version=(not no_auto_upgrade))
    if force_update:
        ext.force_update_tag = str(_gen_guid())
    return sdk_no_wait(no_wait, client.virtual_machine_extensions.create_or_update,
                       resource_group_name, vm_name, instance_name, ext)
# endregion


# region VirtualMachines Extension Images
def list_vm_extension_images(
        cmd, image_location=None, publisher_name=None, name=None, version=None, latest=False):
    return load_extension_images_thru_services(
        cmd.cli_ctx, publisher_name, name, version, image_location, latest)
# endregion


# region VirtualMachines Identity
def _remove_identities(cmd, resource_group_name, name, identities, getter, setter):
    ResourceIdentityType = cmd.get_models('ResourceIdentityType', operation_group='virtual_machines')
    remove_system_assigned_identity = False
    if '[system]' in identities:
        remove_system_assigned_identity = True
        identities.remove('[system]')
    resource = getter(cmd, resource_group_name, name)
    emsis_to_remove = []
    if identities:
        existing_emsis = set([x.lower() for x in list((resource.identity.user_assigned_identities or {}).keys())])
        emsis_to_remove = set([x.lower() for x in identities])
        non_existing = emsis_to_remove.difference(existing_emsis)
        if non_existing:
            raise CLIError("'{}' are not associated with '{}'".format(','.join(non_existing), name))
        if not list(existing_emsis - emsis_to_remove):  # if all emsis are gone, we need to update the type
            if resource.identity.type == ResourceIdentityType.user_assigned:
                resource.identity.type = ResourceIdentityType.none
            elif resource.identity.type == ResourceIdentityType.system_assigned_user_assigned:
                resource.identity.type = ResourceIdentityType.system_assigned

    resource.identity.user_assigned_identities = None
    if remove_system_assigned_identity:
        resource.identity.type = (ResourceIdentityType.none
                                  if resource.identity.type == ResourceIdentityType.system_assigned
                                  else ResourceIdentityType.user_assigned)

    if emsis_to_remove:
        if resource.identity.type not in [ResourceIdentityType.none, ResourceIdentityType.system_assigned]:
            resource.identity.user_assigned_identities = {}
            for identity in emsis_to_remove:
                resource.identity.user_assigned_identities[identity] = None

    result = LongRunningOperation(cmd.cli_ctx)(setter(resource_group_name, name, resource))
    return result.identity


def remove_vm_identity(cmd, resource_group_name, vm_name, identities=None):
    def setter(resource_group_name, vm_name, vm):
        client = _compute_client_factory(cmd.cli_ctx)
        VirtualMachineUpdate = cmd.get_models('VirtualMachineUpdate', operation_group='virtual_machines')
        vm_update = VirtualMachineUpdate(identity=vm.identity)
        return client.virtual_machines.update(resource_group_name, vm_name, vm_update)

    if identities is None:
        from ._vm_utils import MSI_LOCAL_ID
        identities = [MSI_LOCAL_ID]

    return _remove_identities(cmd, resource_group_name, vm_name, identities, get_vm, setter)
# endregion


# region VirtualMachines Images
def list_vm_images(cmd, image_location=None, publisher_name=None, offer=None, sku=None,
                   all=False):  # pylint: disable=redefined-builtin
    load_thru_services = all

    if load_thru_services:
        if not publisher_name and not offer and not sku:
            logger.warning("You are retrieving all the images from server which could take more than a minute. "
                           "To shorten the wait, provide '--publisher', '--offer' or '--sku'. Partial name search "
                           "is supported.")
        all_images = load_images_thru_services(cmd.cli_ctx, publisher_name, offer, sku, image_location)
    else:
        all_images = load_images_from_aliases_doc(cmd.cli_ctx, publisher_name, offer, sku)
        logger.warning(
            'You are viewing an offline list of images, use --all to retrieve an up-to-date list')

    for i in all_images:
        i['urn'] = ':'.join([i['publisher'], i['offer'], i['sku'], i['version']])
    return all_images


def show_vm_image(cmd, urn=None, publisher=None, offer=None, sku=None, version=None, location=None):
    from azure.cli.core.commands.parameters import get_one_of_subscription_locations
    usage_err = 'usage error: --plan STRING --offer STRING --publish STRING --version STRING | --urn STRING'
    location = location or get_one_of_subscription_locations(cmd.cli_ctx)
    if urn:
        if any([publisher, offer, sku, version]):
            raise CLIError(usage_err)
        publisher, offer, sku, version = urn.split(":")
        if version.lower() == 'latest':
            version = _get_latest_image_version(cmd.cli_ctx, location, publisher, offer, sku)
    elif not publisher or not offer or not sku or not version:
        raise CLIError(usage_err)
    client = _compute_client_factory(cmd.cli_ctx)
    return client.virtual_machine_images.get(location, publisher, offer, sku, version)


def accept_market_ordering_terms(cmd, urn=None, publisher=None, offer=None, plan=None):
    from azure.mgmt.marketplaceordering import MarketplaceOrderingAgreements

    usage_err = 'usage error: --plan STRING --offer STRING --publish STRING |--urn STRING'
    if urn:
        if any([publisher, offer, plan]):
            raise CLIError(usage_err)
        publisher, offer, _, _ = urn.split(':')
        image = show_vm_image(cmd, urn)
        if not image.plan:
            logger.warning("Image '%s' has no terms to accept.", urn)
            return
        plan = image.plan.name
    else:
        if not publisher or not offer or not plan:
            raise CLIError(usage_err)

    market_place_client = get_mgmt_service_client(cmd.cli_ctx, MarketplaceOrderingAgreements)

    term = market_place_client.marketplace_agreements.get(publisher, offer, plan)
    term.accepted = True
    return market_place_client.marketplace_agreements.create(publisher, offer, plan, term)
# endregion


# region VirtualMachines NetworkInterfaces (NICs)
def show_vm_nic(cmd, resource_group_name, vm_name, nic):
    from msrestazure.tools import parse_resource_id
    vm = get_vm(cmd, resource_group_name, vm_name)
    found = next(
        (n for n in vm.network_profile.network_interfaces if nic.lower() == n.id.lower()), None
        # pylint: disable=no-member
    )
    if found:
        network_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK)
        nic_name = parse_resource_id(found.id)['name']
        return network_client.network_interfaces.get(resource_group_name, nic_name)
    else:
        raise CLIError("NIC '{}' not found on VM '{}'".format(nic, vm_name))


def list_vm_nics(cmd, resource_group_name, vm_name):
    vm = get_vm(cmd, resource_group_name, vm_name)
    return vm.network_profile.network_interfaces  # pylint: disable=no-member


def add_vm_nic(cmd, resource_group_name, vm_name, nics, primary_nic=None):
    vm = get_vm(cmd, resource_group_name, vm_name)
    new_nics = _build_nic_list(cmd, nics)
    existing_nics = _get_existing_nics(vm)
    return _update_vm_nics(cmd, vm, existing_nics + new_nics, primary_nic)


def remove_vm_nic(cmd, resource_group_name, vm_name, nics, primary_nic=None):

    def to_delete(nic_id):
        return [n for n in nics_to_delete if n.id.lower() == nic_id.lower()]

    vm = get_vm(cmd, resource_group_name, vm_name)
    nics_to_delete = _build_nic_list(cmd, nics)
    existing_nics = _get_existing_nics(vm)
    survived = [x for x in existing_nics if not to_delete(x.id)]
    return _update_vm_nics(cmd, vm, survived, primary_nic)


def set_vm_nic(cmd, resource_group_name, vm_name, nics, primary_nic=None):
    vm = get_vm(cmd, resource_group_name, vm_name)
    nics = _build_nic_list(cmd, nics)
    return _update_vm_nics(cmd, vm, nics, primary_nic)


def _build_nic_list(cmd, nic_ids):
    NetworkInterfaceReference = cmd.get_models('NetworkInterfaceReference')
    nic_list = []
    if nic_ids:
        # pylint: disable=no-member
        network_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK)
        for nic_id in nic_ids:
            rg, name = _parse_rg_name(nic_id)
            nic = network_client.network_interfaces.get(rg, name)
            nic_list.append(NetworkInterfaceReference(id=nic.id, primary=False))
    return nic_list


def _get_existing_nics(vm):
    network_profile = getattr(vm, 'network_profile', None)
    nics = []
    if network_profile is not None:
        nics = network_profile.network_interfaces or []
    return nics


def _update_vm_nics(cmd, vm, nics, primary_nic):
    NetworkProfile = cmd.get_models('NetworkProfile')

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
        vm.network_profile = NetworkProfile(network_interfaces=nics)
    else:
        network_profile.network_interfaces = nics

    return set_vm(cmd, vm).network_profile.network_interfaces
# endregion


# region VirtualMachines RunCommand
def run_command_invoke(cmd, resource_group_name, vm_name, command_id, scripts=None, parameters=None):
    RunCommandInput, RunCommandInputParameter = cmd.get_models('RunCommandInput', 'RunCommandInputParameter')

    parameters = parameters or []
    run_command_input_parameters = []
    auto_arg_name_num = 0
    for p in parameters:
        if '=' in p:
            n, v = p.split('=', 1)
        else:
            # RunCommand API requires named arguments, which doesn't make lots of sense for bash scripts
            # using positional arguments, so here we provide names just to get API happy
            # note, we don't handle mixing styles, but will consolidate by GA when API is settled
            auto_arg_name_num += 1
            n = 'arg{}'.format(auto_arg_name_num)
            v = p
        run_command_input_parameters.append(RunCommandInputParameter(name=n, value=v))

    client = _compute_client_factory(cmd.cli_ctx)
    return client.virtual_machines.run_command(resource_group_name, vm_name,
                                               RunCommandInput(command_id=command_id, script=scripts,
                                                               parameters=run_command_input_parameters))
# endregion


# region VirtualMachines Secrets
def _get_vault_id_from_name(cli_ctx, client, vault_name):
    group_name = _get_resource_group_from_vault_name(cli_ctx, vault_name)
    if not group_name:
        raise CLIError("unable to find vault '{}' in current subscription.".format(vault_name))
    vault = client.get(group_name, vault_name)
    return vault.id


def get_vm_format_secret(cmd, secrets, certificate_store=None, keyvault=None, resource_group_name=None):
    from azure.mgmt.keyvault import KeyVaultManagementClient
    from azure.keyvault import KeyVaultId
    import re
    client = get_mgmt_service_client(cmd.cli_ctx, KeyVaultManagementClient).vaults
    grouped_secrets = {}

    merged_secrets = []
    for s in secrets:
        merged_secrets += s.splitlines()

    # group secrets by source vault
    for secret in merged_secrets:
        parsed = KeyVaultId.parse_secret_id(secret)
        match = re.search('://(.+?)\\.', parsed.vault)
        vault_name = match.group(1)
        if vault_name not in grouped_secrets:
            grouped_secrets[vault_name] = {
                'vaultCertificates': [],
                'id': keyvault or _get_vault_id_from_name(cmd.cli_ctx, client, vault_name)
            }

        vault_cert = {'certificateUrl': secret}
        if certificate_store:
            vault_cert['certificateStore'] = certificate_store

        grouped_secrets[vault_name]['vaultCertificates'].append(vault_cert)

    # transform the reduced map to vm format
    formatted = [{'sourceVault': {'id': value['id']},
                  'vaultCertificates': value['vaultCertificates']}
                 for _, value in list(grouped_secrets.items())]

    return formatted


def add_vm_secret(cmd, resource_group_name, vm_name, keyvault, certificate, certificate_store=None):
    from msrestazure.tools import parse_resource_id
    from ._vm_utils import create_keyvault_data_plane_client, get_key_vault_base_url
    VaultSecretGroup, SubResource, VaultCertificate = cmd.get_models(
        'VaultSecretGroup', 'SubResource', 'VaultCertificate')
    vm = get_vm(cmd, resource_group_name, vm_name)

    if '://' not in certificate:  # has a cert name rather a full url?
        keyvault_client = create_keyvault_data_plane_client(cmd.cli_ctx)
        cert_info = keyvault_client.get_certificate(
            get_key_vault_base_url(cmd.cli_ctx, parse_resource_id(keyvault)['name']), certificate, '')
        certificate = cert_info.sid

    if not _is_linux_os(vm):
        certificate_store = certificate_store or 'My'
    elif certificate_store:
        raise CLIError('Usage error: --certificate-store is only applicable on Windows VM')
    vault_cert = VaultCertificate(certificate_url=certificate, certificate_store=certificate_store)
    vault_secret_group = next((x for x in vm.os_profile.secrets
                               if x.source_vault and x.source_vault.id.lower() == keyvault.lower()), None)
    if vault_secret_group:
        vault_secret_group.vault_certificates.append(vault_cert)
    else:
        vault_secret_group = VaultSecretGroup(source_vault=SubResource(id=keyvault), vault_certificates=[vault_cert])
        vm.os_profile.secrets.append(vault_secret_group)
    vm = set_vm(cmd, vm)
    return vm.os_profile.secrets


def list_vm_secrets(cmd, resource_group_name, vm_name):
    vm = get_vm(cmd, resource_group_name, vm_name)
    return vm.os_profile.secrets


def remove_vm_secret(cmd, resource_group_name, vm_name, keyvault, certificate=None):
    vm = get_vm(cmd, resource_group_name, vm_name)

    # support 2 kinds of filter:
    # a. if only keyvault is supplied, we delete its whole vault group.
    # b. if both keyvault and certificate are supplied, we only delete the specific cert entry.

    to_keep = vm.os_profile.secrets
    keyvault_matched = []
    if keyvault:
        keyvault = keyvault.lower()
        keyvault_matched = [x for x in to_keep if x.source_vault and x.source_vault.id.lower() == keyvault]

    if keyvault and not certificate:
        to_keep = [x for x in to_keep if x not in keyvault_matched]
    elif certificate:
        temp = keyvault_matched if keyvault else to_keep
        cert_url_pattern = certificate.lower()
        if '://' not in cert_url_pattern:  # just a cert name?
            cert_url_pattern = '/' + cert_url_pattern + '/'
        for x in temp:
            x.vault_certificates = ([v for v in x.vault_certificates
                                     if not(v.certificate_url and cert_url_pattern in v.certificate_url.lower())])
        to_keep = [x for x in to_keep if x.vault_certificates]  # purge all groups w/o any cert entries

    vm.os_profile.secrets = to_keep
    vm = set_vm(cmd, vm)
    return vm.os_profile.secrets
# endregion


# region VirtualMachines UnmanagedDisks
def attach_unmanaged_data_disk(cmd, resource_group_name, vm_name, new=False, vhd_uri=None, lun=None,
                               disk_name=None, size_gb=1023, caching=None):
    DataDisk, DiskCreateOptionTypes, VirtualHardDisk = cmd.get_models(
        'DataDisk', 'DiskCreateOptionTypes', 'VirtualHardDisk')
    if not new and not disk_name:
        raise CLIError('Pleae provide the name of the existing disk to attach')
    create_option = DiskCreateOptionTypes.empty if new else DiskCreateOptionTypes.attach

    vm = get_vm(cmd, resource_group_name, vm_name)
    if disk_name is None:
        import datetime
        disk_name = vm_name + '-' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # pylint: disable=no-member
    if vhd_uri is None:
        if not hasattr(vm.storage_profile.os_disk, 'vhd') or not vm.storage_profile.os_disk.vhd:
            raise CLIError('Adding unmanaged disks to a VM with managed disks is not supported')
        blob_uri = vm.storage_profile.os_disk.vhd.uri
        vhd_uri = blob_uri[0:blob_uri.rindex('/') + 1] + disk_name + '.vhd'

    if lun is None:
        lun = _get_disk_lun(vm.storage_profile.data_disks)
    disk = DataDisk(lun=lun, vhd=VirtualHardDisk(uri=vhd_uri), name=disk_name,
                    create_option=create_option,
                    caching=caching, disk_size_gb=size_gb if new else None)
    if vm.storage_profile.data_disks is None:
        vm.storage_profile.data_disks = []
    vm.storage_profile.data_disks.append(disk)
    return set_vm(cmd, vm)


def list_unmanaged_disks(cmd, resource_group_name, vm_name):
    vm = get_vm(cmd, resource_group_name, vm_name)
    return vm.storage_profile.data_disks  # pylint: disable=no-member
# endregion


# region VirtualMachines Users
def _update_linux_access_extension(cmd, vm_instance, resource_group_name, protected_settings,
                                   no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)

    VirtualMachineExtension = cmd.get_models('VirtualMachineExtension')

    # pylint: disable=no-member
    instance_name = _get_extension_instance_name(vm_instance.instance_view,
                                                 extension_mappings[_LINUX_ACCESS_EXT]['publisher'],
                                                 _LINUX_ACCESS_EXT,
                                                 _ACCESS_EXT_HANDLER_NAME)

    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm_instance.resources, _LINUX_ACCESS_EXT)

    ext = VirtualMachineExtension(location=vm_instance.location,  # pylint: disable=no-member
                                  publisher=publisher,
                                  virtual_machine_extension_type=_LINUX_ACCESS_EXT,
                                  protected_settings=protected_settings,
                                  type_handler_version=version,
                                  settings={},
                                  auto_upgrade_minor_version=auto_upgrade)
    return sdk_no_wait(no_wait, client.virtual_machine_extensions.create_or_update,
                       resource_group_name, vm_instance.name, instance_name, ext)


def _set_linux_user(cmd, vm_instance, resource_group_name, username,
                    password=None, ssh_key_value=None, no_wait=False):
    protected_settings = {}
    protected_settings['username'] = username
    if password:
        protected_settings['password'] = password
    elif not ssh_key_value and not password:  # default to ssh
        ssh_key_value = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')

    if ssh_key_value:
        protected_settings['ssh_key'] = read_content_if_is_file(ssh_key_value)

    if no_wait:
        return _update_linux_access_extension(cmd, vm_instance, resource_group_name,
                                              protected_settings, no_wait)
    poller = _update_linux_access_extension(cmd, vm_instance, resource_group_name,
                                            protected_settings)
    return ExtensionUpdateLongRunningOperation(cmd.cli_ctx, 'setting user', 'done')(poller)


def _reset_windows_admin(cmd, vm_instance, resource_group_name, username, password, no_wait=False):
    '''Update the password. You can only change the password. Adding a new user is not supported. '''
    client = _compute_client_factory(cmd.cli_ctx)
    VirtualMachineExtension = cmd.get_models('VirtualMachineExtension')

    publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
        vm_instance.resources, _WINDOWS_ACCESS_EXT)
    # pylint: disable=no-member
    instance_name = _get_extension_instance_name(vm_instance.instance_view,
                                                 publisher,
                                                 _WINDOWS_ACCESS_EXT,
                                                 _ACCESS_EXT_HANDLER_NAME)

    ext = VirtualMachineExtension(location=vm_instance.location,  # pylint: disable=no-member
                                  publisher=publisher,
                                  virtual_machine_extension_type=_WINDOWS_ACCESS_EXT,
                                  protected_settings={'Password': password},
                                  type_handler_version=version,
                                  settings={'UserName': username},
                                  auto_upgrade_minor_version=auto_upgrade)

    if no_wait:
        return sdk_no_wait(no_wait, client.virtual_machine_extensions.create_or_update,
                           resource_group_name, vm_instance.name, instance_name, ext)
    poller = client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                vm_instance.name,
                                                                instance_name, ext)
    return ExtensionUpdateLongRunningOperation(cmd.cli_ctx, 'resetting admin', 'done')(poller)


def set_user(cmd, resource_group_name, vm_name, username, password=None, ssh_key_value=None,
             no_wait=False):
    vm = get_vm(cmd, resource_group_name, vm_name, 'instanceView')
    if _is_linux_os(vm):
        return _set_linux_user(cmd, vm, resource_group_name, username, password, ssh_key_value, no_wait)
    else:
        if ssh_key_value:
            raise CLIError('SSH key is not appliable on a Windows VM')
        return _reset_windows_admin(cmd, vm, resource_group_name, username, password, no_wait)


def delete_user(cmd, resource_group_name, vm_name, username, no_wait=False):
    vm = get_vm(cmd, resource_group_name, vm_name, 'instanceView')
    if not _is_linux_os(vm):
        raise CLIError('Deleting a user is not supported on Windows VM')
    if no_wait:
        return _update_linux_access_extension(cmd, vm, resource_group_name,
                                              {'remove_user': username}, no_wait)
    poller = _update_linux_access_extension(cmd, vm, resource_group_name,
                                            {'remove_user': username})
    return ExtensionUpdateLongRunningOperation(cmd.cli_ctx, 'deleting user', 'done')(poller)


def reset_linux_ssh(cmd, resource_group_name, vm_name, no_wait=False):
    vm = get_vm(cmd, resource_group_name, vm_name, 'instanceView')
    if not _is_linux_os(vm):
        raise CLIError('Resetting SSH is not supported in Windows VM')
    if no_wait:
        return _update_linux_access_extension(cmd, vm, resource_group_name,
                                              {'reset_ssh': True}, no_wait)
    poller = _update_linux_access_extension(cmd, vm, resource_group_name,
                                            {'reset_ssh': True})
    return ExtensionUpdateLongRunningOperation(cmd.cli_ctx, 'resetting SSH', 'done')(poller)
# endregion


# region VirtualMachineScaleSets
def assign_vmss_identity(cmd, resource_group_name, vmss_name, assign_identity=None, identity_role='Contributor',
                         identity_role_id=None, identity_scope=None):
    VirtualMachineScaleSetIdentity, UpgradeMode, ResourceIdentityType, VirtualMachineScaleSetUpdate = cmd.get_models(
        'VirtualMachineScaleSetIdentity', 'UpgradeMode', 'ResourceIdentityType', 'VirtualMachineScaleSetUpdate')
    IdentityUserAssignedIdentitiesValue = cmd.get_models('VirtualMachineScaleSetIdentityUserAssignedIdentitiesValue')
    from azure.cli.core.commands.arm import assign_identity as assign_identity_helper
    client = _compute_client_factory(cmd.cli_ctx)
    _, _, external_identities, enable_local_identity = _build_identities_info(assign_identity)

    def getter():
        return client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)

    def setter(vmss, external_identities=external_identities):

        if vmss.identity and vmss.identity.type == ResourceIdentityType.system_assigned_user_assigned:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif vmss.identity and vmss.identity.type == ResourceIdentityType.system_assigned and external_identities:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif vmss.identity and vmss.identity.type == ResourceIdentityType.user_assigned and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities:
            identity_types = ResourceIdentityType.user_assigned
        else:
            identity_types = ResourceIdentityType.system_assigned
        vmss.identity = VirtualMachineScaleSetIdentity(type=identity_types)
        if external_identities:
            vmss.identity.user_assigned_identities = {}
            for identity in external_identities:
                vmss.identity.user_assigned_identities[identity] = IdentityUserAssignedIdentitiesValue()
        vmss_patch = VirtualMachineScaleSetUpdate()
        vmss_patch.identity = vmss.identity
        poller = client.virtual_machine_scale_sets.update(resource_group_name, vmss_name, vmss_patch)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    assign_identity_helper(cmd.cli_ctx, getter, setter, identity_role=identity_role_id, identity_scope=identity_scope)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    if vmss.upgrade_policy.mode == UpgradeMode.manual:
        logger.warning("With manual upgrade mode, you will need to run 'az vmss update-instances -g %s -n %s "
                       "--instance-ids *' to propagate the change", resource_group_name, vmss_name)

    return _construct_identity_info(identity_scope, identity_role, vmss.identity.principal_id,
                                    vmss.identity.user_assigned_identities)


# pylint: disable=too-many-locals, too-many-statements
def create_vmss(cmd, vmss_name, resource_group_name, image,
                disable_overprovision=False, instance_count=2,
                location=None, tags=None, upgrade_policy_mode='manual', validate=False,
                admin_username=getpass.getuser(), admin_password=None, authentication_type=None,
                vm_sku=None, no_wait=False,
                ssh_dest_key_path=None, ssh_key_value=None, generate_ssh_keys=False,
                load_balancer=None, load_balancer_sku=None, application_gateway=None,
                app_gateway_subnet_address_prefix=None,
                app_gateway_sku='Standard_Large', app_gateway_capacity=10,
                backend_pool_name=None, nat_pool_name=None, backend_port=None, health_probe=None,
                public_ip_address=None, public_ip_address_allocation=None,
                public_ip_address_dns_name=None, accelerated_networking=None,
                public_ip_per_vm=False, vm_domain_name=None, dns_servers=None, nsg=None,
                os_caching=None, data_caching=None,
                storage_container_name='vhds', storage_sku=None,
                os_type=None, os_disk_name=None,
                use_unmanaged_disk=False, data_disk_sizes_gb=None, disk_info=None,
                vnet_name=None, vnet_address_prefix='10.0.0.0/16',
                subnet=None, subnet_address_prefix=None,
                os_offer=None, os_publisher=None, os_sku=None, os_version=None,
                load_balancer_type=None, app_gateway_type=None, vnet_type=None,
                public_ip_address_type=None, storage_profile=None,
                single_placement_group=None, custom_data=None, secrets=None, platform_fault_domain_count=None,
                plan_name=None, plan_product=None, plan_publisher=None, plan_promotion_code=None, license_type=None,
                assign_identity=None, identity_scope=None, identity_role='Contributor',
                identity_role_id=None, zones=None, priority=None, eviction_policy=None,
                application_security_groups=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.core.util import random_string, hash_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.vm._template_builder import (StorageProfile, build_vmss_resource,
                                                                build_vnet_resource, build_public_ip_resource,
                                                                build_load_balancer_resource,
                                                                build_vmss_storage_account_pool_resource,
                                                                build_application_gateway_resource,
                                                                build_msi_role_assignment, build_nsg_resource)
    from msrestazure.tools import resource_id, is_valid_resource_id
    subscription_id = get_subscription_id(cmd.cli_ctx)
    network_id_template = resource_id(
        subscription=subscription_id, resource_group=resource_group_name,
        namespace='Microsoft.Network')

    vmss_id = resource_id(
        subscription=subscription_id, resource_group=resource_group_name,
        namespace='Microsoft.Compute', type='virtualMachineScaleSets', name=vmss_name)

    scrubbed_name = vmss_name.replace('-', '').lower()[:5]
    naming_prefix = '{}{}'.format(scrubbed_name,
                                  hash_string(vmss_id,
                                              length=(9 - len(scrubbed_name)),
                                              force_lower=True))

    # determine final defaults and calculated values
    tags = tags or {}
    os_disk_name = os_disk_name or ('osdisk_{}'.format(hash_string(vmss_id, length=10)) if use_unmanaged_disk else None)
    load_balancer = load_balancer or '{}LB'.format(vmss_name)
    app_gateway = application_gateway or '{}AG'.format(vmss_name)
    backend_pool_name = backend_pool_name or '{}BEPool'.format(load_balancer or application_gateway)

    # Build up the ARM template
    master_template = ArmTemplateBuilder()

    vmss_dependencies = []

    # VNET will always be a dependency
    if vnet_type == 'new':
        vnet_name = vnet_name or '{}VNET'.format(vmss_name)
        subnet = subnet or '{}Subnet'.format(vmss_name)
        vmss_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(vnet_name))
        vnet = build_vnet_resource(
            cmd, vnet_name, location, tags, vnet_address_prefix, subnet, subnet_address_prefix)
        if app_gateway_type:
            vnet['properties']['subnets'].append({
                'name': 'appGwSubnet',
                'properties': {
                    'addressPrefix': app_gateway_subnet_address_prefix
                }
            })
        master_template.add_resource(vnet)

    subnet_id = subnet if is_valid_resource_id(subnet) else \
        '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template, vnet_name, subnet)
    gateway_subnet_id = ('{}/virtualNetworks/{}/subnets/appGwSubnet'.format(network_id_template, vnet_name)
                         if app_gateway_type == 'new' else None)

    # public IP is used by either load balancer/application gateway
    public_ip_address_id = None
    if public_ip_address:
        public_ip_address_id = (public_ip_address if is_valid_resource_id(public_ip_address)
                                else '{}/publicIPAddresses/{}'.format(network_id_template,
                                                                      public_ip_address))

    def _get_public_ip_address_allocation(value, sku):
        IPAllocationMethod = cmd.get_models('IPAllocationMethod', resource_type=ResourceType.MGMT_NETWORK)
        if not value:
            value = IPAllocationMethod.static.value if (sku and sku.lower() == 'standard') \
                else IPAllocationMethod.dynamic.value
        return value

    # Handle load balancer creation
    if load_balancer_type == 'new':
        vmss_dependencies.append('Microsoft.Network/loadBalancers/{}'.format(load_balancer))

        lb_dependencies = []
        if vnet_type == 'new':
            lb_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(vnet_name))
        if public_ip_address_type == 'new':
            public_ip_address = public_ip_address or '{}PublicIP'.format(load_balancer)
            lb_dependencies.append(
                'Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
            master_template.add_resource(build_public_ip_resource(
                cmd, public_ip_address, location, tags,
                _get_public_ip_address_allocation(public_ip_address_allocation, load_balancer_sku),
                public_ip_address_dns_name, load_balancer_sku, zones))
            public_ip_address_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                                    public_ip_address)

        # calculate default names if not provided
        nat_pool_name = nat_pool_name or '{}NatPool'.format(load_balancer)
        if not backend_port:
            backend_port = 3389 if os_type == 'windows' else 22

        lb_resource = build_load_balancer_resource(
            cmd, load_balancer, location, tags, backend_pool_name, nat_pool_name, backend_port,
            'loadBalancerFrontEnd', public_ip_address_id, subnet_id,
            private_ip_address='', private_ip_allocation='Dynamic', sku=load_balancer_sku)
        lb_resource['dependsOn'] = lb_dependencies
        master_template.add_resource(lb_resource)

        # Per https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-standard-overview#nsg
        if load_balancer_sku and load_balancer_sku.lower() == 'standard' and nsg is None:
            nsg_name = '{}NSG'.format(vmss_name)
            master_template.add_resource(build_nsg_resource(
                None, nsg_name, location, tags, 'rdp' if os_type.lower() == 'windows' else 'ssh'))
            nsg = "[resourceId('Microsoft.Network/networkSecurityGroups', '{}')]".format(nsg_name)
            vmss_dependencies.append('Microsoft.Network/networkSecurityGroups/{}'.format(nsg_name))

    # Or handle application gateway creation
    if app_gateway_type == 'new':
        vmss_dependencies.append('Microsoft.Network/applicationGateways/{}'.format(app_gateway))

        ag_dependencies = []
        if vnet_type == 'new':
            ag_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(vnet_name))
        if public_ip_address_type == 'new':
            public_ip_address = public_ip_address or '{}PublicIP'.format(app_gateway)
            ag_dependencies.append(
                'Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
            master_template.add_resource(build_public_ip_resource(
                cmd, public_ip_address, location, tags,
                _get_public_ip_address_allocation(public_ip_address_allocation, None), public_ip_address_dns_name,
                None, zones))
            public_ip_address_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                                    public_ip_address)

        # calculate default names if not provided
        backend_port = backend_port or 80

        ag_resource = build_application_gateway_resource(
            cmd, app_gateway, location, tags, backend_pool_name, backend_port, 'appGwFrontendIP',
            public_ip_address_id, subnet_id, gateway_subnet_id, private_ip_address='',
            private_ip_allocation='Dynamic', sku=app_gateway_sku, capacity=app_gateway_capacity)
        ag_resource['dependsOn'] = ag_dependencies
        master_template.add_variable(
            'appGwID',
            "[resourceId('Microsoft.Network/applicationGateways', '{}')]".format(app_gateway))
        master_template.add_resource(ag_resource)

    # create storage accounts if needed for unmanaged disk storage
    if storage_profile in [StorageProfile.SACustomImage, StorageProfile.SAPirImage]:
        master_template.add_resource(build_vmss_storage_account_pool_resource(
            cmd, 'storageLoop', location, tags, storage_sku))
        master_template.add_variable('storageAccountNames', [
            '{}{}'.format(naming_prefix, x) for x in range(5)
        ])
        master_template.add_variable('vhdContainers', [
            "[concat('https://', variables('storageAccountNames')[{}], '.blob.{}/{}')]".format(
                x, cmd.cli_ctx.cloud.suffixes.storage_endpoint, storage_container_name) for x in range(5)
        ])
        vmss_dependencies.append('storageLoop')

    backend_address_pool_id = None
    inbound_nat_pool_id = None
    if load_balancer_type or app_gateway_type:
        network_balancer = load_balancer if load_balancer_type else app_gateway
        balancer_type = 'loadBalancers' if load_balancer_type else 'applicationGateways'

        if is_valid_resource_id(network_balancer):
            # backend address pool needed by load balancer or app gateway
            backend_address_pool_id = '{}/backendAddressPools/{}'.format(network_balancer, backend_pool_name)
            if nat_pool_name:
                inbound_nat_pool_id = '{}/inboundNatPools/{}'.format(network_balancer, nat_pool_name)
        else:
            # backend address pool needed by load balancer or app gateway
            backend_address_pool_id = '{}/{}/{}/backendAddressPools/{}'.format(
                network_id_template, balancer_type, network_balancer, backend_pool_name)
            if nat_pool_name:
                inbound_nat_pool_id = '{}/{}/{}/inboundNatPools/{}'.format(
                    network_id_template, balancer_type, network_balancer, nat_pool_name)

        if health_probe and not is_valid_resource_id(health_probe):
            health_probe = '{}/loadBalancers/{}/probes/{}'.format(network_id_template, load_balancer, health_probe)

    ip_config_name = '{}IPConfig'.format(naming_prefix)
    nic_name = '{}Nic'.format(naming_prefix)

    if custom_data:
        custom_data = read_content_if_is_file(custom_data)

    if secrets:
        secrets = _merge_secrets([validate_file_or_dict(secret) for secret in secrets])

    vmss_resource = build_vmss_resource(
        cmd=cmd, name=vmss_name, naming_prefix=naming_prefix, location=location, tags=tags,
        overprovision=not disable_overprovision, upgrade_policy_mode=upgrade_policy_mode, vm_sku=vm_sku,
        instance_count=instance_count, ip_config_name=ip_config_name, nic_name=nic_name, subnet_id=subnet_id,
        public_ip_per_vm=public_ip_per_vm, vm_domain_name=vm_domain_name, dns_servers=dns_servers, nsg=nsg,
        accelerated_networking=accelerated_networking, admin_username=admin_username,
        authentication_type=authentication_type, storage_profile=storage_profile, os_disk_name=os_disk_name,
        disk_info=disk_info, storage_sku=storage_sku, os_type=os_type, image=image, admin_password=admin_password,
        ssh_key_value=ssh_key_value, ssh_key_path=ssh_dest_key_path, os_publisher=os_publisher, os_offer=os_offer,
        os_sku=os_sku, os_version=os_version, backend_address_pool_id=backend_address_pool_id,
        inbound_nat_pool_id=inbound_nat_pool_id, health_probe=health_probe,
        single_placement_group=single_placement_group, platform_fault_domain_count=platform_fault_domain_count,
        custom_data=custom_data, secrets=secrets, license_type=license_type, zones=zones, priority=priority,
        eviction_policy=eviction_policy, application_security_groups=application_security_groups)
    vmss_resource['dependsOn'] = vmss_dependencies

    if plan_name:
        vmss_resource['plan'] = {
            'name': plan_name,
            'publisher': plan_publisher,
            'product': plan_product,
            'promotionCode': plan_promotion_code
        }

    enable_local_identity = None
    if assign_identity is not None:
        vmss_resource['identity'], _, _, enable_local_identity = _build_identities_info(
            assign_identity)
        if identity_scope:
            role_assignment_guid = str(_gen_guid())
            master_template.add_resource(build_msi_role_assignment(vmss_name, vmss_id, identity_role_id,
                                                                   role_assignment_guid, identity_scope, False))

    master_template.add_resource(vmss_resource)
    master_template.add_output('VMSS', vmss_name, 'Microsoft.Compute', 'virtualMachineScaleSets',
                               output_type='object')

    if admin_password:
        master_template.add_secure_parameter('adminPassword', admin_password)

    template = master_template.build()
    parameters = master_template.build_parameters()

    # deploy ARM template
    deployment_name = 'vmss_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    if validate:
        from azure.cli.command_modules.vm._vm_utils import log_pprint_template
        log_pprint_template(template)
        log_pprint_template(parameters)
        return sdk_no_wait(no_wait, client.validate, resource_group_name, deployment_name, properties)

    # creates the VMSS deployment
    deployment_result = DeploymentOutputLongRunningOperation(cmd.cli_ctx)(
        sdk_no_wait(no_wait, client.create_or_update, resource_group_name, deployment_name, properties))
    if assign_identity is not None:
        vmss_info = get_vmss(cmd, resource_group_name, vmss_name)
        if enable_local_identity and not identity_scope:
            _show_missing_access_warning(resource_group_name, vmss_name, 'vmss')
        deployment_result['vmss']['identity'] = _construct_identity_info(identity_scope, identity_role,
                                                                         vmss_info.identity.principal_id,
                                                                         vmss_info.identity.user_assigned_identities)
    return deployment_result


def _build_identities_info(identities):
    from ._vm_utils import MSI_LOCAL_ID
    identities = identities or []
    identity_types = []
    if not identities or MSI_LOCAL_ID in identities:
        identity_types.append('SystemAssigned')
    external_identities = [x for x in identities if x != MSI_LOCAL_ID]
    if external_identities:
        identity_types.append('UserAssigned')
    identity_types = ','.join(identity_types)
    info = {'type': identity_types}
    if external_identities:
        info['userAssignedIdentities'] = {e: {} for e in external_identities}
    return (info, identity_types, external_identities, 'SystemAssigned' in identity_types)


def deallocate_vmss(cmd, resource_group_name, vm_scale_set_name, instance_ids=None, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_ids and len(instance_ids) == 1:
        return sdk_no_wait(no_wait, client.virtual_machine_scale_set_vms.deallocate,
                           resource_group_name, vm_scale_set_name, instance_ids[0])

    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.deallocate,
                       resource_group_name, vm_scale_set_name, instance_ids=instance_ids)


def delete_vmss_instances(cmd, resource_group_name, vm_scale_set_name, instance_ids, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    if len(instance_ids) == 1:
        return sdk_no_wait(no_wait, client.virtual_machine_scale_set_vms.delete,
                           resource_group_name, vm_scale_set_name, instance_ids[0])

    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.delete_instances,
                       resource_group_name, vm_scale_set_name, instance_ids)


def get_vmss(cmd, resource_group_name, name):
    return _compute_client_factory(cmd.cli_ctx).virtual_machine_scale_sets.get(resource_group_name, name)


def get_vmss_instance_view(cmd, resource_group_name, vm_scale_set_name, instance_id=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_id:
        if instance_id == '*':

            return [x.instance_view for x in (client.virtual_machine_scale_set_vms.list(
                resource_group_name, vm_scale_set_name, select='instanceView', expand='instanceView'))]

        return client.virtual_machine_scale_set_vms.get_instance_view(resource_group_name, vm_scale_set_name,
                                                                      instance_id)

    return client.virtual_machine_scale_sets.get_instance_view(resource_group_name, vm_scale_set_name)


def list_vmss(cmd, resource_group_name=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.virtual_machine_scale_sets.list(resource_group_name)
    return client.virtual_machine_scale_sets.list_all()


def list_vmss_instance_connection_info(cmd, resource_group_name, vm_scale_set_name):
    from msrestazure.tools import parse_resource_id
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vm_scale_set_name)
    # find the load balancer
    nic_configs = vmss.virtual_machine_profile.network_profile.network_interface_configurations
    primary_nic_config = next((n for n in nic_configs if n.primary), None)
    if primary_nic_config is None:
        raise CLIError('could not find a primary NIC which is needed to search to load balancer')
    ip_configs = primary_nic_config.ip_configurations
    ip_config = next((ip for ip in ip_configs if ip.load_balancer_inbound_nat_pools), None)
    if not ip_config:
        raise CLIError('No load balancer exists to retrieve public IP address')
    res_id = ip_config.load_balancer_inbound_nat_pools[0].id
    lb_info = parse_resource_id(res_id)
    lb_name = lb_info['name']
    lb_rg = lb_info['resource_group']

    # get public ip
    network_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK)
    lb = network_client.load_balancers.get(lb_rg, lb_name)
    if getattr(lb.frontend_ip_configurations[0], 'public_ip_address', None):
        res_id = lb.frontend_ip_configurations[0].public_ip_address.id
        public_ip_info = parse_resource_id(res_id)
        public_ip_name = public_ip_info['name']
        public_ip_rg = public_ip_info['resource_group']
        public_ip = network_client.public_ip_addresses.get(public_ip_rg, public_ip_name)
        public_ip_address = public_ip.ip_address

        # loop around inboundnatrule
        instance_addresses = {}
        for rule in lb.inbound_nat_rules:
            instance_id = parse_resource_id(rule.backend_ip_configuration.id)['child_name_1']
            instance_addresses['instance ' + instance_id] = '{}:{}'.format(public_ip_address,
                                                                           rule.frontend_port)

        return instance_addresses
    else:
        raise CLIError('The VM scale-set uses an internal load balancer, hence no connection information')


def list_vmss_instance_public_ips(cmd, resource_group_name, vm_scale_set_name):
    result = cf_public_ip_addresses(cmd.cli_ctx).list_virtual_machine_scale_set_public_ip_addresses(
        resource_group_name, vm_scale_set_name)
    # filter away over-provisioned instances which are deleted after 'create/update' returns
    return [r for r in result if r.ip_address]


def reimage_vmss(cmd, resource_group_name, vm_scale_set_name, instance_id=None, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_id:
        return sdk_no_wait(no_wait, client.virtual_machine_scale_set_vms.reimage,
                           resource_group_name, vm_scale_set_name, instance_id)
    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.reimage, resource_group_name, vm_scale_set_name)


def restart_vmss(cmd, resource_group_name, vm_scale_set_name, instance_ids=None, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_ids and len(instance_ids) == 1:
        return sdk_no_wait(no_wait, client.virtual_machine_scale_set_vms.restart,
                           resource_group_name, vm_scale_set_name, instance_ids[0])
    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.restart, resource_group_name, vm_scale_set_name,
                       instance_ids=instance_ids)


# pylint: disable=inconsistent-return-statements
def scale_vmss(cmd, resource_group_name, vm_scale_set_name, new_capacity, no_wait=False):
    VirtualMachineScaleSet = cmd.get_models('VirtualMachineScaleSet')
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vm_scale_set_name)
    # pylint: disable=no-member
    if vmss.sku.capacity == new_capacity:
        return
    else:
        vmss.sku.capacity = new_capacity
    vmss_new = VirtualMachineScaleSet(location=vmss.location, sku=vmss.sku)
    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.create_or_update,
                       resource_group_name, vm_scale_set_name, vmss_new)


def show_vmss(cmd, resource_group_name, vm_scale_set_name, instance_id=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_id:
        return client.virtual_machine_scale_set_vms.get(resource_group_name, vm_scale_set_name, instance_id)
    return client.virtual_machine_scale_sets.get(resource_group_name, vm_scale_set_name)


def start_vmss(cmd, resource_group_name, vm_scale_set_name, instance_ids=None, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_ids and len(instance_ids) == 1:
        return sdk_no_wait(no_wait, client.virtual_machine_scale_set_vms.start,
                           resource_group_name, vm_scale_set_name, instance_ids[0])

    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.start,
                       resource_group_name, vm_scale_set_name, instance_ids=instance_ids)


def stop_vmss(cmd, resource_group_name, vm_scale_set_name, instance_ids=None, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_ids and len(instance_ids) == 1:
        return sdk_no_wait(no_wait, client.virtual_machine_scale_set_vms.power_off,
                           resource_group_name, vm_scale_set_name, instance_ids[0])

    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.power_off, resource_group_name, vm_scale_set_name,
                       instance_ids=instance_ids)


def update_vmss_instances(cmd, resource_group_name, vm_scale_set_name, instance_ids, no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.update_instances,
                       resource_group_name, vm_scale_set_name, instance_ids)


def update_vmss(cmd, resource_group_name, name, license_type=None, no_wait=False, **kwargs):
    vmss = kwargs['parameters']
    if license_type is not None:
        vmss.virtual_machine_profile.license_type = license_type

    return sdk_no_wait(no_wait, _compute_client_factory(cmd.cli_ctx).virtual_machine_scale_sets.create_or_update,
                       resource_group_name, name, **kwargs)
# endregion


# region VirtualMachineScaleSets Diagnostics
def set_vmss_diagnostics_extension(
        cmd, resource_group_name, vmss_name, settings, protected_settings=None, version=None,
        no_auto_upgrade=False):
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    # pylint: disable=no-member
    is_linux_os = _is_linux_os(vmss.virtual_machine_profile)
    vm_extension_name = _LINUX_DIAG_EXT if is_linux_os else _WINDOWS_DIAG_EXT
    if is_linux_os and vmss.virtual_machine_profile.extension_profile:  # check incompatibles
        exts = vmss.virtual_machine_profile.extension_profile.extensions or []
        major_ver = extension_mappings[_LINUX_DIAG_EXT]['version'].split('.')[0]
        # For VMSS, we don't do auto-removal like VM because there is no reliable API to wait for
        # the removal done before we can install the newer one
        if next((e for e in exts if e.name == _LINUX_DIAG_EXT and
                 not e.type_handler_version.startswith(major_ver + '.')), None):
            delete_cmd = 'az vmss extension delete -g {} --vmss-name {} -n {}'.format(
                resource_group_name, vmss_name, vm_extension_name)
            raise CLIError("There is an incompatible version of diagnostics extension installed. "
                           "Please remove it by running '{}', and retry. 'az vmss update-instances'"
                           " might be needed if with manual upgrade policy".format(delete_cmd))

    poller = set_vmss_extension(cmd, resource_group_name, vmss_name, vm_extension_name,
                                extension_mappings[vm_extension_name]['publisher'],
                                version or extension_mappings[vm_extension_name]['version'],
                                settings,
                                protected_settings,
                                no_auto_upgrade)

    result = LongRunningOperation(cmd.cli_ctx)(poller)
    UpgradeMode = cmd.get_models('UpgradeMode')
    if vmss.upgrade_policy.mode == UpgradeMode.manual:
        poller2 = update_vmss_instances(cmd, resource_group_name, vmss_name, ['*'])
        LongRunningOperation(cmd.cli_ctx)(poller2)
    return result
# endregion


# region VirtualMachineScaleSets Disks (Managed)
def attach_managed_data_disk_to_vmss(cmd, resource_group_name, vmss_name, size_gb=None, instance_id=None, lun=None,
                                     caching=None, disk=None):

    def _init_data_disk(storage_profile, lun, existing_disk=None):
        data_disks = storage_profile.data_disks or []
        if lun is None:
            luns = [d.lun for d in data_disks]
            lun = max(luns) + 1 if luns else 0
        if existing_disk is None:
            data_disk = DataDisk(lun=lun, create_option=DiskCreateOptionTypes.empty,
                                 disk_size_gb=size_gb, caching=caching)
        else:
            data_disk = DataDisk(lun=lun, create_option=DiskCreateOptionTypes.attach,
                                 managed_disk=ManagedDiskParameters(id=existing_disk), caching=caching)

        data_disks.append(data_disk)
        storage_profile.data_disks = data_disks

    DiskCreateOptionTypes, ManagedDiskParameters = cmd.get_models(
        'DiskCreateOptionTypes', 'ManagedDiskParameters')
    if disk is None:
        DataDisk = cmd.get_models('VirtualMachineScaleSetDataDisk')
    else:
        DataDisk = cmd.get_models('DataDisk')

    client = _compute_client_factory(cmd.cli_ctx)
    if instance_id is None:
        vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
        # pylint: disable=no-member
        _init_data_disk(vmss.virtual_machine_profile.storage_profile, lun)
        return client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss_name, vmss)

    vmss_vm = client.virtual_machine_scale_set_vms.get(resource_group_name, vmss_name, instance_id)
    _init_data_disk(vmss_vm.storage_profile, lun, disk)
    return client.virtual_machine_scale_set_vms.update(resource_group_name, vmss_name, instance_id, vmss_vm)


def detach_disk_from_vmss(cmd, resource_group_name, vmss_name, lun, instance_id=None):
    client = _compute_client_factory(cmd.cli_ctx)
    if instance_id is None:
        vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
        # pylint: disable=no-member
        data_disks = vmss.virtual_machine_profile.storage_profile.data_disks
    else:
        vmss_vm = client.virtual_machine_scale_set_vms.get(resource_group_name, vmss_name, instance_id)
        data_disks = vmss_vm.storage_profile.data_disks

    leftovers = [d for d in data_disks if d.lun != lun]
    if len(data_disks) == len(leftovers):
        raise CLIError("Could not find the data disk with lun '{}'".format(lun))

    if instance_id is None:
        vmss.virtual_machine_profile.storage_profile.data_disks = leftovers
        return client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss_name, vmss)
    vmss_vm.storage_profile.data_disks = leftovers
    return client.virtual_machine_scale_set_vms.update(resource_group_name, vmss_name, instance_id, vmss_vm)
# endregion


# region VirtualMachineScaleSets Extensions
def delete_vmss_extension(cmd, resource_group_name, vmss_name, extension_name):
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    # pylint: disable=no-member
    if not vmss.virtual_machine_profile.extension_profile:
        raise CLIError('Scale set has no extensions to delete')

    keep_list = [e for e in vmss.virtual_machine_profile.extension_profile.extensions
                 if e.name != extension_name]
    if len(keep_list) == len(vmss.virtual_machine_profile.extension_profile.extensions):
        raise CLIError('Extension {} not found'.format(extension_name))

    vmss.virtual_machine_profile.extension_profile.extensions = keep_list

    return client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss_name, vmss)


# pylint: disable=inconsistent-return-statements
def get_vmss_extension(cmd, resource_group_name, vmss_name, extension_name):
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    # pylint: disable=no-member
    if not vmss.virtual_machine_profile.extension_profile:
        return
    return next((e for e in vmss.virtual_machine_profile.extension_profile.extensions
                 if e.name == extension_name), None)


def list_vmss_extensions(cmd, resource_group_name, vmss_name):
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    # pylint: disable=no-member
    return None if not vmss.virtual_machine_profile.extension_profile \
        else vmss.virtual_machine_profile.extension_profile.extensions


def set_vmss_extension(cmd, resource_group_name, vmss_name, extension_name, publisher, version=None,
                       settings=None, protected_settings=None, no_auto_upgrade=False, force_update=False,
                       no_wait=False):
    client = _compute_client_factory(cmd.cli_ctx)
    vmss = client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    VirtualMachineScaleSetExtension, VirtualMachineScaleSetExtensionProfile = cmd.get_models(
        'VirtualMachineScaleSetExtension', 'VirtualMachineScaleSetExtensionProfile')

    # pylint: disable=no-member
    version = _normalize_extension_version(cmd.cli_ctx, publisher, extension_name, version, vmss.location)
    extension_profile = vmss.virtual_machine_profile.extension_profile
    if extension_profile:
        extensions = extension_profile.extensions
        if extensions:
            extension_profile.extensions = [x for x in extensions if
                                            x.type.lower() != extension_name.lower() or x.publisher.lower() != publisher.lower()]  # pylint: disable=line-too-long

    ext = VirtualMachineScaleSetExtension(name=extension_name,
                                          publisher=publisher,
                                          type=extension_name,
                                          protected_settings=protected_settings,
                                          type_handler_version=version,
                                          settings=settings,
                                          auto_upgrade_minor_version=(not no_auto_upgrade))
    if force_update:
        ext.force_update_tag = str(_gen_guid())

    if not vmss.virtual_machine_profile.extension_profile:
        vmss.virtual_machine_profile.extension_profile = VirtualMachineScaleSetExtensionProfile(extensions=[])
    vmss.virtual_machine_profile.extension_profile.extensions.append(ext)

    return sdk_no_wait(no_wait, client.virtual_machine_scale_sets.create_or_update,
                       resource_group_name, vmss_name, vmss)
# endregion


# region VirtualMachineScaleSets Identity
def remove_vmss_identity(cmd, resource_group_name, vmss_name, identities=None):
    client = _compute_client_factory(cmd.cli_ctx)

    def _get_vmss(_, resource_group_name, vmss_name):
        return client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)

    def _set_vmss(resource_group_name, name, vmss_instance):
        VirtualMachineScaleSetUpdate = cmd.get_models('VirtualMachineScaleSetUpdate',
                                                      operation_group='virtual_machine_scale_sets')
        vmss_update = VirtualMachineScaleSetUpdate(identity=vmss_instance.identity)
        return client.virtual_machine_scale_sets.update(resource_group_name, vmss_name, vmss_update)

    if identities is None:
        from ._vm_utils import MSI_LOCAL_ID
        identities = [MSI_LOCAL_ID]

    return _remove_identities(cmd, resource_group_name, vmss_name, identities,
                              _get_vmss,
                              _set_vmss)
# endregion
