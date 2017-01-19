# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from azure.cli.core.commands.arm import resource_id, parse_resource_id, is_valid_resource_id
from azure.cli.core._util import CLIError
from azure.cli.command_modules.vm._vm_utils import (
    read_content_if_is_file, random_string, check_existence)
from azure.cli.command_modules.vm._template_builder import StorageProfile

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

def validate_location(namespace):
    if not namespace.location:
        from azure.mgmt.resource.resources import ResourceManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        resource_client = get_mgmt_service_client(ResourceManagementClient)
        rg = resource_client.resource_groups.get(namespace.resource_group_name)
        namespace.location = rg.location  # pylint: disable=no-member

# region VM Create Validators

def _validate_vm_create_storage_profile(namespace):

    from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc

    image = namespace.image

    # 1 - Create native disk with VHD URI
    if image.lower().endswith('.vhd'):
        namespace.storage_profile = StorageProfile.SACustomImage
        if not namespace.os_type:
            raise CLIError('--os-type TYPE is required for a native OS VHD disk.')
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

    namespace.os_type = 'windows' if 'windows' in namespace.os_offer.lower() else 'linux'

    # 2 - Create native disk from PIR image
    namespace.storage_profile = StorageProfile.SAPirImage  # pylint: disable=redefined-variable-type

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
        for vnet_match in (v for v in client.list(rg) if v.location == location and v.subnets):

            # 1 - find a suitable existing vnet/subnet
            subnet_match = next(
                (s.name for s in vnet_match.subnets if s.name != 'GatewaySubnet'), None
            )
            if not subnet_match:
                continue
            namespace.subnet = subnet_match.name
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

def _validate_vm_create_auth(namespace):

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
            import getpass
            while True:
                password_1 = getpass.getpass('Admin Password: ')
                password_2 = getpass.getpass('Confirm Password: ')
                if password_1 == password_2:
                    namespace.admin_password = password_1
                    break
                else:
                    # TODO: print error message
                    pass

    elif namespace.authentication_type == 'ssh':

        if not namespace.ssh_key_value or namespace.admin_password:
            raise ValueError(
                "incorrect usage for authentication-type 'ssh': "
                "--ssh-key-value VALUE_OR_PATH [--ssh-dest-key-path PATH]")

        # load the SSH key and set the dest key path if not supplied
        namespace.ssh_key_value = read_content_if_is_file(namespace.ssh_key_value)
        if not namespace.ssh_key_value:
            import os
            ssh_key_file = os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub')
            if os.path.isfile(ssh_key_file):
                with open(ssh_key_file) as f:
                    namespace.ssh_key_value = f.read()
            else:
                raise CLIError('An RSA key file or key value must be supplied to SSH Key Value')

        if not namespace.ssh_dest_key_path:
            namespace.ssh_dest_key_path = \
                '/home/{}/.ssh/authorized_keys'.format(namespace.admin_username)

def process_vm_create_namespace(namespace):
    validate_location(namespace)
    _validate_vm_create_storage_profile(namespace)
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
    _validate_vm_create_storage_profile(namespace)
    _validate_vmss_create_load_balancer(namespace)
    _validate_vm_create_vnet(namespace)
    _validate_vm_create_public_ip(namespace)
    _validate_vm_create_auth(namespace)

# endregion
