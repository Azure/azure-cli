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


def synapse_spark_factory(cli_ctx, workspace_name, sparkpool_name):
    from azure.synapse.spark import SparkClient
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cli_ctx)
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, _ = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.synapse_analytics_resource_id,
        subscription_id=subscription_id
    )
    return SparkClient(
        credential=cred,
        endpoint='{}{}{}'.format("https://", workspace_name, cli_ctx.cloud.suffixes.synapse_analytics_endpoint),
        spark_pool_name=sparkpool_name
    )


def cf_synapse_spark_batch(cli_ctx, workspace_name, sparkpool_name):
    return synapse_spark_factory(cli_ctx, workspace_name, sparkpool_name).spark_batch


def cf_synapse_spark_session(cli_ctx, workspace_name, sparkpool_name):
    return synapse_spark_factory(cli_ctx, workspace_name, sparkpool_name).spark_session
