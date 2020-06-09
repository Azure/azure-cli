# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def cf_monitor(cli_ctx, **kwargs):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_MONITOR, **kwargs)


def cf_alert_rules(cli_ctx, _):
    return cf_monitor(cli_ctx).alert_rules


def cf_alert_rule_incidents(cli_ctx, _):
    return cf_monitor(cli_ctx).alert_rule_incidents


def cf_autoscale(cli_ctx, _):
    return cf_monitor(cli_ctx).autoscale_settings


def cf_diagnostics(cli_ctx, _):
    return cf_monitor(cli_ctx).diagnostic_settings


def cf_diagnostics_category(cli_ctx, _):
    return cf_monitor(cli_ctx).diagnostic_settings_category


def cf_log_profiles(cli_ctx, _):
    return cf_monitor(cli_ctx).log_profiles


def cf_action_groups(cli_ctx, _):
    return cf_monitor(cli_ctx).action_groups


def cf_activity_log_alerts(cli_ctx, _):
    return cf_monitor(cli_ctx).activity_log_alerts


def cf_metrics(cli_ctx, _):
    return cf_monitor(cli_ctx).metrics


def cf_metric_def(cli_ctx, _):
    return cf_monitor(cli_ctx).metric_definitions


def cf_activity_log(cli_ctx, _):
    return cf_monitor(cli_ctx).activity_logs


def cf_event_categories(cli_ctx, _):
    return cf_monitor(cli_ctx).event_categories


def cf_metric_alerts(cli_ctx, _):
    return cf_monitor(cli_ctx).metric_alerts


def _log_analytics_client_factory(cli_ctx, **kwargs):
    from azure.mgmt.loganalytics import LogAnalyticsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, LogAnalyticsManagementClient, **kwargs)


def cf_private_link_resources(cli_ctx, _):
    return cf_monitor(cli_ctx).private_link_resources


def cf_private_link_scoped_resources(cli_ctx, _):
    return cf_monitor(cli_ctx).private_link_scoped_resources


def cf_private_link_scope_operation_status(cli_ctx, _):
    return cf_monitor(cli_ctx).private_link_scope_operation_status


def cf_private_link_scopes(cli_ctx, _):
    return cf_monitor(cli_ctx).private_link_scopes


def cf_private_endpoint_connections(cli_ctx, _):
    return cf_monitor(cli_ctx).private_endpoint_connections


def cf_log_analytics_workspace(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).workspaces


def cf_log_analytics_deleted_workspaces(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).deleted_workspaces


def cf_log_analytics_workspace_tables(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).tables


def cf_log_analytics_workspace_management_groups(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).management_groups


def cf_log_analytics_workspace_usage(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).usages


def cf_log_analytics_workspace_schema(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).schema


def cf_log_analytics_workspace_shared_keys(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).shared_keys


def cf_log_analytics_workspace_intelligence_packs(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).intelligence_packs


def cf_log_analytics_workspace_linked_service(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).linked_services


def cf_log_analytics_cluster(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).clusters


def cf_log_analytics_linked_storage(cli_ctx, _):
    return _log_analytics_client_factory(cli_ctx).linked_storage_accounts
