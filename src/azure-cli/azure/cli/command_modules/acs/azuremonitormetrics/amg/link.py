# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import uuid
from knack.util import CLIError
from azure.cli.command_modules.acs.azuremonitormetrics.constants import (
    GRAFANA_API,
    GRAFANA_ROLE_ASSIGNMENT_API,
    GrafanaLink
)
from azure.cli.command_modules.acs.azuremonitormetrics.helper import sanitize_resource_id


def link_grafana_instance(cmd, raw_parameters, azure_monitor_workspace_resource_id):
    from azure.cli.core.util import send_raw_request
    # GET grafana principal ID
    try:
        grafana_resource_id = raw_parameters.get("grafana_resource_id")
        if grafana_resource_id is None or grafana_resource_id == "":
            return GrafanaLink.NOPARAMPROVIDED
        grafana_resource_id = sanitize_resource_id(grafana_resource_id)
        grafanaURI = "{0}{1}?api-version={2}".format(
            cmd.cli_ctx.cloud.endpoints.resource_manager,
            grafana_resource_id,
            GRAFANA_API
        )
        headers = ['User-Agent=azuremonitormetrics.link_grafana_instance']
        grafanaArmResponse = send_raw_request(cmd.cli_ctx, "GET", grafanaURI, body={}, headers=headers)

        # Check if 'identity' and 'type' exist in the response
        identity_info = grafanaArmResponse.json().get("identity", {})
        identity_type = identity_info.get("type", "").lower()

        if identity_type == "systemassigned":
            servicePrincipalId = identity_info.get("principalId")
        elif identity_type == "userassigned":
            user_assigned_identities = identity_info.get("userAssignedIdentities", {})
            if not user_assigned_identities:
                raise CLIError("No user-assigned identities found.")
            servicePrincipalId = list(user_assigned_identities.values())[0]["principalId"]
        else:
            raise CLIError("Unsupported or missing identity type.")

        if not servicePrincipalId:
            raise CLIError("No service principal ID found for the specified identity.")
    except CLIError as e:
        raise CLIError(e)
    # Add Role Assignment
    try:
        MonitoringDataReader = "b0d8363b-8ddd-447d-831f-62ca05bff136"
        roleDefinitionURI = "{0}{1}/providers/Microsoft.Authorization/roleAssignments/{2}?api-version={3}".format(
            cmd.cli_ctx.cloud.endpoints.resource_manager,
            azure_monitor_workspace_resource_id,
            uuid.uuid4(),
            GRAFANA_ROLE_ASSIGNMENT_API
        )
        roleDefinitionId = "{0}/providers/Microsoft.Authorization/roleDefinitions/{1}".format(
            azure_monitor_workspace_resource_id,
            MonitoringDataReader
        )
        association_body = json.dumps({
            "properties": {
                "roleDefinitionId": roleDefinitionId,
                "principalId": servicePrincipalId
            }
        })
        headers = ['User-Agent=azuremonitormetrics.add_role_assignment']
        send_raw_request(cmd.cli_ctx, "PUT", roleDefinitionURI, body=association_body, headers=headers)
    except CLIError as e:
        if e.response.status_code != 409:
            erroString = "Role Assingment failed. Please manually assign the `Monitoring Data Reader` role\
                to the Azure Monitor Workspace ({0}) for the Azure Managed Grafana\
                System Assigned Managed Identity ({1})".format(
                azure_monitor_workspace_resource_id,
                servicePrincipalId
            )
            print(erroString)
    # Setting up AMW Integration
    targetGrafanaArmPayload = grafanaArmResponse.json()
    if targetGrafanaArmPayload["properties"] is None:
        raise CLIError("Invalid grafana payload to add AMW integration")
    if "grafanaIntegrations" not in json.dumps(targetGrafanaArmPayload):
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"] = {}
    if "azureMonitorWorkspaceIntegrations" not in json.dumps(targetGrafanaArmPayload):
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"] = []
    amwIntegrations = targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"]
    if amwIntegrations != [] and azure_monitor_workspace_resource_id in json.dumps(amwIntegrations).lower():
        return GrafanaLink.ALREADYPRESENT
    try:
        grafanaURI = "{0}{1}?api-version={2}".format(
            cmd.cli_ctx.cloud.endpoints.resource_manager,
            grafana_resource_id,
            GRAFANA_API
        )
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"].append({
            "azureMonitorWorkspaceResourceId": azure_monitor_workspace_resource_id
        })
        targetGrafanaArmPayload = json.dumps(targetGrafanaArmPayload)
        headers = ['User-Agent=azuremonitormetrics.setup_amw_grafana_integration', 'Content-Type=application/json']
        send_raw_request(cmd.cli_ctx, "PUT", grafanaURI, body=targetGrafanaArmPayload, headers=headers)
    except CLIError as e:
        raise CLIError(e)
    return GrafanaLink.SUCCESS
