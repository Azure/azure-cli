# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_create_db(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id

    elastic_pool_id = namespace.virtual_network_subnet_id
    elastic_pool_id_is_id = is_valid_resource_id(elastic_pool_id)
    elastic_pool_name = namespace.elastic_pool_name

    if is_valid_resource_id(elastic_pool_id) and not elastic_pool_name:
        pass
    elif elastic_pool_name and not elastic_pool_id:
        namespace.elastic_pool_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Sql',
            type='servers',
            name=namespace.server_name,
            child_type_1='elasticPools',
            child_name_1=elastic_pool_name)
    else:
        raise CLIError('incorrect usage: [--elastic-pool-id ID | --elastic-pool NAME]')
    delattr(namespace, 'elastic_pool_name')



# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id

    subnet = namespace.virtual_network_subnet_id
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        namespace.virtual_network_subnet_id = resource_id(
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
