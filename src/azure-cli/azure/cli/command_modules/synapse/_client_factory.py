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


def cf_synapse_client_accesscontrol_factory(cli_ctx, workspace_name):
    from azure.synapse.accesscontrol import AccessControlClient
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cli_ctx)
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, _ = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.synapse_analytics_resource_id,
        subscription_id=subscription_id
    )
    return AccessControlClient(
        credential=cred,
        endpoint='{}{}{}'.format("https://", workspace_name, cli_ctx.cloud.suffixes.synapse_analytics_endpoint)
    )


def cf_graph_client_factory(cli_ctx, **_):
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import configure_common_settings
    from azure.graphrbac import GraphRbacManagementClient
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    client = GraphRbacManagementClient(cred, tenant_id,
                                       base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    configure_common_settings(cli_ctx, client)
    return client


def cf_synapse_client_artifacts_factory(cli_ctx, workspace_name):
    from azure.synapse.artifacts import ArtifactsClient
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cli_ctx)
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, _ = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.synapse_analytics_resource_id,
        subscription_id=subscription_id
    )
    return ArtifactsClient(
        credential=cred,
        endpoint='{}{}{}'.format("https://", workspace_name, cli_ctx.cloud.suffixes.synapse_analytics_endpoint)
    )


def cf_synapse_linked_service(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).linked_service


def cf_synapse_dataset(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).dataset


def cf_synapse_pipeline(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).pipeline


def cf_synapse_pipeline_run(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).pipeline_run
