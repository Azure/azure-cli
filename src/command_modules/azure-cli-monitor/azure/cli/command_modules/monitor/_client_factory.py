# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def cf_monitor(cli_ctx, _):
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, MonitorManagementClient)


def cf_alert_rules(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).alert_rules


def cf_alert_rule_incidents(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).alert_rule_incidents


def cf_autoscale(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).autoscale_settings


def cf_diagnostics(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).diagnostic_settings


def cf_log_profiles(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).log_profiles


def cf_action_groups(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).action_groups


def cf_activity_log_alerts(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).activity_log_alerts


def cf_metrics(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).metrics


def cf_metric_def(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).metric_definitions


def cf_activity_log(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).activity_logs


def cf_event_categories(cli_ctx, kwargs):
    return cf_monitor(cli_ctx, kwargs).event_categories
