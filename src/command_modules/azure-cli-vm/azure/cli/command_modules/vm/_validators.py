#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import math
import random
import time

from azure.cli.core.commands.arm import resource_id

def generate_guid():
    return '{}{}'.format(str(int(math.ceil(time.time())))[:9], str(random.randint(1, 100000)))

def validate_nsg_name(namespace):
    namespace.network_security_group_name = namespace.network_security_group_name \
        or '{}NSG{}'.format(namespace.vm_name, random.randint(1, 999))

def validate_vm_nics(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    nics_value = namespace.network_interface_ids
    nics = []

    if not nics_value:
        namespace.network_interface_type = 'new'
        return

    namespace.network_interface_type = 'existing'

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

    namespace.network_interface_ids = nics
    namespace.network_interface_type = 'existing'

    namespace.public_ip_address_type = 'none'

def validate_default_vnet(namespace):
    ns = namespace
    if not ns.virtual_network and not ns.virtual_network_type:
        from azure.mgmt.network import NetworkManagementClient
        from azure.mgmt.resource.resources import ResourceManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client

        resource_client = get_mgmt_service_client(ResourceManagementClient)
        vnet_client = get_mgmt_service_client(NetworkManagementClient).virtual_networks

        rg = resource_client.resource_groups.get(ns.resource_group_name)
        location = ns.location or rg.location # pylint: disable=no-member

        # find VNET in target resource group that matches the VM's location
        vnet = next((v for v in vnet_client.list(rg.name) if v.location == location), None) # pylint: disable=no-member

        if vnet:
            try:
                ns.subnet_name = vnet.subnets[0].name
                ns.virtual_network = vnet.name
                ns.virtual_network_type = 'existingName'
            except KeyError:
                pass

def validate_default_storage_account(namespace):
    ns = namespace
    if not ns.storage_account and not ns.storage_account_type:
        from azure.mgmt.storage import StorageManagementClient
        from azure.mgmt.resource.resources import ResourceManagementClient
        from azure.cli.core.commands.client_factory import get_mgmt_service_client

        resource_client = get_mgmt_service_client(ResourceManagementClient)
        storage_client = get_mgmt_service_client(StorageManagementClient).storage_accounts

        rg = resource_client.resource_groups.get(ns.resource_group_name)
        location = ns.location or rg.location # pylint: disable=no-member

        sku_tier = 'Premium' if 'Premium' in ns.storage_type else 'Standard'
        # find storage account in target resource group that matches the VM's location
        account = next((a for a in storage_client.list_by_resource_group(ns.resource_group_name)
                        if a.sku.tier.value == sku_tier and a.location == location), None)

        if account:
            ns.storage_account = account.name
            ns.storage_account_type = 'existingName'
        else:
            ns.storage_account = 'vhd{}'.format(generate_guid())

def validate_default_os_disk(namespace):
    if not namespace.os_disk_name:
        namespace.os_disk_name = 'osdisk{}'.format(generate_guid())
