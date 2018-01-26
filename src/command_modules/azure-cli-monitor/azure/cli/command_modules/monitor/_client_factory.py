# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def cf_monitor(cli_ctx, _):
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, MonitorManagementClient)


def cf_alert_rules(cli_ctx, _):
    return cf_monitor(cli_ctx, _).alert_rules


def cf_alert_rule_incidents(cli_ctx, _):
    return cf_monitor(cli_ctx, _).alert_rule_incidents


def cf_autoscale(cli_ctx, _):
    return cf_monitor(cli_ctx, _).autoscale_settings


def cf_diagnostics(cli_ctx, _):
    return cf_monitor(cli_ctx, _).diagnostic_settings


def cf_log_profiles(cli_ctx, _):
    return cf_monitor(cli_ctx, _).log_profiles


def cf_action_groups(cli_ctx, _):
    return cf_monitor(cli_ctx, _).action_groups


def cf_activity_log_alerts(cli_ctx, _):
    return cf_monitor(cli_ctx, _).activity_log_alerts


def cf_metrics(cli_ctx, _):
    return cf_monitor(cli_ctx, _).metrics


def cf_metric_def(cli_ctx, _):
    return cf_monitor(cli_ctx, _).metric_definitions


def cf_activity_log(cli_ctx, _):
    return cf_monitor(cli_ctx, _).activity_logs


def cf_event_categories(cli_ctx, _):
    return cf_monitor(cli_ctx, _).event_categories
