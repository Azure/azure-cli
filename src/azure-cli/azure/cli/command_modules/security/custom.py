import json
import string

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.security.models import (SecurityContact,
                                        AutoProvisioningSetting,
                                        SecurityAssessment,
                                        SecurityAssessmentMetadata,
                                        AzureResourceDetails,
                                        AssessmentStatus,
                                        IoTSecuritySolutionModel,
                                        UpdateIotSecuritySolutionData,
                                        Pricing,
                                        WorkspaceSetting,
                                        AdvancedThreatProtectionSetting,
                                        RuleResultsInput,
                                        RulesResultsInput,
                                        AlertSyncSettings,
                                        DataExportSettings,
                                        AlertsSuppressionRule,
                                        SuppressionAlertsScope,
                                        ScopeElement,
                                        Automation,
                                        AutomationScope,
                                        AutomationSource,
                                        AutomationActionWorkspace,
                                        AutomationActionLogicApp,
                                        AutomationActionEventHub,
                                        AutomationRuleSet,
                                        AutomationTriggeringRule)
from azure.mgmt.security.models._security_center_enums import Enum69
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.azclierror import (MutuallyExclusiveArgumentError)
from msrestazure.tools import resource_id
from msrestazure.azure_exceptions import CloudError
from ._utils import (
    run_cli_cmd
)

# --------------------------------------------------------------------------------------------
# Security Tasks
# --------------------------------------------------------------------------------------------


def list_security_tasks(client, resource_group_name=None):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    if resource_group_name:
        return client.tasks.list_by_resource_group(resource_group_name)

    return client.tasks.list()


def get_security_task(client, resource_name, resource_group_name=None):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    if resource_group_name:
        return client.tasks.get_resource_group_level_task(resource_group_name, resource_name)

    return client.tasks.get_subscription_level_task(resource_name)


# --------------------------------------------------------------------------------------------
# Security Alerts
# --------------------------------------------------------------------------------------------

def list_security_alerts(client, resource_group_name=None, location=None):

    if location:
        client._config.asc_location = location  # pylint: disable=protected-access

        if resource_group_name:
            return client.list_resource_group_level_by_region(resource_group_name)

        return client.list_subscription_level_by_region()

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def get_security_alert(client, location, resource_name, resource_group_name=None):

    client._config.asc_location = location  # pylint: disable=protected-access

    if resource_group_name:
        return client.get_resource_group_level(resource_name, resource_group_name)

    return client.get_subscription_level(resource_name)


def update_security_alert(client, location, resource_name, status, resource_group_name=None):

    client._config.asc_location = location  # pylint: disable=protected-access

    if resource_group_name:
        if status == "Dismiss":
            client.update_resource_group_level_state_to_dismiss(resource_name, resource_group_name)
        if status == "Activate":
            client.update_resource_group_level_state_to_activate(resource_name, resource_group_name)
        if status == "Resolve":
            client.update_resource_group_level_state_to_resolve(resource_name, resource_group_name)
    else:
        if status == "Dismiss":
            client.update_subscription_level_state_to_dismiss(resource_name)
        if status == "Activate":
            client.update_subscription_level_state_to_activate(resource_name)
        if status == "Resolve":
            client.update_subscription_level_state_to_resolve(resource_name)

# --------------------------------------------------------------------------------------------
# Security Alerts Suppression Rule
# --------------------------------------------------------------------------------------------


def list_security_alerts_suppression_rule(client):

    return client.list()


def show_security_alerts_suppression_rule(client, rule_name):

    return client.get(alerts_suppression_rule_name=rule_name)


def delete_security_alerts_suppression_rule(client, rule_name):

    return client.delete(alerts_suppression_rule_name=rule_name)


def update_security_alerts_suppression_rule(client,
                                            rule_name,
                                            alert_type,
                                            reason,
                                            state,
                                            expiration_date_utc=None,
                                            comment=None):

    from azure.core.exceptions import ResourceNotFoundError

    current_rule = None
    try:
        current_rule = client.get(alerts_suppression_rule_name=rule_name)
    except ResourceNotFoundError:
        suppression_alerts_scope = None

    if current_rule is not None:
        suppression_alerts_scope = current_rule.suppression_alerts_scope

    suppression_rule_data = AlertsSuppressionRule(name=rule_name,
                                                  alert_type=alert_type,
                                                  expiration_date_utc=expiration_date_utc,
                                                  reason=reason, state=state,
                                                  comment=comment,
                                                  suppression_alerts_scope=suppression_alerts_scope)

    return client.update(alerts_suppression_rule_name=rule_name, alerts_suppression_rule=suppression_rule_data)


def upsert_security_alerts_suppression_rule_scope(client, rule_name, field, contains_substring=None, any_of=None):
    from azure.cli.core.commands import upsert_to_collection

    # get the parent object
    parent_object = client.get(alerts_suppression_rule_name=rule_name)

    if contains_substring is not None:
        current_additional_properties = {'contains': contains_substring}
    else:
        current_additional_properties = {'in': any_of}
    scope = ScopeElement(additional_properties=current_additional_properties, field=field)

    if parent_object.suppression_alerts_scope is None:
        parent_object.suppression_alerts_scope = SuppressionAlertsScope(all_of=[scope])
    else:
        # add the new child to the parent collection
        upsert_to_collection(parent_object.suppression_alerts_scope, 'all_of', scope, 'field')

    # update the parent object
    result = client.update(alerts_suppression_rule_name=rule_name, alerts_suppression_rule=parent_object)

    # return the child object
    return next((x for x in result.suppression_alerts_scope.all_of if x.field.lower() == field.lower()), None)


def delete_security_alerts_suppression_rule_scope(client, rule_name, field):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    err_msg_field_not_found = 'The specified --field was not found in scope'

    # get the parent object
    parent_object = client.get(alerts_suppression_rule_name=rule_name)

    if parent_object.suppression_alerts_scope is None:
        raise InvalidArgumentValueError(err_msg_field_not_found)

    item_to_remove = next((x for x in
                           parent_object.suppression_alerts_scope.all_of if x.field.lower() == field.lower()), None)

    if item_to_remove is None:
        raise InvalidArgumentValueError(err_msg_field_not_found)

    parent_object.suppression_alerts_scope.all_of.remove(item_to_remove)
    if len(parent_object.suppression_alerts_scope.all_of) == 0:
        parent_object.suppression_alerts_scope = None

    return client.update(alerts_suppression_rule_name=rule_name, alerts_suppression_rule=parent_object)


# --------------------------------------------------------------------------------------------
# Security Settings
# --------------------------------------------------------------------------------------------


def list_security_settings(client):

    return client.list()


def get_security_setting(client, setting_name):

    return client.get(setting_name)


def update_security_setting(client, setting_name, enabled):

    if setting_name == Enum69.SENTINEL:
        setting = AlertSyncSettings()
    else:
        setting = DataExportSettings()

    setting.enabled = enabled
    return client.update(setting_name, setting)


# --------------------------------------------------------------------------------------------
# Security Contacts
# --------------------------------------------------------------------------------------------


def list_security_contacts(client):

    return client.list()


def get_security_contact(client, resource_name):

    return client.get(resource_name)


def create_security_contact(client, resource_name, email, phone=None, alert_notifications=None, alerts_admins=None):

    if alert_notifications is None:
        alert_notifications = ''

    if alerts_admins is None:
        alerts_admins = ''

    if phone is None:
        phone = ''

    new_contact = SecurityContact(email=email,
                                  phone=phone,
                                  alert_notifications=alert_notifications,
                                  alerts_to_admins=alerts_admins)

    return client.create(resource_name, new_contact)


def delete_security_contact(client, resource_name):

    return client.delete(resource_name)


# --------------------------------------------------------------------------------------------
# Security Automatic Provisioning Settings
# --------------------------------------------------------------------------------------------

def list_security_auto_provisioning_settings(client):

    return client.list()


def get_security_auto_provisioning_setting(client, resource_name):

    return client.get(resource_name)


def update_security_auto_provisioning_setting(client, auto_provision, resource_name):

    new_auto_provision = AutoProvisioningSetting(auto_provision=auto_provision)
    return client.create(resource_name, new_auto_provision)


def turn_off_security_auto_provisioning_setting(client, resource_name):

    new_auto_provision = AutoProvisioningSetting(auto_provision='Off')
    return client.create(resource_name, new_auto_provision)


# --------------------------------------------------------------------------------------------
# Discovered Security Solutions
# --------------------------------------------------------------------------------------------

def list_security_discovered_security_solutions(client):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.discovered_security_solutions.list()


def get_security_discovered_security_solution(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.discovered_security_solutions.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# External Security Solutions
# --------------------------------------------------------------------------------------------

def list_security_external_security_solutions(client):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.external_security_solutions.list()


def get_security_external_security_solution(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.external_security_solutions.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Just in Time network access policies
# --------------------------------------------------------------------------------------------

def list_security_jit_network_access_policies(client, resource_group_name=None, location=None):

    if location:
        client._config.asc_location = location  # pylint: disable=protected-access

        if resource_group_name:
            return client.list_by_resource_group_and_region(resource_group_name)

        return client.list_by_region()

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def get_security_jit_network_access_policy(client, location, resource_name, resource_group_name):

    client._config.asc_location = location  # pylint: disable=protected-access

    return client.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Security Locations
# --------------------------------------------------------------------------------------------

def list_security_locations(client):

    return client.list()


def get_security_location(client, resource_name):

    client._config.asc_location = resource_name  # pylint: disable=protected-access

    return client.get()


# --------------------------------------------------------------------------------------------
# Security Pricings
# --------------------------------------------------------------------------------------------

def list_security_pricings(client):

    return client.list()


def get_security_pricing(client, resource_name):

    return client.get(resource_name)


def create_security_pricing(client, resource_name, tier):

    return client.update(resource_name, Pricing(pricing_tier=tier))

# --------------------------------------------------------------------------------------------
# Security Topology
# --------------------------------------------------------------------------------------------


def list_security_topology(client):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.topology.list()


def get_security_topology(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.topology.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Security Workspace
# --------------------------------------------------------------------------------------------


def list_security_workspace_settings(client):

    return client.list()


def get_security_workspace_setting(client, resource_name):

    return client.get(resource_name)


def create_security_workspace_setting(cmd, client, resource_name, target_workspace):

    scope = '/subscriptions/' + get_subscription_id(cmd.cli_ctx)
    return client.create(resource_name, WorkspaceSetting(workspace_id=target_workspace, scope=scope))


def delete_security_workspace_setting(client, resource_name):

    client.delete(resource_name)


# --------------------------------------------------------------------------------------------
# Security ATP
# --------------------------------------------------------------------------------------------

def get_atp_setting(cmd, client, resource_group_name, storage_account_name):

    return client.get(_construct_resource_id(cmd, resource_group_name, storage_account_name))


def update_atp_setting(cmd, client, resource_group_name, storage_account_name, is_enabled):

    return client.create(_construct_resource_id(cmd, resource_group_name, storage_account_name),
                         AdvancedThreatProtectionSetting(is_enabled=is_enabled))


def _construct_resource_id(cmd, resource_group_name, storage_account_name):

    return resource_id(
        subscription=get_subscription_id(cmd.cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Storage',
        type='storageAccounts',
        name=storage_account_name)


# --------------------------------------------------------------------------------------------
# Sql Vulnerability Assessment
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
def get_va_sql_scan(client, vm_resource_id, workspace_id, server_name, database_name, scan_id, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.get(scan_id, workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def list_va_sql_scans(client, vm_resource_id, workspace_id, server_name, database_name, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.list(workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def get_va_sql_result(client, vm_resource_id, workspace_id, server_name, database_name, scan_id, rule_id, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.get(scan_id, rule_id, workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def list_va_sql_results(client, vm_resource_id, workspace_id, server_name, database_name, scan_id, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.list(scan_id, workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def get_va_sql_baseline(client, vm_resource_id, workspace_id, server_name, database_name, rule_id, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.get(rule_id, workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def list_va_sql_baseline(client, vm_resource_id, workspace_id, server_name, database_name, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.list(workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def delete_va_sql_baseline(client, vm_resource_id, workspace_id, server_name, database_name, rule_id, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    return client.delete(rule_id, workspace_id, va_sql_resource_id)


# pylint: disable=line-too-long
def update_va_sql_baseline(client, vm_resource_id, workspace_id, server_name, database_name, rule_id, baseline=None, baseline_latest=False, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    if baseline_latest is True and baseline is None:
        return client.create_or_update(rule_id, workspace_id, va_sql_resource_id, RuleResultsInput(latest_scan=True))
    if baseline_latest is False and baseline is not None:
        return client.create_or_update(rule_id, workspace_id, va_sql_resource_id, RuleResultsInput(results=baseline))
    raise MutuallyExclusiveArgumentError("Baseline can be set upon either provided baseline or latest results")


# pylint: disable=line-too-long
def set_va_sql_baseline(client, vm_resource_id, workspace_id, server_name, database_name, baseline=None, baseline_latest=False, vm_name=None, agent_id=None, vm_uuid=None):

    va_sql_resource_id = _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid)
    if baseline_latest is True and baseline is None:
        return client.add(workspace_id, va_sql_resource_id, RulesResultsInput(latest_scan=True))
    if baseline_latest is False and baseline is not None:
        return client.add(workspace_id, va_sql_resource_id, RulesResultsInput(results=baseline))
    raise MutuallyExclusiveArgumentError("Baseline can be set upon either provided baseline or latest results")


def _get_va_sql_resource_id(vm_resource_id, server_name, database_name, vm_name, agent_id, vm_uuid):

    if vm_name is None and agent_id is None and vm_uuid is None:
        return f'{vm_resource_id}/sqlServers/{server_name}/databases/{database_name}'
    if vm_name is not None and agent_id is not None and vm_uuid is not None:
        vm_identifier = f'{vm_name}_{agent_id}_{vm_uuid}'
        return f'{vm_resource_id}/onPremiseMachines/{vm_identifier}/sqlServers/{server_name}/databases/{database_name}'
    raise MutuallyExclusiveArgumentError('Please specify all of (--vm-name, --agent-id, --vm-uuid) for On-Premise resources, or none, other resource types')


# --------------------------------------------------------------------------------------------
# Security Assessments
# --------------------------------------------------------------------------------------------


def list_security_assessments(cmd, client):

    return client.list(scope='/subscriptions/' + get_subscription_id(cmd.cli_ctx))


def get_security_assessment(cmd, client, resource_name, assessed_resource_id=None):

    if assessed_resource_id is None:
        assessed_resource_id = '/subscriptions/' + get_subscription_id(cmd.cli_ctx)
    return client.get(assessed_resource_id,
                      assessment_name=resource_name)


def create_security_assessment(cmd,
                               client,
                               resource_name,
                               status_code,
                               status_cause=None,
                               status_description=None,
                               additional_data=None,
                               assessed_resource_id=None):

    if assessed_resource_id is None:
        assessed_resource_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx))

    resource_details = AzureResourceDetails(source="Azure")

    status = AssessmentStatus(code=status_code,
                              cause=status_cause,
                              description=status_description)

    new_assessment = SecurityAssessment(resource_details=resource_details,
                                        status=status,
                                        additional_data=additional_data,
                                        assessed_resource_id=assessed_resource_id)

    return client.create_or_update(resource_id=assessed_resource_id,
                                   assessment_name=resource_name,
                                   assessment=new_assessment)


def delete_security_assessment(cmd, client, resource_name, assessed_resource_id=None):

    if assessed_resource_id is None:
        assessed_resource_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx))

    return client.delete(assessment_name=resource_name,
                         resource_id=assessed_resource_id)


# --------------------------------------------------------------------------------------------
# Security Assessment Metadata
# --------------------------------------------------------------------------------------------


def list_security_assessment_metadata(client):

    return client.list_by_subscription()


def get_security_assessment_metadata(client, resource_name):

    try:
        return client.get(resource_name)
    except CloudError:
        return client.get_in_subscription(resource_name)


def create_security_assessment_metadata(client, resource_name,
                                        display_name,
                                        severity,
                                        description,
                                        remediation_description=None):

    new_assessment_metadata = SecurityAssessmentMetadata(display_name=display_name,
                                                         severity=severity,
                                                         assessment_type="CustomerManaged",
                                                         remediation_description=remediation_description,
                                                         description=description)

    return client.create_in_subscription(assessment_metadata_name=resource_name,
                                         assessment_metadata=new_assessment_metadata)


def delete_security_assessment_metadata(client, resource_name):

    return client.delete_in_subscription(resource_name)


# --------------------------------------------------------------------------------------------
# Security Sub Assessment
# --------------------------------------------------------------------------------------------


def list_security_sub_assessments(cmd, client, assessment_name=None, assessed_resource_id=None):

    if assessed_resource_id is None:
        assessed_resource_id = '/subscriptions/' + get_subscription_id(cmd.cli_ctx)
        return client.list_all(scope=assessed_resource_id)

    return client.list(scope=assessed_resource_id, assessment_name=assessment_name)


def get_security_sub_assessment(cmd, client, resource_name, assessment_name, assessed_resource_id=None):

    if assessed_resource_id is None:
        assessed_resource_id = '/subscriptions/' + get_subscription_id(cmd.cli_ctx)

    return client.get(sub_assessment_name=resource_name,
                      assessment_name=assessment_name,
                      scope=assessed_resource_id)


# --------------------------------------------------------------------------------------------
# Adaptive Application Controls
# --------------------------------------------------------------------------------------------


def list_security_adaptive_application_controls(client):

    return client.list()


def get_security_adaptive_application_controls(client, group_name):

    return client.get(group_name=group_name)


# --------------------------------------------------------------------------------------------
# Adaptive Network Hardenings
# --------------------------------------------------------------------------------------------


def get_security_adaptive_network_hardenings(client,
                                             adaptive_network_hardenings_resource_name,
                                             resource_name,
                                             resource_type,
                                             resource_namespace,
                                             resource_group_name):

    return client.get(resource_group_name,
                      resource_namespace,
                      resource_type,
                      resource_name,
                      adaptive_network_hardenings_resource_name)


def list_security_adaptive_network_hardenings(client,
                                              resource_name,
                                              resource_type,
                                              resource_namespace,
                                              resource_group_name):

    return client.list_by_extended_resource(resource_group_name,
                                            resource_namespace,
                                            resource_type,
                                            resource_name)


# --------------------------------------------------------------------------------------------
# Allowed Connections
# --------------------------------------------------------------------------------------------


def list_security_allowed_connections(client):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.allowed_connections.list()


def get_security_allowed_connections(client, resource_name, resource_group_name):

    for loc in client.locations.list():
        client._config.asc_location = loc.name  # pylint: disable=protected-access

    return client.allowed_connections.get(resource_group_name, resource_name)


# --------------------------------------------------------------------------------------------
# Security IoT Solution
# --------------------------------------------------------------------------------------------


def list_security_iot_solution(client, resource_group_name=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    return client.list_by_subscription()


def show_security_iot_solution(client, resource_group_name, iot_solution_name):

    return client.get(resource_group_name=resource_group_name, solution_name=iot_solution_name)


def delete_security_iot_solution(client, resource_group_name, iot_solution_name):

    return client.delete(resource_group_name=resource_group_name, solution_name=iot_solution_name)


def create_security_iot_solution(client, resource_group_name, iot_solution_name,
                                 iot_solution_display_name, iot_solution_iot_hubs, location):

    iot_security_solution_data = IoTSecuritySolutionModel(display_name=iot_solution_display_name,
                                                          iot_hubs=iot_solution_iot_hubs.split(","),
                                                          location=location)

    return client.create_or_update(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name,
        iot_security_solution_data=iot_security_solution_data)


def update_security_iot_solution(client, resource_group_name, iot_solution_name,
                                 iot_solution_display_name=None, iot_solution_iot_hubs=None):

    return client.update(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name,
        update_iot_security_solution_data=UpdateIotSecuritySolutionData(
            displayName=iot_solution_display_name,
            iotHubs=iot_solution_iot_hubs))


# --------------------------------------------------------------------------------------------
# Security IoT Analytics
# --------------------------------------------------------------------------------------------


def list_security_iot_analytics(client, resource_group_name, iot_solution_name):

    return client.list(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name)


def show_security_iot_analytics(client, resource_group_name, iot_solution_name):

    return client.get(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name)


# --------------------------------------------------------------------------------------------
# Security IoT Alerts
# --------------------------------------------------------------------------------------------


def list_security_iot_alerts(client, resource_group_name, iot_solution_name):

    return client.list(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name)


def show_security_iot_alerts(client, resource_group_name, iot_solution_name, resource_name):

    return client.get(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name,
        aggregated_alert_name=resource_name)


def dismiss_security_iot_alerts(client, resource_group_name, iot_solution_name, resource_name):

    return client.dismiss(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name,
        aggregated_alert_name=resource_name)


# --------------------------------------------------------------------------------------------
# Security IoT Recommendations
# --------------------------------------------------------------------------------------------


def list_security_iot_recommendations(client, resource_group_name, iot_solution_name):

    return client.list(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name)


def show_security_iot_recommendations(client, resource_group_name, iot_solution_name, resource_name):

    return client.get(
        resource_group_name=resource_group_name,
        solution_name=iot_solution_name,
        aggregated_recommendation_name=resource_name)


# --------------------------------------------------------------------------------------------
# Security Regulatory Compliance
# --------------------------------------------------------------------------------------------


def list_regulatory_compliance_standards(client):

    return client.list()


def get_regulatory_compliance_standard(client, resource_name):

    return client.get(regulatory_compliance_standard_name=resource_name)


def list_regulatory_compliance_controls(client, standard_name):

    return client.list(regulatory_compliance_standard_name=standard_name)


def get_regulatory_compliance_control(client, resource_name, standard_name):

    return client.get(regulatory_compliance_standard_name=standard_name,
                      regulatory_compliance_control_name=resource_name)


def list_regulatory_compliance_assessments(client, standard_name, control_name):

    return client.list(regulatory_compliance_standard_name=standard_name,
                       regulatory_compliance_control_name=control_name)


def get_regulatory_compliance_assessment(client, resource_name, standard_name, control_name):

    return client.get(regulatory_compliance_standard_name=standard_name,
                      regulatory_compliance_control_name=control_name,
                      regulatory_compliance_assessment_name=resource_name)

# --------------------------------------------------------------------------------------------
# Security Secure Score
# --------------------------------------------------------------------------------------------


def list_secure_scores(client):

    return client.list()


def get_secure_score(client, resource_name):

    return client.get(resource_name)


def list_secure_score_controls(client):

    return client.list()


def list_by_score(client, resource_name):

    return client.list_by_secure_score(resource_name)


def list_secure_score_control_definitions(client):

    return client.list_by_subscription()

# --------------------------------------------------------------------------------------------
# Security Automations
# --------------------------------------------------------------------------------------------


def list_security_automations(client, resource_group_name=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def get_security_automation(client, resource_group_name, resource_name):

    return client.get(resource_group_name, resource_name)


def delete_security_automation(client, resource_group_name, resource_name):

    return client.delete(resource_group_name, resource_name)


def create_or_update_security_automation(client, resource_group_name, resource_name, scopes, sources, actions, location=None, etag=None, tags=None, description=None, isEnabled=None):

    if location is None:
        resourceGroup = run_cli_cmd('az group show --name {}'.format(resource_group_name))
        location = resourceGroup['location']
    automation = create_security_automation_object(location, scopes, sources, actions, etag, tags, description, isEnabled)
    return client.create_or_update(resource_group_name, resource_name, automation)


def validate_security_automation(client, resource_group_name, resource_name, scopes, sources, actions, location=None, etag=None, tags=None, description=None, isEnabled=None):

    if location is None:
        resourceGroup = run_cli_cmd('az group show --name {}'.format(resource_group_name))
        location = resourceGroup['location']
    automation = create_security_automation_object(location, scopes, sources, actions, etag, tags, description, isEnabled)
    return client.validate(resource_group_name, resource_name, automation)


def create_security_automation_scope(description, scope_path):

    return AutomationScope(description=description, scope_path=scope_path)


def create_security_automation_rule(expected_value, operator, property_j_path, property_type):

    return AutomationTriggeringRule(property_j_path=property_j_path, property_type=property_type, expected_value=expected_value, operator=operator)


def create_security_automation_rule_set(rules=None):

    return AutomationRuleSet(rules=rules)


def create_security_automation_source(event_source, rule_sets=None):

    return AutomationSource(event_source=event_source, rule_sets=rule_sets)


def create_security_automation_action_logic_app(logic_app_resource_id, uri):

    return AutomationActionLogicApp(logic_app_resource_id=logic_app_resource_id, uri=uri)


def create_security_automation_action_event_hub(event_hub_resource_id, connection_string, sas_policy_name=None):

    automationActionEventHub = AutomationActionEventHub(event_hub_resource_id=event_hub_resource_id, connection_string=connection_string)
    automationActionEventHub.sas_policy_name = sas_policy_name
    return automationActionEventHub


def create_security_automation_action_workspace(workspace_resource_id):

    return AutomationActionWorkspace(workspace_resource_id=workspace_resource_id)


# Security Automations Utils


def create_security_automation_object(location, scopes, sources, actions, etag=None, tags=None, description=None, isEnabled=None):

    scopes = sanitize_json_as_string(scopes)
    sources = sanitize_json_as_string(sources)
    actions = sanitize_json_as_string(actions)

    scopes = json.loads(scopes)
    scopesAsObjectList = []
    for scope in scopes:
        scopeAsObject = AutomationScope(description=scope['description'], scope_path=scope['scopePath'])
        scopesAsObjectList.append(scopeAsObject)

    sources = json.loads(sources)
    sourcesAsObjectList = []
    for source in sources:
        sourceAsObject = AutomationSource(event_source=source['eventSource'], rule_sets=get_security_automation_ruleSets_object(source['ruleSets']))
        sourcesAsObjectList.append(sourceAsObject)

    actions = json.loads(actions)
    actionsAsObjectList = []
    for action in actions:
        if action['actionType'] == 'LogicApp':
            actionAsObject = AutomationActionLogicApp(logic_app_resource_id=action['logicAppResourceId'], uri=action['ruleSets'])
        elif action['actionType'] == 'EventHub':
            actionAsObject = AutomationActionEventHub(event_hub_resource_id=action['eventHubResourceId'], connection_string=action['connectionString'])
        elif action['actionType'] == 'Workspace':
            actionAsObject = AutomationActionWorkspace(workspace_resource_id=action['workspaceResourceId'])

        actionsAsObjectList.append(actionAsObject)

    if tags is not None:
        tags = json.loads(tags)

    return Automation(location=location,
                      scopes=scopesAsObjectList,
                      sources=sourcesAsObjectList,
                      actions=actionsAsObjectList,
                      tags=tags,
                      etag=etag,
                      description=description,
                      isEnabled=isEnabled)


def get_security_automation_ruleSets_object(ruleSets):
    if ruleSets is None:
        return
    ruleSetsAsObjectList = []
    for ruleSet in ruleSets:
        ruleSetAsObject = AutomationRuleSet(rules=get_security_automation_rules_object(ruleSet['rules']))
        ruleSetsAsObjectList.append(ruleSetAsObject)
    return ruleSetsAsObjectList


def get_security_automation_rules_object(rules):
    if rules is None:
        return
    ruleAsObjectList = []
    for rule in rules:
        ruleAsObject = AutomationTriggeringRule(property_j_path=rule['propertyJPath'], property_type=rule['propertyType'], expected_value=rule['expectedValue'], operator=rule['operator'])
        ruleAsObjectList.append(ruleAsObject)
    return ruleAsObjectList


def sanitize_json_as_string(value: string):
    valueLength = len(value)
    if((value[0] == '\'' and value[valueLength - 1] == '\'') or (value[0] == '\"' and value[valueLength - 1] == '\"')):
        value = value[1:]
        value = value[:-1]
    return value
