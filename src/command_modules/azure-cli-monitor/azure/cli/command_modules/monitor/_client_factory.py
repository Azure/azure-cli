# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def get_monitor_management_client(_):
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(MonitorManagementClient)


def get_monitor_autoscale_settings_operation(kwargs):
    return get_monitor_management_client(kwargs).autoscale_settings


def get_monitor_diagnostic_settings_operation(kwargs):
    return get_monitor_management_client(kwargs).service_diagnostic_settings


def get_monitor_alert_rules_operation(kwargs):
    return get_monitor_management_client(kwargs).alert_rules


def get_monitor_alert_rule_incidents_operation(kwargs):
    return get_monitor_management_client(kwargs).alert_rule_incidents


def get_monitor_log_profiles_operation(kwargs):
    return get_monitor_management_client(kwargs).log_profiles


# DATA CLIENT FACTORIES
def get_monitor_client(_):
    from azure.monitor import MonitorClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(MonitorClient)


def get_monitor_activity_log_operation(kwargs):
    return get_monitor_client(kwargs).activity_logs


def get_monitor_metric_definitions_operation(kwargs):
    return get_monitor_client(kwargs).metric_definitions


def get_monitor_metrics_operation(kwargs):
    return get_monitor_client(kwargs).metrics
