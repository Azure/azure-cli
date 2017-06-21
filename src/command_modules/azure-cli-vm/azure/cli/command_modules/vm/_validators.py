# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re

from msrestazure.azure_exceptions import CloudError

from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.cli.core.commands.arm import resource_id, parse_resource_id, is_valid_resource_id
from azure.cli.core.commands.validators import \
    (get_default_location_from_resource_group, validate_file_or_dict)
from azure.cli.core.util import CLIError, hash_string
from azure.cli.command_modules.vm._vm_utils import check_existence
from azure.cli.command_modules.vm._template_builder import StorageProfile
import azure.cli.core.azlogging as azlogging
from ._client_factory import _compute_client_factory

logger = azlogging.get_az_logger(__name__)


def validate_nsg_name(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    vm_id = resource_id(name=namespace.vm_name, resource_group=namespace.resource_group_name,
                        namespace='Microsoft.Compute', type='virtualMachines',
                        subscription=get_subscription_id())
    namespace.network_security_group_name = namespace.network_security_group_name \
        or '{}_NSG_{}'.format(namespace.vm_name, hash_string(vm_id, length=8))


def _get_resource_group_from_vault_name(vault_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    client = get_mgmt_service_client(KeyVaultManagementClient).vaults
    for vault in client.list():
        id_comps = parse_resource_id(vault.id)
        if id_comps['name'] == vault_name:
            return id_comps['resource_group']
    return None


def _get_resource_id(val, resource_group, resource_type, resource_namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    if is_valid_resource_id(val):
        return val

    return resource_id(name=val, resource_group=resource_group, namespace=resource_namespace, type=resource_type,
                       subscription=get_subscription_id())


def _get_nic_id(val, resource_group):
    return _get_resource_id(val, resource_group,
                            'networkInterfaces', 'Microsoft.Network')


def validate_vm_nic(namespace):
    namespace.nic = _get_nic_id(namespace.nic, namespace.resource_group_name)


def validate_vm_nics(namespace):
    rg = namespace.resource_group_name
    nic_ids = []

    for n in namespace.nics:
        nic_ids.append(_get_nic_id(n, rg))
    namespace.nics = nic_ids

    if hasattr(namespace, 'primary_nic') and namespace.primary_nic:
        namespace.primary_nic = _get_nic_id(namespace.primary_nic, rg)


def _validate_secrets(secrets, os_type):
    """
    Validates a parsed JSON array containing secrets for use in VM Creation
    Secrets JSON structure
    [{
        "sourceVault": { "id": "value" },
        "vaultCertificates": [{
            "certificateUrl": "value",
            "certificateStore": "cert store name (only on windows)"
        }]
    }]
    :param dict secrets: Dict fitting the JSON description above
    :param string os_type: the type of OS (linux or windows)
    :return: errors if any were found
    :rtype: list
    """
    is_windows = os_type == 'windows'
    errors = []

    try:
        loaded_secret = [validate_file_or_dict(secret) for secret in secrets]
    except Exception as err:
        raise CLIError('Error decoding secrets: {0}'.format(err))

    for idx_arg, narg_secret in enumerate(loaded_secret):
        for idx, secret in enumerate(narg_secret):
            if 'sourceVault' not in secret:
                errors.append(
                    'Secret is missing sourceVault key at index {0} in arg {1}'.format(
                        idx, idx_arg))
            if 'sourceVault' in secret and 'id' not in secret['sourceVault']:
                errors.append(
                    'Secret is missing sourceVault.id key at index {0}  in arg {1}'.format(
                        idx, idx_arg))
            if 'vaultCertificates' not in secret or not secret['vaultCertificates']:
                err = 'Secret is missing vaultCertificates array or it is empty at index {0} in ' \
                      'arg {1} '
                errors.append(err.format(idx, idx_arg))
            else:
                for jdx, cert in enumerate(secret['vaultCertificates']):
                    message = 'Secret is missing {0} within vaultCertificates array at secret ' \
                              'index {1} and vaultCertificate index {2} in arg {3}'
                    if 'certificateUrl' not in cert:
                        errors.append(message.format('certificateUrl', idx, jdx, idx_arg))
                    if is_windows and 'certificateStore' not in cert:
                        errors.append(message.format('certificateStore', idx, jdx, idx_arg))

    if errors:
        raise CLIError('\n'.join(errors))


# region VM Create Validators

def _parse_image_argument(namespace):
    """ Systematically determines what type is supplied for the --image parameter. Updates the
        namespace and returns the type for subsequent processing. """
    # 1 - easy check for URI
    if namespace.image.lower().endswith('.vhd'):
        return 'uri'

    # 2 - attempt to match an URN alias (most likely)
    from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc
    images = load_images_from_aliases_doc()
    matched = next((x for x in images if x['urnAlias'].lower() == namespace.image.lower()), None)
    if matched:
        namespace.os_publisher = matched['publisher']
        namespace.os_offer = matched['offer']
        namespace.os_sku = matched['sku']
        namespace.os_version = matched['version']
        return 'urn'

    # 3 - attempt to match an URN pattern
    urn_match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', namespace.image)
    if urn_match:
        namespace.os_publisher = urn_match.group(1)
        namespace.os_offer = urn_match.group(2)
        namespace.os_sku = urn_match.group(3)
        namespace.os_version = urn_match.group(4)
        compute_client = _compute_client_factory()
        if namespace.os_version.lower() == 'latest':
            top_one = compute_client.virtual_machine_images.list(namespace.location,
                                                                 namespace.os_publisher,
                                                                 namespace.os_offer,
                                                                 namespace.os_sku,
                                                                 top=1,
                                                                 orderby='name desc')
            if not top_one:
                raise CLIError("Can't resolve the vesion of '{}'".format(namespace.image))

            image_version = top_one[0].name
        else:
            image_version = namespace.os_version

        image = compute_client.virtual_machine_images.get(namespace.location,
                                                          namespace.os_publisher,
                                                          namespace.os_offer,
                                                          namespace.os_sku,
                                                          image_version)

        # pylint: disable=no-member
        if image.plan:
            namespace.plan_name = image.plan.name
            namespace.plan_product = image.plan.product
            namespace.plan_publisher = image.plan.publisher
        return 'urn'

    # 4 - check if a fully-qualified ID (assumes it is an image ID)
    if is_valid_resource_id(namespace.image):
        return 'image_id'

    # 5 - check if an existing managed disk image resource
    compute_client = _compute_client_factory()
    try:
        compute_client.images.get(namespace.resource_group_name, namespace.image)
        namespace.image = _get_resource_id(namespace.image, namespace.resource_group_name,
                                           'images', 'Microsoft.Compute')
        return 'image_id'
    except CloudError:
        err = 'Invalid image "{}". Use a custom image name, id, or pick one from {}'
        raise CLIError(err.format(namespace.image, [x['urnAlias'] for x in images]))


def _get_storage_profile_description(profile):
    if profile == StorageProfile.SACustomImage:
        return 'create unmanaged OS disk created from generalized VHD'
    elif profile == StorageProfile.SAPirImage:
        return 'create unmanaged OS disk from Azure Marketplace image'
    elif profile == StorageProfile.SASpecializedOSDisk:
        return 'attach to existing unmanaged OS disk'
    elif profile == StorageProfile.ManagedCustomImage:
        return 'create managed OS disk from custom image'
    elif profile == StorageProfile.ManagedPirImage:
        return 'create managed OS disk from Azure Marketplace image'
    elif profile == StorageProfile.ManagedSpecializedOSDisk:
        return 'attach existing managed OS disk'


storage_profile_param_options = {
    'os_disk_name': '--os-disk-name',
    'os_caching': '--os-caching',
    'os_type': '--os-type',
    'attach_os_disk': '--attach-os-disk',
    'image': '--image',
    'storage_account': '--storage-account',
    'storage_container_name': '--storage-container-name',
    'storage_sku': '--storage-sku',
    'use_unmanaged_disk': '--use-unmanaged-disk'
}


network_balancer_param_options = {
    'application_gateway': '--application-gateway',
    'load_balancer': '--load-balancer',
    'app_gateway_subnet_address_prefix': '--app-gateway-subnet-address-prefix',
    'backend_pool_name': '--backend-pool-name'
}


def _validate_storage_required_forbidden_parameters(namespace, required, forbidden):
    missing_required = [x for x in required if not getattr(namespace, x)]
    included_forbidden = [x for x in forbidden if getattr(namespace, x)]
    if missing_required or included_forbidden:
        error = 'invalid usage for storage profile: {}:'.format(
            _get_storage_profile_description(namespace.storage_profile))
        if missing_required:
            missing_string = ', '.join(
                storage_profile_param_options[x] for x in missing_required)
            error = '{}\n\tmissing: {}'.format(error, missing_string)
        if included_forbidden:
            forbidden_string = ', '.join(
                storage_profile_param_options[x] for x in included_forbidden)
            error = '{}\n\tnot applicable: {}'.format(error, forbidden_string)
        raise CLIError(error)


def _validate_network_balancer_required_forbidden_parameters(namespace, required, forbidden, desc):
    missing_required = [x for x in required if not getattr(namespace, x)]
    included_forbidden = [x for x in forbidden if getattr(namespace, x)]
    if missing_required or included_forbidden:
        error = 'invalid usage for network balancer: {}'.format(desc)
        if missing_required:
            missing_string = ', '.join(
                network_balancer_param_options[x] for x in missing_required)
            error = '{}\n\tmissing: {}'.format(error, missing_string)
        if included_forbidden:
            forbidden_string = ', '.join(
                network_balancer_param_options[x] for x in included_forbidden)
            error = '{}\n\tnot applicable: {}'.format(error, forbidden_string)
        raise CLIError(error)


def _validate_managed_disk_sku(sku):

    allowed_skus = ['Premium_LRS', 'Standard_LRS']
    if sku and sku.lower() not in [x.lower() for x in allowed_skus]:
        raise CLIError("invalid storage SKU '{}': allowed values: '{}'".format(sku, allowed_skus))


# pylint: disable=too-many-branches, too-many-statements
def _validate_vm_create_storage_profile(namespace, for_scale_set=False):

    # use minimal parameters to resolve the expected storage profile
    if getattr(namespace, 'attach_os_disk', None) and not namespace.image:
        if namespace.use_unmanaged_disk:
            # STORAGE PROFILE #3
            namespace.storage_profile = StorageProfile.SASpecializedOSDisk
        else:
            # STORAGE PROFILE #6
            namespace.storage_profile = StorageProfile.ManagedSpecializedOSDisk
    elif namespace.image and not getattr(namespace, 'attach_os_disk', None):
        image_type = _parse_image_argument(namespace)
        if image_type == 'uri':
            # STORAGE PROFILE #2
            namespace.storage_profile = StorageProfile.SACustomImage
        elif image_type == 'image_id':
            # STORAGE PROFILE #5
            namespace.storage_profile = StorageProfile.ManagedCustomImage
        elif image_type == 'urn':
            if namespace.use_unmanaged_disk:
                # STORAGE PROFILE #1
                namespace.storage_profile = StorageProfile.SAPirImage
            else:
                # STORAGE PROFILE #4
                namespace.storage_profile = StorageProfile.ManagedPirImage
        else:
            raise CLIError('Unrecognized image type: {}'.format(image_type))
    else:
        # did not specify image XOR attach-os-disk
        raise CLIError('incorrect usage: --image IMAGE | --attach-os-disk DISK')

    # perform parameter validation for the specific storage profile
    # start with the required/forbidden parameters for VM
    if namespace.storage_profile == StorageProfile.ManagedPirImage:
        required = ['image']
        forbidden = ['os_type', 'attach_os_disk', 'storage_account',
                     'storage_container_name', 'use_unmanaged_disk']
        if for_scale_set:
            forbidden.append('os_disk_name')
        _validate_managed_disk_sku(namespace.storage_sku)

    elif namespace.storage_profile == StorageProfile.ManagedCustomImage:
        required = ['image']
        forbidden = ['os_type', 'attach_os_disk', 'storage_account',
                     'storage_container_name', 'use_unmanaged_disk']
        if for_scale_set:
            forbidden.append('os_disk_name')
        _validate_managed_disk_sku(namespace.storage_sku)

    elif namespace.storage_profile == StorageProfile.ManagedSpecializedOSDisk:
        required = ['os_type', 'attach_os_disk']
        forbidden = ['os_disk_name', 'os_caching', 'storage_account',
                     'storage_container_name', 'use_unmanaged_disk', 'storage_sku']
        _validate_managed_disk_sku(namespace.storage_sku)

    elif namespace.storage_profile == StorageProfile.SAPirImage:
        required = ['image', 'use_unmanaged_disk']
        forbidden = ['os_type', 'data_caching', 'attach_os_disk', 'data_disk_sizes_gb']

    elif namespace.storage_profile == StorageProfile.SACustomImage:
        required = ['image', 'os_type', 'use_unmanaged_disk']
        forbidden = ['attach_os_disk', 'data_caching', 'data_disk_sizes_gb']

    elif namespace.storage_profile == StorageProfile.SASpecializedOSDisk:
        required = ['os_type', 'attach_os_disk', 'use_unmanaged_disk']
        forbidden = ['os_disk_name', 'os_caching', 'data_caching', 'image', 'storage_account',
                     'storage_container_name', 'data_disk_sizes_gb', 'storage_sku']

    else:
        raise CLIError('Unrecognized storage profile: {}'.format(namespace.storage_profile))

    if for_scale_set:
        # VMSS lacks some parameters, so scrub these out
        props_to_remove = ['attach_os_disk', 'storage_account']
        for prop in props_to_remove:
            if prop in required:
                required.remove(prop)
            if prop in forbidden:
                forbidden.remove(prop)

    # set default storage SKU if not provided and using an image based OS
    if not namespace.storage_sku and namespace.storage_profile not in [StorageProfile.ManagedSpecializedOSDisk, StorageProfile.SASpecializedOSDisk]:  # pylint: disable=line-too-long
        namespace.storage_sku = 'Standard_LRS' if for_scale_set else 'Premium_LRS'

    # Now verify that the status of required and forbidden parameters
    _validate_storage_required_forbidden_parameters(namespace, required, forbidden)

    if namespace.storage_profile == StorageProfile.ManagedCustomImage:
        # extract additional information from a managed custom image
        res = parse_resource_id(namespace.image)
        compute_client = _compute_client_factory()
        image_info = compute_client.images.get(res['resource_group'], res['name'])
        # pylint: disable=no-member
        namespace.os_type = image_info.storage_profile.os_disk.os_type.value
        namespace.image_data_disks = image_info.storage_profile.data_disks

    elif namespace.storage_profile == StorageProfile.ManagedSpecializedOSDisk:
        # accept disk name or ID
        namespace.attach_os_disk = _get_resource_id(
            namespace.attach_os_disk, namespace.resource_group_name, 'disks', 'Microsoft.Compute')

    if getattr(namespace, 'attach_data_disks', None):
        if not namespace.use_unmanaged_disk:
            namespace.attach_data_disks = [_get_resource_id(d, namespace.resource_group_name, 'disks',
                                                            'Microsoft.Compute') for d in namespace.attach_data_disks]

    if not namespace.os_type:
        namespace.os_type = 'windows' if 'windows' in namespace.os_offer.lower() else 'linux'


def _validate_vm_create_storage_account(namespace):

    if namespace.storage_account:
        storage_id = parse_resource_id(namespace.storage_account)
        rg = storage_id.get('resource_group', namespace.resource_group_name)
        if check_existence(storage_id['name'], rg, 'Microsoft.Storage', 'storageAccounts'):
            # 1 - existing storage account specified
            namespace.storage_account_type = 'existing'
        else:
            # 2 - params for new storage account specified
            namespace.storage_account_type = 'new'
    else:
        from azure.cli.core.profiles import ResourceType
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        storage_client = get_mgmt_service_client(ResourceType.MGMT_STORAGE).storage_accounts

        # find storage account in target resource group that matches the VM's location
        sku_tier = 'Premium' if 'Premium' in namespace.storage_sku else 'Standard'
        account = next(
            (a for a in storage_client.list_by_resource_group(namespace.resource_group_name)
             if a.sku.tier.value == sku_tier and a.location == namespace.location), None)

        if account:
            # 3 - nothing specified - find viable storage account in target resource group
            namespace.storage_account = account.name
            namespace.storage_account_type = 'existing'
        else:
            # 4 - nothing specified - create a new storage account
            namespace.storage_account_type = 'new'


def _validate_vm_create_availability_set(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    if namespace.availability_set:
        as_id = parse_resource_id(namespace.availability_set)
        name = as_id['name']
        rg = as_id.get('resource_group', namespace.resource_group_name)

        if not check_existence(name, rg, 'Microsoft.Compute', 'availabilitySets'):
            raise CLIError("Availability set '{}' does not exist.".format(name))

        namespace.availability_set = resource_id(
            subscription=get_subscription_id(),
            resource_group=rg,
            namespace='Microsoft.Compute',
            type='availabilitySets',
            name=name)


def _validate_vm_vmss_create_vnet(namespace, for_scale_set=False):

    vnet = namespace.vnet_name
    subnet = namespace.subnet
    rg = namespace.resource_group_name
    location = namespace.location
    nics = getattr(namespace, 'nics', None)

    if not vnet and not subnet and not nics:
        # if nothing specified, try to find an existing vnet and subnet in the target resource group
        client = get_network_client().virtual_networks

        # find VNET in target resource group that matches the VM's location with a matching subnet
        for vnet_match in (v for v in client.list(rg) if v.location == location and v.subnets):

            # 1 - find a suitable existing vnet/subnet
            result = None
            if not for_scale_set:
                result = next((s for s in vnet_match.subnets if s.name.lower() != 'gatewaysubnet'), None)
            else:
                def _check_subnet(s):
                    if s.name.lower() == 'gatewaysubnet':
                        return False
                    subnet_mask = s.address_prefix.split('/')[-1]
                    return _subnet_capacity_check(subnet_mask, namespace.instance_count)

                result = next((s for s in vnet_match.subnets if _check_subnet(s)), None)
            if not result:
                continue
            namespace.subnet = result.name
            namespace.vnet_name = vnet_match.name
            namespace.vnet_type = 'existing'
            return

    if subnet:
        subnet_is_id = is_valid_resource_id(subnet)
        if (subnet_is_id and vnet) or (not subnet_is_id and not vnet):
            raise CLIError("incorrect '--subnet' usage: --subnet SUBNET_ID | "
                           "--subnet SUBNET_NAME --vnet-name VNET_NAME")

        subnet_exists = \
            check_existence(subnet, rg, 'Microsoft.Network', 'subnets', vnet, 'virtualNetworks')

        if subnet_is_id and not subnet_exists:
            raise CLIError("Subnet '{}' does not exist.".format(subnet))
        elif subnet_exists:
            # 2 - user specified existing vnet/subnet
            namespace.vnet_type = 'existing'
            return
    # 3 - create a new vnet/subnet
    namespace.vnet_type = 'new'


def _subnet_capacity_check(subnet_mask, vmss_instance_count):
    mask = int(subnet_mask)
    # '2' are the reserved broadcasting addresses
    return ((1 << (32 - mask)) - 2) > vmss_instance_count


def _validate_vmss_create_subnet(namespace):
    if namespace.vnet_type == 'new':
        if namespace.subnet_address_prefix is None:
            cidr = namespace.vnet_address_prefix.split('/', 1)[0]
            i = 0
            for i in range(24, 16, -1):
                if _subnet_capacity_check(i, namespace.instance_count):
                    break
            if i < 16:
                err = "instance count '{}' is out of range of 2^16 subnet size'"
                raise CLIError(err.format(namespace.instance_count))
            namespace.subnet_address_prefix = '{}/{}'.format(cidr, i)

        if namespace.app_gateway_type and namespace.app_gateway_subnet_address_prefix is None:
            namespace.app_gateway_subnet_address_prefix = _get_next_subnet_addr_suffix(
                namespace.vnet_address_prefix, namespace.subnet_address_prefix, 24)


def _get_next_subnet_addr_suffix(vnet_cidr, subnet_cidr, new_mask):
    def _convert_to_int(address, bit_mask_len):
        a, b, c, d = [int(x) for x in address.split('.')]
        result = '{0:08b}{1:08b}{2:08b}{3:08b}'.format(a, b, c, d)
        return int(result[:-bit_mask_len], 2)

    error_msg = "usage error: --subnet-address-prefix value should be a subrange of --vnet-address-prefix's"
    # extract vnet information needed to verify the defaults we are coming out
    vnet_ip_address, mask = vnet_cidr.split('/')
    vnet_bit_mask_len = 32 - int(mask)
    vnet_int = _convert_to_int(vnet_ip_address, vnet_bit_mask_len)

    subnet_ip_address, mask = subnet_cidr.split('/')
    subnet_bit_mask_len = 32 - int(mask)

    if vnet_bit_mask_len <= subnet_bit_mask_len:
        raise CLIError(error_msg)

    candidate_int = _convert_to_int(subnet_ip_address, subnet_bit_mask_len) + 1
    if (candidate_int >> (vnet_bit_mask_len - subnet_bit_mask_len)) > vnet_int:  # overflows?
        candidate_int = candidate_int - 2  # try the other way around
        if (candidate_int >> (vnet_bit_mask_len - subnet_bit_mask_len)) > vnet_int:
            raise CLIError(error_msg)

    # format back to the cidr
    candaidate_str = '{0:32b}'.format(candidate_int << subnet_bit_mask_len)
    return '{0}.{1}.{2}.{3}/{4}'.format(int(candaidate_str[0:8], 2), int(candaidate_str[8:16], 2),
                                        int(candaidate_str[16:24], 2), int(candaidate_str[24:32], 2),
                                        new_mask)


def _validate_vm_create_nsg(namespace):

    if namespace.nsg:
        if check_existence(namespace.nsg, namespace.resource_group_name,
                           'Microsoft.Network', 'networkSecurityGroups'):
            namespace.nsg_type = 'existing'
        else:
            namespace.nsg_type = 'new'
    elif namespace.nsg == '':
        namespace.nsg_type = None
    elif namespace.nsg is None:
        namespace.nsg_type = 'new'


def _validate_vm_create_public_ip(namespace):
    if namespace.public_ip_address:
        if check_existence(namespace.public_ip_address, namespace.resource_group_name,
                           'Microsoft.Network', 'publicIPAddresses'):
            namespace.public_ip_type = 'existing'
        else:
            namespace.public_ip_type = 'new'
    elif namespace.public_ip_address == '':
        namespace.public_ip_type = None
    elif namespace.public_ip_address is None:
        namespace.public_ip_type = 'new'


def _validate_vmss_create_public_ip(namespace):
    if namespace.load_balancer_type is None and namespace.app_gateway_type is None:
        if namespace.public_ip_address:
            raise CLIError('--public-ip-address can only be used  when creating a new load '
                           'balancer or application gateway frontend.')
        namespace.public_ip_address = ''
    _validate_vm_create_public_ip(namespace)


def _validate_vm_create_nics(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    nics_value = namespace.nics
    nics = []

    if not nics_value:
        namespace.nic_type = 'new'
        return

    if not isinstance(nics_value, list):
        nics_value = [nics_value]

    for n in nics_value:
        nics.append({
            'id': n if '/' in n else resource_id(name=n,
                                                 resource_group=namespace.resource_group_name,
                                                 namespace='Microsoft.Network',
                                                 type='networkInterfaces',
                                                 subscription=get_subscription_id()),
            'properties': {
                'primary': nics_value[0] == n
            }
        })

    namespace.nics = nics
    namespace.nic_type = 'existing'
    namespace.public_ip_type = None


def _validate_vm_vmss_create_auth(namespace):
    if namespace.storage_profile in [StorageProfile.ManagedSpecializedOSDisk,
                                     StorageProfile.SASpecializedOSDisk]:
        return

    _validate_admin_username(namespace.admin_username, namespace.os_type)

    if not namespace.os_type:
        raise CLIError("Unable to resolve OS type. Specify '--os-type' argument.")

    if not namespace.authentication_type:
        # apply default auth type (password for Windows, ssh for Linux) by examining the OS type

        namespace.authentication_type = 'password' if namespace.os_type.lower() == 'windows' else 'ssh'

    if namespace.os_type.lower() == 'windows' and namespace.authentication_type == 'ssh':
        raise CLIError('SSH not supported for Windows VMs.')

    # validate proper arguments supplied based on the authentication type
    if namespace.authentication_type == 'password':
        if namespace.ssh_key_value or namespace.ssh_dest_key_path:
            raise ValueError(
                "incorrect usage for authentication-type 'password': "
                "[--admin-username USERNAME] --admin-password PASSWORD")

        from azure.cli.core.prompting import prompt_pass, NoTTYException
        try:
            if not namespace.admin_password:
                namespace.admin_password = prompt_pass('Admin Password: ', confirm=True)
        except NoTTYException:
            raise CLIError('Please specify password in non-interactive mode.')

        # validate password
        _validate_admin_password(namespace.admin_password,
                                 namespace.os_type)

    elif namespace.authentication_type == 'ssh':

        if namespace.admin_password:
            raise ValueError('Admin password cannot be used with SSH authentication type')

        validate_ssh_key(namespace)

        if not namespace.ssh_dest_key_path:
            namespace.ssh_dest_key_path = \
                '/home/{}/.ssh/authorized_keys'.format(namespace.admin_username)


def _validate_admin_username(username, os_type):
    if not username:
        raise CLIError("admin user name can not be empty")
    is_linux = (os_type.lower() == 'linux')
    # pylint: disable=line-too-long
    pattern = (r'[\\\/"\[\]:|<>+=;,?*@#()!A-Z]+' if is_linux else r'[\\\/"\[\]:|<>+=;,?*@]+')
    linux_err = r'admin user name cannot contain upper case character A-Z, special characters \/"[]:|<>+=;,?*@#()! or start with $ or -'
    win_err = r'admin user name cannot contain special characters \/"[]:|<>+=;,?*@# or ends with .'
    if re.findall(pattern, username):
        raise CLIError(linux_err if is_linux else win_err)
    if is_linux and re.findall(r'^[$-]+', username):
        raise CLIError(linux_err)
    if not is_linux and username.endswith('.'):
        raise CLIError(win_err)
    disallowed_user_names = [
        "administrator", "admin", "user", "user1", "test", "user2",
        "test1", "user3", "admin1", "1", "123", "a", "actuser", "adm",
        "admin2", "aspnet", "backup", "console", "david", "guest", "john",
        "owner", "root", "server", "sql", "support", "support_388945a0",
        "sys", "test2", "test3", "user4", "user5"]
    if username.lower() in disallowed_user_names:
        raise CLIError("This user name '{}' meets the general requirements, but is specifically disallowed for this image. Please try a different value.".format(username))


def _validate_admin_password(password, os_type):
    is_linux = (os_type.lower() == 'linux')
    max_length = 72 if is_linux else 123
    min_length = 12
    if len(password) not in range(min_length, max_length + 1):
        raise CLIError('The password length must be between {} and {}'.format(min_length,
                                                                              max_length))
    contains_lower = re.findall('[a-z]+', password)
    contains_upper = re.findall('[A-Z]+', password)
    contains_digit = re.findall('[0-9]+', password)
    contains_special_char = re.findall(r'[ `~!@#$%^&*()=+_\[\]{}\|;:.\/\'\",<>?]+', password)
    count = len([x for x in [contains_lower, contains_upper,
                             contains_digit, contains_special_char] if x])
    # pylint: disable=line-too-long
    if count < 3:
        raise CLIError('Password must have the 3 of the following: 1 lower case character, 1 upper case character, 1 number and 1 special character')


def validate_ssh_key(namespace):
    string_or_file = (namespace.ssh_key_value or
                      os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub'))
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not _is_valid_ssh_rsa_public_key(content):
        if namespace.generate_ssh_keys:
            # figure out appropriate file names:
            # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
            public_key_filepath = string_or_file
            if public_key_filepath[-4:].lower() == '.pub':
                private_key_filepath = public_key_filepath[:-4]
            else:
                private_key_filepath = public_key_filepath + '.private'
            content = _generate_ssh_keys(private_key_filepath, public_key_filepath)
            logger.warning("SSH key files '%s' and '%s' have been generated under ~/.ssh to "
                           "allow SSH access to the VM. If using machines without "
                           "permanent storage, back up your keys to a safe location.",
                           private_key_filepath, public_key_filepath)
        else:
            raise CLIError('An RSA key file or key value must be supplied to SSH Key Value. '
                           'You can use --generate-ssh-keys to let CLI generate one for you')
    namespace.ssh_key_value = content


def _generate_ssh_keys(private_key_filepath, public_key_filepath):
    import paramiko

    ssh_dir, _ = os.path.split(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        os.chmod(ssh_dir, 0o700)

    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(private_key_filepath)
    os.chmod(private_key_filepath, 0o600)

    with open(public_key_filepath, 'w') as public_key_file:
        public_key = '%s %s' % (key.get_name(), key.get_base64())
        public_key_file.write(public_key)
    os.chmod(public_key_filepath, 0o644)

    return public_key


def _is_valid_ssh_rsa_public_key(openssh_pubkey):
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression
    # A "good enough" check is to see if the key starts with the correct header.
    import struct
    try:
        from base64 import decodebytes as base64_decode
    except ImportError:
        # deprecated and redirected to decodebytes in Python 3
        from base64 import decodestring as base64_decode
    parts = openssh_pubkey.split()
    if len(parts) < 2:
        return False
    key_type = parts[0]
    key_string = parts[1]

    data = base64_decode(key_string.encode())  # pylint:disable=deprecated-method
    int_len = 4
    str_len = struct.unpack('>I', data[:int_len])[0]  # this should return 7
    return data[int_len:int_len + str_len] == key_type.encode()


def process_vm_create_namespace(namespace):
    get_default_location_from_resource_group(namespace)
    _validate_vm_create_storage_profile(namespace)
    if namespace.storage_profile in [StorageProfile.SACustomImage,
                                     StorageProfile.SAPirImage]:
        _validate_vm_create_storage_account(namespace)

    _validate_vm_create_availability_set(namespace)
    _validate_vm_vmss_create_vnet(namespace)
    _validate_vm_create_nsg(namespace)
    _validate_vm_create_public_ip(namespace)
    _validate_vm_create_nics(namespace)
    _validate_vm_vmss_create_auth(namespace)
    if namespace.secrets:
        _validate_secrets(namespace.secrets, namespace.os_type)
    if namespace.license_type and namespace.os_type.lower() != 'windows':
        raise CLIError('usage error: --license-type is only applicable on Windows VM')

# endregion

# region VMSS Create Validators


def _get_vmss_create_instance_threshold():
    return 100


def _validate_vmss_create_load_balancer_or_app_gateway(namespace):

    INSTANCE_THRESHOLD = _get_vmss_create_instance_threshold()

    # convert the single_placement_group to boolean for simpler logic beyond
    if namespace.single_placement_group is None:
        namespace.single_placement_group = namespace.instance_count <= INSTANCE_THRESHOLD
    else:
        namespace.single_placement_group = (namespace.single_placement_group == 'true')

    if not namespace.single_placement_group and namespace.load_balancer:
        raise CLIError(
            '--load-balancer is not applicable when --single-placement-group is turned off.')

    if namespace.load_balancer and namespace.application_gateway:
        raise CLIError('incorrect usage: --load-balancer NAME_OR_ID | '
                       '--application-gateway NAME_OR_ID')

    if namespace.instance_count > INSTANCE_THRESHOLD and namespace.load_balancer:
        raise CLIError(
            '--load-balancer cannot be used with --instance_count is > {}'.format(
                INSTANCE_THRESHOLD))

    # Resolve the type of balancer (if any) being used
    balancer_type = 'None'
    if namespace.load_balancer is None and namespace.application_gateway is None:
        # use defaulting rules to determine
        balancer_type = 'loadBalancer' if namespace.instance_count <= INSTANCE_THRESHOLD \
            else 'applicationGateway'
    elif namespace.load_balancer:
        balancer_type = 'loadBalancer'
    elif namespace.application_gateway:
        balancer_type = 'applicationGateway'

    if balancer_type == 'applicationGateway':

        if namespace.application_gateway:
            client = get_network_client().application_gateways
            try:
                client.get(namespace.resource_group_name, namespace.application_gateway)
                namespace.app_gateway_type = 'existing'
            except CloudError:
                namespace.app_gateway_type = 'new'
        elif namespace.application_gateway == '':
            namespace.app_gateway_type = None
        elif namespace.application_gateway is None:
            namespace.app_gateway_type = 'new'

        # AppGateway frontend
        required = []
        if namespace.app_gateway_type == 'new' and namespace.vnet_type != 'new':
            required.append('app_gateway_subnet_address_prefix')
        elif namespace.app_gateway_type == 'existing':
            required.append('backend_pool_name')
        forbidden = ['nat_pool_name', 'load_balancer']
        _validate_network_balancer_required_forbidden_parameters(
            namespace, required, forbidden, 'application gateway')

    elif balancer_type == 'loadBalancer':
        # LoadBalancer frontend
        required = []
        forbidden = ['app_gateway_subnet_address_prefix', 'application_gateway']
        _validate_network_balancer_required_forbidden_parameters(
            namespace, required, forbidden, 'load balancer')

        if namespace.load_balancer:
            if check_existence(namespace.load_balancer, namespace.resource_group_name,
                               'Microsoft.Network', 'loadBalancers'):
                namespace.load_balancer_type = 'existing'
            else:
                namespace.load_balancer_type = 'new'
        elif namespace.load_balancer == '':
            namespace.load_balancer_type = None
        elif namespace.load_balancer is None:
            namespace.load_balancer_type = 'new'


def get_network_client():
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceType.MGMT_NETWORK)


def process_vmss_create_namespace(namespace):
    get_default_location_from_resource_group(namespace)
    _validate_vm_create_storage_profile(namespace, for_scale_set=True)
    _validate_vm_vmss_create_vnet(namespace, for_scale_set=True)
    _validate_vmss_create_load_balancer_or_app_gateway(namespace)
    _validate_vmss_create_subnet(namespace)
    _validate_vmss_create_public_ip(namespace)
    _validate_vm_vmss_create_auth(namespace)

# endregion

# region disk, snapshot, image validators


def validate_vm_disk(namespace):
    namespace.disk = _get_resource_id(namespace.disk, namespace.resource_group_name,
                                      'disks', 'Microsoft.Compute')


def process_disk_or_snapshot_create_namespace(namespace):
    if namespace.source:
        usage_error = 'usage error: --source {SNAPSHOT | DISK} | --source VHD_BLOB_URI [--source-storage-account-id ID]'
        try:
            namespace.source_blob_uri, namespace.source_disk, namespace.source_snapshot = _figure_out_storage_source(namespace.resource_group_name, namespace.source)  # pylint: disable=line-too-long
            if not namespace.source_blob_uri and namespace.source_storage_account_id:
                raise CLIError(usage_error)
        except CloudError:
            raise CLIError(usage_error)


def process_image_create_namespace(namespace):
    try:
        # try capturing from VM, a most common scenario
        compute_client = _compute_client_factory()
        res_id = _get_resource_id(namespace.source, namespace.resource_group_name,
                                  'virtualMachines', 'Microsoft.Compute')
        res = parse_resource_id(res_id)
        vm_info = compute_client.virtual_machines.get(res['resource_group'], res['name'])
        # pylint: disable=no-member
        namespace.os_type = vm_info.storage_profile.os_disk.os_type.value
        namespace.source_virtual_machine = res_id
        if namespace.data_disk_sources:
            raise CLIError("'--data-disk-sources' is not allowed when capturing "
                           "images from virtual machines")
    except CloudError:
        namespace.os_blob_uri, namespace.os_disk, namespace.os_snapshot = _figure_out_storage_source(namespace.resource_group_name, namespace.source)  # pylint: disable=line-too-long
        namespace.data_blob_uris = []
        namespace.data_disks = []
        namespace.data_snapshots = []
        if namespace.data_disk_sources:
            for data_disk_source in namespace.data_disk_sources:
                source_blob_uri, source_disk, source_snapshot = _figure_out_storage_source(
                    namespace.resource_group_name, data_disk_source)
                if source_blob_uri:
                    namespace.data_blob_uris.append(source_blob_uri)
                if source_disk:
                    namespace.data_disks.append(source_disk)
                if source_snapshot:
                    namespace.data_snapshots.append(source_snapshot)
        if not namespace.os_type:
            raise CLIError("usage error: os type is required to create the image, "
                           "please specify '--os-type OS_TYPE'")


def _figure_out_storage_source(resource_group_name, source):
    source_blob_uri = None
    source_disk = None
    source_snapshot = None
    if source.lower().endswith('.vhd'):
        source_blob_uri = source
    elif '/disks/' in source.lower():
        source_disk = source
    elif '/snapshots/' in source.lower():
        source_snapshot = source
    else:
        compute_client = _compute_client_factory()
        # pylint: disable=no-member
        try:
            info = compute_client.snapshots.get(resource_group_name, source)
            source_snapshot = info.id
        except CloudError:
            info = compute_client.disks.get(resource_group_name, source)
            source_disk = info.id

    return (source_blob_uri, source_disk, source_snapshot)


def process_disk_encryption_namespace(namespace):
    namespace.disk_encryption_keyvault = _get_resource_id(namespace.disk_encryption_keyvault,
                                                          namespace.resource_group_name,
                                                          'vaults', 'Microsoft.KeyVault')

    if namespace.key_encryption_keyvault:
        if not namespace.key_encryption_key:
            raise CLIError("Incorrect usage '--key-encryption-keyvault': "
                           "'--key-encryption-key' is required")
        namespace.key_encryption_keyvault = _get_resource_id(namespace.key_encryption_keyvault,
                                                             namespace.resource_group_name,
                                                             'vaults', 'Microsoft.KeyVault')

# endregion
