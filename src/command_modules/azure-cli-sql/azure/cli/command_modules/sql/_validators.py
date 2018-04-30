# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from msrestazure.tools import resource_id, is_valid_resource_id
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError

# Important note: if cmd validator exists, then individual param validators will not be
# executed. See C:\git\azure-cli\env\lib\site-packages\knack\invocation.py `def _validation`


###############################################
#                sql db                       #
###############################################


def validate_elastic_pool_id(cmd, namespace):

    # If elastic_pool_id is specified but it is not a valid resource id,
    # then assume that user specified elastic pool name which we need to
    # convert to elastic pool id.
    if namespace.elastic_pool_id and not is_valid_resource_id(namespace.elastic_pool_id):
        namespace.elastic_pool_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Sql',
            type='servers',
            name=namespace.server_name,
            child_type_1='elasticPools',
            child_name_1=namespace.elastic_pool_id)


###############################################
#                sql server vnet-rule         #
###############################################


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):

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
