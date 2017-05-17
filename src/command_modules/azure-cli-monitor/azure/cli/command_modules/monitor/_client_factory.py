# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def cf_monitor(_):
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(MonitorManagementClient)


def cf_alert_rules(kwargs):
    return cf_monitor(kwargs).alert_rules


def cf_alert_rule_incidents(kwargs):
    return cf_monitor(kwargs).alert_rule_incidents


def cf_autoscale(kwargs):
    return cf_monitor(kwargs).autoscale_settings


def cf_diagnostics(kwargs):
    return cf_monitor(kwargs).service_diagnostic_settings


def cf_log_profiles(kwargs):
    return cf_monitor(kwargs).log_profiles


# DATA CLIENT FACTORIES
def cf_monitor_data(_):
    from azure.monitor import MonitorClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(MonitorClient)


def cf_metrics(kwargs):
    return cf_monitor_data(kwargs).metrics


def cf_metric_def(kwargs):
    return cf_monitor_data(kwargs).metric_definitions


def cf_activity_log(kwargs):
    return cf_monitor_data(kwargs).activity_logs
