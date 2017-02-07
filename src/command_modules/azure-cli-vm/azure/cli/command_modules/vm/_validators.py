# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re

from msrestazure.azure_exceptions import CloudError

from azure.cli.core.commands.arm import resource_id, parse_resource_id, is_valid_resource_id
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core._util import CLIError
from ._client_factory import _compute_client_factory
from azure.cli.command_modules.vm._vm_utils import random_string, check_existence
from azure.cli.command_modules.vm._template_builder import StorageProfile
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


def validate_nsg_name(namespace):
    namespace.network_security_group_name = namespace.network_security_group_name \
        or '{}_NSG_{}'.format(namespace.vm_name, random_string(8))


def _get_resource_id(val, resource_group, resource_type, resource_namespace):
    if is_valid_resource_id(val):
        return val
    else:
        return resource_id(
            name=val,
            resource_group=resource_group,
            namespace=resource_namespace,
            type=resource_type,
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


def validate_location(namespace):
    if not namespace.location:
        from azure.mgmt.resource.resources import ResourceManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        resource_client = get_mgmt_service_client(ResourceManagementClient)
        rg = resource_client.resource_groups.get(namespace.resource_group_name)
        namespace.location = rg.location  # pylint: disable=no-member


# region VM Create Validators

def _validate_vm_create_storage_profile(namespace, for_scale_set=False):  # pylint: disable=too-many-branches, too-many-statements

    from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc

    image = namespace.image or ''

    # do VM specific validating
    if not for_scale_set:
        if namespace.managed_os_disk:
            if namespace.image:
                raise CLIError("'--image' is not applicable when attach to an existing os disk")
            if not namespace.os_type:
                raise CLIError('--os-type TYPE is required when attach to an existing os disk')
        else:
            if not image:
                raise CLIError("Please provide parameter value to '--image'")

    if image.lower().endswith('.vhd'):
        if not namespace.os_type:
            raise CLIError('--os-type TYPE is required for a native OS VHD disk.')

    valid_managed_skus = ['premium_lrs', 'standard_lrs']
    valid_unmanaged_skus = valid_managed_skus + ['standard_grs', 'standard_ragrs', 'standard_zrs']

    if namespace.use_unmanaged_disk:
        if namespace.storage_sku.lower() not in valid_unmanaged_skus:
            raise CLIError("Invalid storage sku '{}', please choose from '{}'".format(
                namespace.storage_sku, valid_unmanaged_skus))
        if namespace.data_disk_sizes_gb:
            raise CLIError("'--data-disk-sizes-gb' is only applicable when use managed disks")
        if '/images/' in namespace.image.lower():
            raise CLIError("VM/VMSS created from a managed custom image must use managed disks")
        if not for_scale_set and namespace.managed_os_disk:
            raise CLIError("'--use-unmanaged-disk' is ignored when attach to a managed os disk")
    else:
        if namespace.storage_sku.lower() not in valid_managed_skus:
            err = "invalid storage sku '{}' to use for managed os disks, please choose from '{}'"
            raise CLIError(err.format(namespace.storage_sku, valid_managed_skus))
        if for_scale_set and namespace.os_disk_name:
            raise CLIError("'--os-disk-name' is not allowed for scale sets using managed disks")
        if not for_scale_set and namespace.storage_account:
            raise CLIError("'--storage-account' is only applicable when use unmanaged disk."
                           " Please either remove it or turn on '--use-unmanaged-disk'")

    # attempt to parse an URN
    urn_match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', image)
    if urn_match:
        namespace.os_publisher = urn_match.group(1)
        namespace.os_offer = urn_match.group(2)
        namespace.os_sku = urn_match.group(3)
        namespace.os_version = urn_match.group(4)
        namespace.storage_profile = (StorageProfile.SAPirImage
                                     if namespace.use_unmanaged_disk
                                     else StorageProfile.ManagedPirImage)
    elif is_valid_resource_id(image):
        namespace.storage_profile = StorageProfile.ManagedCustomImage
    elif image.lower().endswith('.vhd'):
        # pylint: disable=redefined-variable-type
        namespace.storage_profile = StorageProfile.SACustomImage
    elif not for_scale_set and namespace.managed_os_disk:
        res = parse_resource_id(namespace.managed_os_disk)
        name = res['name']
        rg = res.get('resource_group', namespace.resource_group_name)
        namespace.managed_os_disk = resource_id(
            subscription=get_subscription_id(),
            resource_group=rg,
            namespace='Microsoft.Compute',
            type='disks',
            name=name)
        namespace.storage_profile = StorageProfile.ManagedSpecializedOSDisk
    else:
        images = load_images_from_aliases_doc()
        matched = next((x for x in images if x['urnAlias'].lower() == image.lower()), None)
        if matched:
            namespace.os_publisher = matched['publisher']
            namespace.os_offer = matched['offer']
            namespace.os_sku = matched['sku']
            namespace.os_version = matched['version']
            namespace.storage_profile = (StorageProfile.SAPirImage
                                         if namespace.use_unmanaged_disk
                                         else StorageProfile.ManagedPirImage)
        else:
            # last try: is it a custom image name?
            compute_client = _compute_client_factory()
            try:
                compute_client.images.get(namespace.resource_group_name, image)
                image = namespace.image = _get_resource_id(image, namespace.resource_group_name,
                                                           'images', 'Microsoft.Compute')
                namespace.storage_profile = StorageProfile.ManagedCustomImage
            except CloudError:
                err = 'Invalid image "{}". Use a custom image name, id, or pick one from {}'
                raise CLIError(err.format(image, [x['urnAlias'] for x in images]))

    if namespace.storage_profile == StorageProfile.ManagedCustomImage:
        res = parse_resource_id(image)
        compute_client = _compute_client_factory()
        image_info = compute_client.images.get(res['resource_group'], res['name'])
        # pylint: disable=no-member
        namespace.os_type = image_info.storage_profile.os_disk.os_type.value
        namespace.image_data_disks = image_info.storage_profile.data_disks

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
        from azure.mgmt.storage import StorageManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        storage_client = get_mgmt_service_client(StorageManagementClient).storage_accounts

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


def _validate_vm_create_vnet(namespace):

    vnet = namespace.vnet_name
    subnet = namespace.subnet
    rg = namespace.resource_group_name
    location = namespace.location
    nics = getattr(namespace, 'nics', None)

    if not vnet and not subnet and not nics:
        # if nothing specified, try to find an existing vnet and subnet in the target resource group
        from azure.mgmt.network import NetworkManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        client = get_mgmt_service_client(NetworkManagementClient).virtual_networks

        # find VNET in target resource group that matches the VM's location and has a subnet
        for vnet_match in (v for v in client.list(rg) if v.location == location and v.subnets):

            # 1 - find a suitable existing vnet/subnet
            subnet_match = next(
                (s.name for s in vnet_match.subnets if s.name.lower() != 'gatewaysubnet'), None
            )
            if not subnet_match:
                continue
            namespace.subnet = subnet_match
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


def _validate_vmss_create_subnet(namespace):
    # TODO: we can consider for non-new sceanrio there are user asks
    if namespace.vnet_type == 'new':
        if namespace.subnet_address_prefix is None:
            cidr = namespace.vnet_address_prefix.split('/', 1)[0]
            i = 0
            for i in range(8, 32, 1):
                if 2 << i > namespace.instance_count:
                    break
                i = i + 1
            if i > 32:
                err = "instance count '{}' is out of range of 32 bits IP addresses'"
                raise CLIError(err.format(namespace.instance_count))
            namespace.subnet_address_prefix = '{}/{}'.format(cidr, 32 - i)


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
    if namespace.load_balancer_type is None:
        if namespace.public_ip_address:
            raise CLIError('--public-ip-address is not applicable when there is no load-balancer '
                           'attached, or implictly disabled due to 100+ instance count')
        namespace.public_ip_address = ''
    _validate_vm_create_public_ip(namespace)


def _validate_vm_create_nics(namespace):
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


def _validate_vm_create_auth(namespace):
    if namespace.storage_profile == StorageProfile.ManagedSpecializedOSDisk:
        return

    if len(namespace.admin_username) < 6 or namespace.admin_username.lower() == 'root':
        # prompt for admin username if inadequate
        from azure.cli.core.prompting import prompt, NoTTYException
        try:
            logger.warning("Cannot use admin username: %s. Admin username should be at "
                           "least 6 characters and cannot be 'root'", namespace.admin_username)
            namespace.admin_username = prompt('Admin Username: ')
        except NoTTYException:
            raise CLIError('Please specify a valid admin username in non-interactive mode.')

    if not namespace.os_type:
        raise CLIError("Unable to resolve OS type. Specify '--os-type' argument.")

    if not namespace.authentication_type:
        # apply default auth type (password for Windows, ssh for Linux) by examining the OS type
        namespace.authentication_type = 'password' if namespace.os_type == 'windows' else 'ssh'

    if namespace.os_type == 'windows' and namespace.authentication_type == 'ssh':
        raise CLIError('SSH not supported for Windows VMs.')

    # validate proper arguments supplied based on the authentication type
    if namespace.authentication_type == 'password':
        if namespace.ssh_key_value or namespace.ssh_dest_key_path:
            raise ValueError(
                "incorrect usage for authentication-type 'password': "
                "[--admin-username USERNAME] --admin-password PASSWORD")

        if not namespace.admin_password:
            # prompt for admin password if not supplied
            from azure.cli.core.prompting import prompt_pass, NoTTYException
            try:
                namespace.admin_password = prompt_pass('Admin Password: ', confirm=True)
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')

    elif namespace.authentication_type == 'ssh':

        if namespace.admin_password:
            raise ValueError('Admin password cannot be used with SSH authentication type')

        validate_ssh_key(namespace)

        if not namespace.ssh_dest_key_path:
            namespace.ssh_dest_key_path = \
                '/home/{}/.ssh/authorized_keys'.format(namespace.admin_username)


def validate_ssh_key(namespace):
    string_or_file = (namespace.ssh_key_value or
                      os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub'))
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
            logger.warning('Created SSH key files: %s,%s',
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
    # http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression # pylint: disable=line-too-long
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
    validate_location(namespace)
    _validate_vm_create_storage_profile(namespace)
    if namespace.storage_profile in [StorageProfile.SACustomImage,
                                     StorageProfile.SAPirImage]:
        _validate_vm_create_storage_account(namespace)

    _validate_vm_create_availability_set(namespace)
    _validate_vm_create_vnet(namespace)
    _validate_vm_create_nsg(namespace)
    _validate_vm_create_public_ip(namespace)
    _validate_vm_create_nics(namespace)
    _validate_vm_create_auth(namespace)


# endregion

# region VMSS Create Validators


def _validate_vmss_create_load_balancer(namespace):
    # convert the single_placement_group to boolean for simpler logic beyond
    if namespace.single_placement_group is None:
        namespace.single_placement_group = namespace.instance_count <= 100
    else:
        namespace.single_placement_group = (namespace.single_placement_group == 'true')

    if not namespace.single_placement_group:
        if namespace.load_balancer:
            raise CLIError('--load-balancer is not applicable when --single-placement-group is '
                           'explictly turned off or implictly turned off for 100+ instance count')
        namespace.load_balancer = ''

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


def process_vmss_create_namespace(namespace):
    validate_location(namespace)
    _validate_vm_create_storage_profile(namespace, for_scale_set=True)
    _validate_vmss_create_load_balancer(namespace)
    _validate_vm_create_vnet(namespace)
    _validate_vmss_create_subnet(namespace)
    _validate_vmss_create_public_ip(namespace)
    _validate_vm_create_auth(namespace)

# endregion

# region disk, snapshot, image validators


def validate_vm_disk(namespace):
    namespace.disk = _get_resource_id(namespace.disk, namespace.resource_group_name,
                                      'disks', 'Microsoft.Compute')


def process_disk_or_snapshot_create_namespace(namespace):
    if namespace.source:
        try:
            namespace.source_blob_uri, namespace.source_disk, namespace.source_snapshot = _figure_out_storage_source(namespace.resource_group_name, namespace.source)  # pylint: disable=line-too-long
        except CloudError:
            raise CLIError("Incorrect '--source' usage: --source VHD_BLOB_URI | SNAPSHOT | DISK")


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
    source = source.lower()
    source_blob_uri = None
    source_disk = None
    source_snapshot = None
    if source.lower().endswith('.vhd'):
        source_blob_uri = source
    elif '/disks/' in source:
        source_disk = source
    elif '/snapshots/' in source:
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


# endregion
