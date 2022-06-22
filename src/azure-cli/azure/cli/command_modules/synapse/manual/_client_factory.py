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


def cf_synapse_client_workspace_aad_admins_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).workspace_aad_admins


def cf_synapse_client_bigdatapool_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).big_data_pools


def cf_synapse_client_sqlpool_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).sql_pools


def cf_synapse_client_sqlpool_sensitivity_labels_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).sql_pool_sensitivity_labels


def cf_synapse_client_restorable_dropped_sqlpools_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).restorable_dropped_sql_pools


def cf_synapse_client_sqlpool_transparent_data_encryptions_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).sql_pool_transparent_data_encryptions


def cf_synapse_client_sqlpool_security_alert_policies_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).sql_pool_security_alert_policies


def cf_synapse_client_sqlpool_blob_auditing_policies_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).sql_pool_blob_auditing_policies


def cf_synapse_client_sqlserver_blob_auditing_policies_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).workspace_managed_sql_server_blob_auditing_policies


def cf_synapse_client_ipfirewallrules_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).ip_firewall_rules


def cf_synapse_client_cmk_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).keys


def cf_synapse_client_managed_identity_sqlcontrol_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).workspace_managed_identity_sql_control_settings


def cf_synapse_client_integrationruntimes_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtimes


def cf_synapse_client_integrationruntimeauthkeys_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_auth_keys


def cf_synapse_client_integrationruntimemonitoringdata_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_monitoring_data


def cf_synapse_client_integrationruntimenodes_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_nodes


def cf_synapse_client_integrationruntimenodeipaddress_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_node_ip_address


def cf_synapse_client_integrationruntimecredentials_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_credentials


def cf_synapse_client_integrationruntimeconnectioninfos_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_connection_infos


def cf_synapse_client_integrationruntimestatus_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).integration_runtime_status


def cf_synapse_client_operations_factory(cli_ctx, *_):
    return cf_synapse(cli_ctx).operations


def cf_kusto_pool(cli_ctx, *_):
    return cf_synapse(cli_ctx).kusto_pools


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


def synapse_accesscontrol_factory(cli_ctx, workspace_name):
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


def cf_synapse_role_assignments(cli_ctx, workspace_name):
    return synapse_accesscontrol_factory(cli_ctx, workspace_name).role_assignments


def cf_synapse_role_definitions(cli_ctx, workspace_name):
    return synapse_accesscontrol_factory(cli_ctx, workspace_name).role_definitions


def cf_graph_client_factory(cli_ctx, **_):
    from azure.cli.command_modules.role import graph_client_factory
    graph_client = graph_client_factory(cli_ctx)
    return graph_client


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


def cf_synapse_trigger(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).trigger


def cf_synapse_trigger_run(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).trigger_run


def cf_synapse_data_flow(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).data_flow


def cf_synapse_notebook(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).notebook


def cf_synapse_spark_pool(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).big_data_pools


def cf_synapse_library(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).library


def cf_synapse_client_managedprivateendpoints_factory(cli_ctx, workspace_name):
    from azure.synapse.managedprivateendpoints import ManagedPrivateEndpointsClient
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cli_ctx)
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, _ = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.synapse_analytics_resource_id,
        subscription_id=subscription_id
    )
    return ManagedPrivateEndpointsClient(
        credential=cred,
        endpoint='{}{}{}'.format("https://", workspace_name, cli_ctx.cloud.suffixes.synapse_analytics_endpoint)
    )


def cf_synapse_managedprivateendpoints_factory(cli_ctx, workspace_name):
    return cf_synapse_client_managedprivateendpoints_factory(cli_ctx, workspace_name).managed_private_endpoints


def cf_synapse_spark_job_definition(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).spark_job_definition


def cf_kusto_script(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).kql_script


def cf_kusto_scripts(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).kql_scripts


def cf_synapse_sql_script(cli_ctx, workspace_name):
    return cf_synapse_client_artifacts_factory(cli_ctx, workspace_name).sql_script
