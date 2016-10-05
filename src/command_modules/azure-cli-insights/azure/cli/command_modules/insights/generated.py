#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.command_modules.insights.sdk.insightsclient import InsightsClient
from azure.cli.command_modules.insights.sdk.insightsclient.operations import \
    (UsageMetricsOperations, EventCategoriesOperations, EventsOperations,
    TenantEventsOperations, MetricDefinitionsOperations, MetricsOperations)

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.insights.custom import \
    (list_events, list_digest_events, list_tenant_digest_events, list_tenant_events)

def _insights_client_factory(client):
    return get_mgmt_service_client(client)

cli_command('insights event list', list_events)
cli_command('insights event list-digest-events', list_digest_events)
cli_command('insights event tenant list-digest-events', list_tenant_digest_events)
cli_command('insights event tenant list', list_tenant_events)

factory = lambda _: _insights_client_factory(InsightsClient).event_categories
cli_command('insights event list-categories', EventCategoriesOperations.list, factory)


#factory = lambda x: _insights_client_factory(InsightsClient).usage_metric
#cli_command('insights list-usage', UsageMetricOperations.list, factory)

# factory = lambda x: _insights_client_factory(InsightsClient).log
# cli_command('insights logs list', LogOperations.get, factory)

# factory = lambda x: _insights_client_factory(InsightsClient).log_definition
# cli_command('insights logs list-definitions', LogDefinitionOperations.get, factory)

factory = lambda x: _insights_client_factory(InsightsClient).metric
cli_command('insights metrics list', MetricsOperations.list, factory)

factory = lambda x: _insights_client_factory(InsightsClient).metric_definition
cli_command('insights metrics list-definitions', MetricDefinitionsOperations.list, factory)

#factory = lambda x: _insights_client_factory(InsightsManagementClient).alert
#cli_command('insights alerts incident show', Alert.get_incident, factory)
#cli_command('insights alerts incident list', Alert.list_incidents_for_rule, factory)
#cli_command('insights alerts rule create', Alert.create_or_update_rule, factory)
#cli_command('insights alerts rule update', Alert.update_rule, factory)
#cli_command('insights alerts rule delete', Alert.delete_rule, factory)
#cli_command('insights alerts rule show', Alert.get_rule, factory)
#cli_command('insights alerts rule list', Alert.list_rules, factory)
