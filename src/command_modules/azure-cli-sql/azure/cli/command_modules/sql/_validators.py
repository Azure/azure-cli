# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from msrestazure.tools import resource_id, is_valid_resource_id
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError
from azure.mgmt.sql.models import (
    CapabilityStatus,
    DatabaseEdition,
    Sku
)
from ._util import (
    get_sql_capabilities_operations
)

# Important note: if cmd validator exists, then individual param validators will not be
# executed. See C:\git\azure-cli\env\lib\site-packages\knack\invocation.py `def _validation`


###############################################
#                sql db                       #
###############################################


def _validate_db_sku(cmd, namespace):

    # Convert sku string to sku object
    if namespace.sku:
        namespace.sku = Sku(namespace.sku)

    # Process tier into sku object
    if namespace.tier:
        if namespace.sku:
            namespace.sku.tier = namespace.tier
        else:
            # Get capabilities for this edition
            from .custom import db_list_capabilities
            edition_capabilities = db_list_capabilities(
                get_sql_capabilities_operations(cmd.cli_ctx),
                edition=namespace.tier
            )

            if not edition_capabilities:
                raise CLIError('Invalid tier {}'.format(namespace.tier))

            # Get default sku for this edition
            default_slo = next((slo for slo in edition_capabilities.supported_service_level_objectives
                                if slo.status == CapabilityStatus.default.value), None)
            if not default_slo:
                raise CLIError('No default sku found for tier {}'.format(namespace.tier))

            namespace.sku = default_slo.sku

    # Process capacity into sku object
    if namespace.capacity:
        if namespace.sku:
            namespace.sku.capacity = namespace.capacity
        else:
            raise CLIError('If --capacity is specfied, --sku and/or --tier are required')


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


def _validate_db_edition(cmd, namespace):  # pylint: disable=unused-argument

    # pylint: disable=no-member
    if namespace.tier and namespace.tier.lower() == DatabaseEdition.data_warehouse.value.lower():
        raise CLIError('Azure SQL Data Warehouse can be created with the command `az sql dw create`.')


def validate_create_db(cmd, namespace):

    pass
    # _validate_elastic_pool_id(cmd, namespace)
    # _validate_db_sku(cmd, namespace)
    # _validate_db_edition(cmd, namespace)


###############################################
#                sql elastic-pool             #
###############################################


def _validate_elastic_pool_sku(cmd, namespace):

    # Convert sku string to sku object
    if namespace.sku:
        namespace.sku = Sku(namespace.sku)

    # Process tier into sku object
    if namespace.tier:
        if namespace.sku:
            namespace.sku.tier = namespace.tier
        else:
            # Get capabilities for this edition
            from .custom import elastic_pool_list_capabilities
            edition_capabilities = elastic_pool_list_capabilities(
                get_sql_capabilities_operations(cmd.cli_ctx),
                edition=namespace.tier
            )

            if not edition_capabilities:
                raise CLIError('Invalid tier {}'.format(namespace.tier))

            # Get default sku for this edition
            default_perf_level = next((pl for pl in edition_capabilities.supported_elastic_pool_performance_levels
                                       if pl.status == CapabilityStatus.default.value), None)
            if not default_perf_level:
                raise CLIError('No default sku found for tier {}'.format(namespace.tier))

            namespace.sku = default_perf_level.sku

    # Process capacity into sku object
    if namespace.capacity:
        if namespace.sku:
            namespace.sku.capacity = namespace.capacity
        else:
            raise CLIError('If --capacity is specfied, --sku and/or --tier are required')


def validate_create_elastic_pool(cmd, namespace):

    _validate_elastic_pool_sku(cmd, namespace)


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
