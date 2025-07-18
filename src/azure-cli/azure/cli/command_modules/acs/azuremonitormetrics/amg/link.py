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


# pylint: disable=line-too-long
def link_grafana_instance(cmd, raw_parameters, azure_monitor_workspace_resource_id):
    from azure.cli.command_modules.acs._client_factory import get_resources_client
    resources = get_resources_client(cmd.cli_ctx, raw_parameters.get("subscription_id"))
    # GET grafana principal ID
    try:
        grafana_resource_id = raw_parameters.get("grafana_resource_id")
        if grafana_resource_id is None or grafana_resource_id == "":
            return GrafanaLink.NOPARAMPROVIDED
        grafana_resource_id = sanitize_resource_id(grafana_resource_id)
        grafanaArmResponse = resources.get_by_id(grafana_resource_id, GRAFANA_API)

        # Check if 'identity' and 'type' exist in the response
        identity_info = getattr(grafanaArmResponse, "identity", {})
        identity_type = getattr(identity_info, "type", "").lower() if identity_info else ""

        if identity_type == "systemassigned":
            servicePrincipalId = getattr(identity_info, "principal_id", None)
        elif identity_type == "userassigned":
            user_assigned_identities = getattr(identity_info, "user_assigned_identities", {})
            if not user_assigned_identities:
                raise CLIError("No user-assigned identities found.")
            user_assigned_values = list(user_assigned_identities.values())
            if not user_assigned_values or "principal_id" not in user_assigned_values[0]:
                raise CLIError("Invalid user-assigned identity structure or missing principal_id.")
            servicePrincipalId = user_assigned_values[0]["principal_id"]
        else:
            raise CLIError("Unsupported or missing identity type.")

        if not servicePrincipalId:
            raise CLIError("No service principal ID found for the specified identity.")
    except Exception as e:
        raise CLIError(e)
    # Add Role Assignment
    try:
        MonitoringDataReader = "b0d8363b-8ddd-447d-831f-62ca05bff136"
        roleAssignmentId = str(uuid.uuid4())
        roleDefinitionId = (
            f"{azure_monitor_workspace_resource_id}/providers/Microsoft.Authorization/roleDefinitions/"
            f"{MonitoringDataReader}"
        )
        roleAssignmentResourceId = (
            f"{azure_monitor_workspace_resource_id}/providers/Microsoft.Authorization/roleAssignments/"
            f"{roleAssignmentId}"
        )
        association_body = {
            "properties": {
                "roleDefinitionId": roleDefinitionId,
                "principalId": servicePrincipalId
            }
        }
        try:
            resources.begin_create_or_update_by_id(
                roleAssignmentResourceId,
                GRAFANA_ROLE_ASSIGNMENT_API,
                association_body
            )
        except CLIError as e:
            # If already exists (409), ignore, else print error
            if not (hasattr(e, "status_code") and e.status_code == 409):
                erroString = (
                    f"Role Assignment failed. Please manually assign the `Monitoring Data Reader` role\n"
                    f"to the Azure Monitor Workspace ({azure_monitor_workspace_resource_id}) "
                    f"for the Azure Managed Grafana\nSystem Assigned Managed Identity ({servicePrincipalId})"
                )
                print(erroString)
    except Exception as e:
        raise CLIError(e)
    # Setting up AMW Integration
    targetGrafanaArmPayload = (
        grafanaArmResponse.as_dict()
        if hasattr(grafanaArmResponse, "as_dict")
        else grafanaArmResponse
    )
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
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"].append({
            "azureMonitorWorkspaceResourceId": azure_monitor_workspace_resource_id
        })
        resources.begin_create_or_update_by_id(
            grafana_resource_id,
            GRAFANA_API,
            targetGrafanaArmPayload
        )
    except CLIError as e:
        raise CLIError(e)
    return GrafanaLink.SUCCESS
