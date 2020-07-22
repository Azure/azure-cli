# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def cf_synapse(cli_ctx, *_):

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.synapse import SynapseManagementClient
    return get_mgmt_service_client(cli_ctx, SynapseManagementClient)


def cf_synapse_client_workspace_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).workspaces


def cf_synapse_client_bigdatapool_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).big_data_pools


def cf_synapse_client_sqlpool_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).sql_pools


def cf_synapse_client_ipfirewallrules_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).ip_firewall_rules


def cf_synapse_client_operations_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).operations
