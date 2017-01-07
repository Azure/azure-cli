# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import math
import random
import re
import time

from azure.cli.core.commands.arm import resource_id, parse_resource_id, is_valid_resource_id
from azure.cli.core._util import CLIError
from azure.cli.command_modules.vm._vm_utils import (
    read_content_if_is_file, random_string, check_existence)
from azure.cli.command_modules.vm._experimental import StorageProfile

def validate_nsg_name(namespace):
    namespace.network_security_group_name = namespace.network_security_group_name \
        or '{}_NSG_{}'.format(namespace.vm_name, random_string(8))

def _get_nic_id(val, resource_group, subscription):
    if is_valid_resource_id(val):
        return val
    else:
        return resource_id(
            name=val,
            resource_group=resource_group,
            namespace='Microsoft.Network',
            type='networkInterfaces',
            subscription=subscription)


def validate_vm_nic(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    namespace.nic = _get_nic_id(namespace.nic, namespace.resource_group_name, get_subscription_id())


def validate_vm_nics(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id

    subscription = get_subscription_id()
    rg = namespace.resource_group_name
    nic_ids = []

    for n in namespace.nics:
        nic_ids.append(_get_nic_id(n, rg, subscription))
    namespace.nics = nic_ids

    if hasattr(namespace, 'primary_nic') and namespace.primary_nic:
        namespace.primary_nic = _get_nic_id(namespace.primary_nic, rg, subscription)

# region VM Create Validators

def _validate_vm_create_location(namespace):
    if not namespace.location:
        from azure.mgmt.resource.resources import ResourceManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        resource_client = get_mgmt_service_client(ResourceManagementClient)
        rg = resource_client.resource_groups.get(namespace.resource_group_name)
        namespace.location = rg.location

def _validate_vm_create_storage_profile(namespace):

    from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc

    image = namespace.image
    managed_disk = namespace.managed_disk

    if (image and managed_disk) or (not image and not managed_disk):
        raise ValueError('incorrect usage: --image IMAGE [--os-type TYPE] | '
                         '--managed-disk NAME_OR_ID --os-type TYPE')

    # 1 - Attach existing managed disk
    if managed_disk:
        namespace.storage_profile = StorageProfile.MDAttachExisting
        # TODO: Add logic to ensure other parameters were not supplied
        raise CLIError("TODO: add name or id logic to get the ID")
        return

    # 2 - Create native disk with VHD URI
    if image.lower().endswith('.vhd'):
        namespace.storage_profile = StorageProfile.SACustomImage
        if not namespace.os_type:
            raise CLIError('--os-type TYPE is required for a native OS VHD disk.')
        return

    # 3 - Create managed disk with custom managed image
    image_id = parse_resource_id(image)
    if image_id and image_id.get('type', None) == 'images' and \
        image_id.get('namespace', None) == 'Microsoft.Compute':
            namespace.storage_profile = StorageProfile.MDCustomImage
            # TODO: ensure extra parameters not supplied
            # TODO: retrieve image and examine the storage_profile.os_disk.os_type field to set
            # namespace.os_type = 'windows'/'linux'
            return

    # attempt to parse an URN
    urn_match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', image)
    if urn_match:
        namespace.os_publisher = urn_match.group(1)
        namespace.os_offer = urn_match.group(2)
        namespace.os_sku = urn_match.group(3)
        namespace.os_version = urn_match.group(4)
    else:
        images = load_images_from_aliases_doc()
        matched = next((x for x in images if x['urnAlias'].lower() == image.lower()), None)
        if matched is None:
            raise CLIError('Invalid image "{}". Please pick one from {}' \
                .format(image, [x['urnAlias'] for x in images]))
        namespace.os_publisher = matched['publisher']
        namespace.os_offer = matched['offer']
        namespace.os_sku = matched['sku']
        namespace.os_version = matched['version']

    if namespace.use_native_disk:
        # 4 - Create native disk from PIR image
        namespace.storage_profile = StorageProfile.SAPirImage
    else:
        # 5 - Create managed disk from PIR image
        namespace.storage_profile = StorageProfile.MDPirImage

def _validate_vm_create_storage_account(namespace):

    if namespace.storage_profile not in [StorageProfile.SACustomImage, StorageProfile.SAPirImage]:
        # TODO: verify Native disk parameters NOT specified
        raise CLIError('TODO: Verify native disk parameters NOT specified...')
        namespace.storage_account_type = None
        return

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

        from azure.cli.core.commands.client_factory import get_subscription_id
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

    if not vnet and not subnet:
        # if nothing specified, try to find an existing vnet and subnet in the target resource group
        from azure.mgmt.network import NetworkManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        client = get_mgmt_service_client(NetworkManagementClient).virtual_networks

        # find VNET in target resource group that matches the VM's location and has a subnet
        vnet_match = next((v for v in client.list(rg) if v.location == location and v.subnets), None) # pylint: disable=no-member

        # 1 - find a suitable existing vnet/subnet
        if vnet_match:
            namespace.subnet = vnet_match.subnets[0].name
            namespace.vnet_name = vnet_match.name
            namespace.vnet_type = 'existing'
            return

    if subnet:
        subnet_is_id = is_valid_resource_id(subnet)
        if (subnet_is_id and vnet) or (not subnet_is_id and not vnet):
            raise CLIError("incorrect '--subnet' usage: --subnet SUBNET_ID | "
                           "--subnet SUBNET_NAME --vnet-name VNET_NAME")

        subnet_exists = check_existence(subnet, rg, 'Microsoft.Network', 'subnets', vnet, 'virtualNetworks')

        if subnet_is_id and not subnet_exists:
            raise CLIError("Subnet '{}' does not exist.".format(subnet))
        elif subnet_exists:
            # 2 - user specified existing vnet/subnet
            namespace.vnet_type = 'existing'
            return

    # 3 - create a new vnet/subnet
    namespace.vnet_type = 'new'

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

#def _handle_auth_types(**kwargs):
#    if kwargs['command'] != 'vm create' and kwargs['command'] != 'vmss create':
#        return

#    args = kwargs['args']

#    is_windows = 'Windows' in args.os_offer \
#        and getattr(args, 'custom_os_disk_type', None) != 'linux'

#    if not args.authentication_type:
#        args.authentication_type = 'password' if is_windows else 'ssh'

#    if args.authentication_type == 'password':
#        if args.ssh_dest_key_path:
#            raise CLIError('SSH parameters cannot be used with password authentication type')
#        elif not args.admin_password:
#            import getpass
#            args.admin_password = getpass.getpass('Admin Password: ')
#    elif args.authentication_type == 'ssh':
#        if args.admin_password:
#            raise CLIError('Admin password cannot be used with SSH authentication type')

#        ssh_key_file = os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub')
#        if not args.ssh_key_value:
#            if os.path.isfile(ssh_key_file):
#                with open(ssh_key_file) as f:
#                    args.ssh_key_value = f.read()
#            else:
#                raise CLIError('An RSA key file or key value must be supplied to SSH Key Value')

#    if hasattr(args, 'network_security_group_type'):
#        args.network_security_group_rule = 'RDP' if is_windows else 'SSH'

#    if hasattr(args, 'nat_backend_port') and not args.nat_backend_port:
#        args.nat_backend_port = '3389' if is_windows else '22'


def _validate_vm_create_auth(namespace):

    if not namespace.authentication_type:
        # apply default auth type (password for Windows, ssh for Linux) by examining the OS type
        if namespace.storage_profile in [StorageProfile.SAPirImage, StorageProfile.MDPirImage]:
            namespace.authentication_type = 'password' \
                if 'Windows' in namespace.os_publisher else 'ssh'
        else:
            if not namespace.os_type:
                raise CLIError("Unable to resolve OS type. Specify '--os-type' argument.")
            namespace.authentication_type = 'password' if namespace.os_type == 'windows' else 'ssh'

    # validate proper arguments supplied based on the authentication type
    if namespace.authentication_type == 'password':
        if not namespace.admin_password or namespace.ssh_key_value or namespace.ssh_dest_key_path:
            raise ValueError(
                "incorrect usage for authentication-type 'password': "
                "[--admin-username USERNAME] --admin-password PASSWORD")
    elif namespace.authentication_type == 'ssh':
        if not namespace.ssh_key_value or namespace.admin_password:
            raise ValueError(
                "incorrect usage for authentication-type 'ssh': "
                "--ssh-key-value VALUE_OR_PATH [--ssh-dest-key-path PATH]")

        # load the SSH key and set the dest key path if not supplied
        namespace.ssh_key_value = read_content_if_is_file(namespace.ssh_key_value)
        if not namespace.ssh_dest_key_path:
            namespace.ssh_dest_key_path = \
                '/home/{}/.ssh/authorized_keys'.format(namespace.admin_username)

def process_vm_create_namespace(namespace):
    _validate_vm_create_location(namespace)
    _validate_vm_create_storage_profile(namespace)
    _validate_vm_create_storage_account(namespace)
    _validate_vm_create_availability_set(namespace)
    _validate_vm_create_vnet(namespace)
    _validate_vm_create_nsg(namespace)
    _validate_vm_create_public_ip(namespace)
    _validate_vm_create_nics(namespace)
    _validate_vm_create_auth(namespace)

# endregion