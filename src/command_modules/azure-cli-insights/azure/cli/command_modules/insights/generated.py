#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.command_modules.insights.sdk.insightsclient import InsightsClient
from azure.cli.command_modules.insights.sdk.insightsclient.operations import \
    (UsageMetricsOperations, EventCategoriesOperations, EventsOperations,
     TenantEventsOperations, MetricDefinitionsOperations, MetricsOperations)
from azure.cli.command_modules.insights.sdk.insightsmanagementclient import \
     InsightsManagementClient
from azure.cli.command_modules.insights.sdk.insightsmanagementclient.operations import \
    (AutoscaleSettingsOperations, ServiceDiagnosticSettingsOperations,
     AlertRulesOperations, AlertRuleIncidentsOperations, IncidentsOperations,
     LogProfilesOperations)

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.insights.custom import \
    (list_events, list_digest_events, list_tenant_digest_events,
     list_tenant_events, _generate_alerts_rule_template)

def _insights_client_factory(client):
    return get_mgmt_service_client(client)

cli_command('insights events list', list_events)
# list-digest and tenat list-digest are not aviailable
#cli_command('insights events list-digest-events', list_digest_events)
#cli_command('insights events tenant list-digest-events', list_tenant_digest_events)
cli_command('insights events tenant list', list_tenant_events)

factory = lambda _: _insights_client_factory(InsightsClient).event_categories
cli_command('insights events list-categories', EventCategoriesOperations.list, factory)


# factory = lambda x: _insights_client_factory(InsightsClient).usage_metric
# cli_command('insights list-usage', UsageMetricOperations.list, factory)

factory = lambda x: _insights_client_factory(InsightsClient).metrics
cli_command('insights metrics list', MetricsOperations.list, factory)

factory = lambda x: _insights_client_factory(InsightsClient).metric_definitions
cli_command('insights metrics list-definitions', MetricDefinitionsOperations.list, factory)

factory = lambda x: _insights_client_factory(InsightsManagementClient).alert_rules
cli_command('insights alerts rule create', AlertRulesOperations.create_or_update, factory)
cli_command('insights alerts rule update', AlertRulesOperations.create_or_update, factory)
cli_command('insights alerts rule delete', AlertRulesOperations.delete, factory)
cli_command('insights alerts rule show', AlertRulesOperations.get, factory)
cli_command('insights alerts rule list', AlertRulesOperations.list_by_resource_group, factory)
# A helper command to generate alerts rule resource template
cli_command('insights alerts rule TEMPLATE', _generate_alerts_rule_template)

factory = lambda x: _insights_client_factory(InsightsManagementClient).alert_rule_incidents
cli_command('insights alerts incident show', AlertRuleIncidentsOperations.get, factory)

factory = lambda x: _insights_client_factory(InsightsManagementClient).incidents
cli_command('insights alerts incident list', IncidentsOperations.list_by_alert_rule, factory)

# factory = lambda x: _insights_client_factory(InsightsClient).log
# cli_command('insights logs list', LogOperations.get, factory)

# factory = lambda x: _insights_client_factory(InsightsClient).log_definition
# cli_command('insights logs list-definitions', LogDefinitionOperations.get, factory)