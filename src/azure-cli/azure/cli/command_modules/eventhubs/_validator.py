# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
from azure.cli.core.util import CLIError


def validate_storageaccount(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.storage_account_resource_id:
        if not is_valid_resource_id(namespace.storage_account_resource_id):
            namespace.storage_account_resource_id = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage',
                type='storageAccounts',
                name=namespace.storage_account_resource_id)


def validate_partner_namespace(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.partner_namespace:
        if not is_valid_resource_id(namespace.partner_namespace):
            namespace.partner_namespace = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.EventHub',
                type='namespaces',
                name=namespace.partner_namespace)


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    subnet = namespace.subnet
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        raise CLIError('incorrect usage: [--subnet ID | --subnet NAME --vnet-name NAME]')
    delattr(namespace, 'vnet_name')


def validate_rights(namespace):
    if 'Manage' in namespace.rights:
        if 'Listen' not in namespace.rights or 'Send' not in namespace.rights:
            raise CLIError('Error : Assigning \'Manage\' to --rights requires \'Listen\' and \'Send\' to be included with. e.g. --rights Manage Send Listen')


def validate_clustercapcity(namespace):
    if namespace.capacity:
        if namespace.capacity != 1:
            raise CLIError('Error : Allowed values for Capacity of Cluster is \'1\'')
