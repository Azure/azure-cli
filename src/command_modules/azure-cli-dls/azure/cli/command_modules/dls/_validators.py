# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.util import CLIError

from azure.cli.core.commands.client_factory import get_mgmt_service_client


# Helpers
def _get_resource_group_from_account_name(client, account_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    from msrestazure.tools import parse_resource_id
    for acct in client.list():
        id_comps = parse_resource_id(acct.id)
        if id_comps['name'] == account_name:
            return id_comps['resource_group']
    raise CLIError(
        "The Resource 'Microsoft.DataLakeStore/accounts/{}'".format(account_name) +
        " not found within subscription: {}".format(client.config.subscription_id))


# COMMAND NAMESPACE VALIDATORS
def validate_resource_group_name(cmd, ns):
    from azure.mgmt.datalake.store import DataLakeStoreAccountManagementClient
    if not ns.resource_group_name:
        try:
            account_name = ns.name
        except AttributeError:
            account_name = ns.account_name
        client = get_mgmt_service_client(cmd.cli_ctx, DataLakeStoreAccountManagementClient).accounts
        group_name = _get_resource_group_from_account_name(client, account_name)
        ns.resource_group_name = group_name


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
